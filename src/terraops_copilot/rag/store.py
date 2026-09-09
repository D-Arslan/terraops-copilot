"""Embeddings + vector store (Chroma, local, persisted) + hybrid retriever.

The embedder is injectable so the store is testable without downloading a model.
Default model: paraphrase-multilingual-MiniLM-L12-v2 - the corpus mixes French
(learning.md) and English (README), and questions arrive in French. A monolingual
English model would put 'dérive' and 'drift' far apart.

Known limit, measured: MiniLM embeds only the first 128 tokens of a chunk. Any
longer text is truncated SILENTLY (one transformers warning, easy to miss). The
chunker's default size (450 chars, ~110 tokens) exists because of that number.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from pathlib import Path

from .chunking import Chunk
from .lexical import LexicalIndex

Embedder = Callable[[list[str]], list[list[float]]]

DEFAULT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION = "terraops_docs"
RRF_K = 60   # reciprocal-rank-fusion constant (standard value from the RRF paper)


def sentence_transformer_embedder(model_name: str | None = None) -> Embedder:
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(model_name or os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL))

    def embed(texts: list[str]) -> list[list[float]]:
        # normalize -> cosine distance in Chroma == 1 - dot product, comparable across queries
        return model.encode(texts, normalize_embeddings=True, batch_size=32).tolist()
    return embed


@dataclass
class Hit:
    id: str
    text: str
    citation: str
    source: str
    dense_score: float = 0.0     # cosine similarity (0 = unrelated, 1 = identical)
    lexical_score: float = 0.0   # BM25 (0 = no query term in the chunk)
    fused: float = 0.0           # RRF score used for ranking
    channels: list[str] = field(default_factory=list)  # which retrievers found it

    @property
    def score(self) -> float:    # kept for the dense-only path / tests
        return self.dense_score


class VectorStore:
    def __init__(self, path: str | Path, embedder: Embedder):
        import chromadb
        self._client = chromadb.PersistentClient(path=str(path))
        self._embed = embedder
        self._col = self._client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"})

    def count(self) -> int:
        return self._col.count()

    def rebuild(self, chunks: list[Chunk]) -> int:
        self._client.delete_collection(COLLECTION)
        self._col = self._client.get_or_create_collection(
            COLLECTION, metadata={"hnsw:space": "cosine"})
        for start in range(0, len(chunks), 64):
            batch = chunks[start:start + 64]
            self._col.add(
                ids=[c.id for c in batch],
                documents=[c.text for c in batch],
                embeddings=self._embed([c.text for c in batch]),
                metadatas=[{"source": c.source, "citation": c.citation,
                            "heading": " › ".join(c.heading_path)} for c in batch],
            )
        return self.count()

    def all(self) -> list[Hit]:
        """Every stored chunk (used to build the lexical index at startup)."""
        if self.count() == 0:
            return []
        res = self._col.get(include=["documents", "metadatas"])
        return [Hit(id=i, text=d, citation=m["citation"], source=m["source"])
                for i, d, m in zip(res["ids"], res["documents"], res["metadatas"])]

    def search(self, query: str, k: int = 4) -> list[Hit]:
        """Dense-only search."""
        if self.count() == 0:
            return []
        res = self._col.query(query_embeddings=self._embed([query]),
                              n_results=min(k, self.count()),
                              include=["documents", "metadatas", "distances"])
        return [Hit(id=i, text=d, citation=m["citation"], source=m["source"],
                    dense_score=1.0 - float(dist), channels=["dense"])
                for i, d, m, dist in zip(res["ids"][0], res["documents"][0],
                                         res["metadatas"][0], res["distances"][0])]


class HybridRetriever:
    """Dense (Chroma) + lexical (BM25) fused with reciprocal rank fusion.

    RRF: score(chunk) = sum over channels of 1 / (RRF_K + rank). Rank-based, so the
    two channels' incomparable scales (cosine vs BM25) never need calibrating.
    """

    def __init__(self, store: VectorStore, candidates: int = 20):
        self.store = store
        self.candidates = candidates
        chunks = store.all()
        self._by_id = {h.id: h for h in chunks}
        self._lexical = LexicalIndex([h.id for h in chunks], [h.text for h in chunks])

    def count(self) -> int:
        return len(self._by_id)

    def search(self, query: str, k: int = 4) -> list[Hit]:
        n = min(self.candidates, max(self.count(), 1))
        acc: dict[str, dict] = {}

        def slot(cid: str) -> dict:
            return acc.setdefault(cid, {"dense": 0.0, "lex": 0.0, "fused": 0.0, "ch": []})

        for rank, h in enumerate(self.store.search(query, k=n)):
            a = slot(h.id)
            a["dense"], a["fused"] = h.dense_score, a["fused"] + 1.0 / (RRF_K + rank)
            a["ch"].append("dense")
        for rank, (cid, s) in enumerate(self._lexical.search(query, k=n)):
            a = slot(cid)
            a["lex"], a["fused"] = s, a["fused"] + 1.0 / (RRF_K + rank)
            a["ch"].append("lexical")
        top = sorted(acc.items(), key=lambda kv: -kv[1]["fused"])[:k]
        return [replace(self._by_id[cid], dense_score=a["dense"], lexical_score=a["lex"],
                        fused=a["fused"], channels=list(a["ch"])) for cid, a in top]
