"""BM25 keyword index - the lexical half of hybrid retrieval.

Measured on this corpus (LEARNINGS.md, Sprint 2): dense-only MiniLM got hit@1 = 1/5
on five reference questions; BM25 alone 2/5; the two fused 3/5. Embeddings catch
paraphrase ('promotion d'un modèle' ~ 'gate champion/challenger'); BM25 catches
exact identifiers ('min_delta', 'Wasserstein', 'X-TerraOps-Source') that a small
embedding model blurs. Neither is sufficient alone on a bilingual technical corpus.

Stopwords matter: without them 'c'est quoi la dérive ?' scores every chunk on
'la' and 'est', and a query about pizza still 'matches' the whole corpus.
"""
from __future__ import annotations

import re
import unicodedata

from rank_bm25 import BM25Okapi

STOPWORDS = set("""
a an and are as at be by for from has have in is it its of on or that the this to was
with what which who how why when where does do did not no
le la les un une des du de d l et ou en au aux ce cet cette ces qui que quoi dont est
sont etre a on ne pas plus pour par sur sous dans avec sans comment pourquoi quel quelle
quels quelles il elle ils elles nous vous je tu se sa son ses leur leurs y
""".split())


def tokenize(text: str) -> list[str]:
    """lowercase, strip accents (dérive -> derive), keep identifiers with '_'."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return [t for t in re.findall(r"[a-z0-9_]+", text) if t not in STOPWORDS and len(t) > 1]


class LexicalIndex:
    def __init__(self, ids: list[str], texts: list[str]):
        self.ids = ids
        self._bm25 = BM25Okapi([tokenize(t) for t in texts]) if texts else None

    def search(self, query: str, k: int) -> list[tuple[str, float]]:
        """-> [(chunk_id, bm25_score)] for chunks with a strictly positive score."""
        if self._bm25 is None:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        order = sorted(range(len(self.ids)), key=lambda i: -scores[i])
        return [(self.ids[i], float(scores[i])) for i in order[:k] if scores[i] > 0]
