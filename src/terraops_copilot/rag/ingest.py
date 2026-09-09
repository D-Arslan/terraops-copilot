"""Build the vector store from ./corpus.  `python -m terraops_copilot.rag.ingest`

Idempotent and offline (after the first model download). Run it again after
refreshing the corpus; the collection is rebuilt from scratch, never appended to,
so a removed file cannot linger as stale chunks.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from .chunking import Chunk, chunk_document
from .store import VectorStore, sentence_transformer_embedder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS = PROJECT_ROOT / "corpus"
DEFAULT_STORE = PROJECT_ROOT / ".rag_store"
EXTENSIONS = (".md", ".yaml", ".yml")


def load_chunks(corpus_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(corpus_dir.rglob("*")):
        if path.suffix.lower() not in EXTENSIONS or path.name == "MANIFEST.md":
            continue
        text = path.read_text(encoding="utf-8")
        chunks.extend(chunk_document(text, source=path.name))
    return chunks


def store_path() -> Path:
    return Path(os.getenv("RAG_STORE_PATH", DEFAULT_STORE))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    ap.add_argument("--store", type=Path, default=store_path())
    ap.add_argument("--rebuild", action="store_true", help="(default behaviour; kept for clarity)")
    args = ap.parse_args(argv)

    chunks = load_chunks(args.corpus)
    by_source: dict[str, int] = {}
    for c in chunks:
        by_source[c.source] = by_source.get(c.source, 0) + 1
    print(f"{len(chunks)} chunks from {len(by_source)} files: {by_source}")

    store = VectorStore(args.store, sentence_transformer_embedder())
    n = store.rebuild(chunks)
    print(f"stored {n} chunks in {args.store}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
