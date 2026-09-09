"""RAG without any model download: a fake embedder that projects on keywords.

Tests the chunker (structure + citations), the store round-trip, and the tool's
over-retrieval guard rails (k cap, relevance floor, citation in every passage).
"""
import math
import re
import zlib

import pytest

from terraops_copilot.llm.types import ToolCall
from terraops_copilot.rag.chunking import Chunk, chunk_document, split_markdown_sections, window
from terraops_copilot.rag.store import HybridRetriever, VectorStore
from terraops_copilot.tools.base import ToolRegistry
from terraops_copilot.tools.docs import MAX_K, build_docs_tool

DOC = """# TerraOps

Intro paragraph long enough to be kept as a chunk in the store.

## Sprint 4 — Monitoring

### Concept n°1 — Data drift vs concept drift

Data drift: the inputs change. Concept drift: the relation input→label changes.
Only the first is detectable without labels.

```
# a heading inside a fence must not split
```

### Concept n°2 — Wasserstein

Effect size instead of p-value, because volume inflates p-values.
"""

KEYWORDS = ["drift", "wasserstein", "gate", "champion"]


def fake_embed(texts):
    """Keyword dimensions (weight 1) + hashed-word dimensions (weight 0.1).

    Deterministic, no model. Two texts sharing no keyword AND no word end up nearly
    orthogonal, which is what a real embedder would do with 'pizza' vs 'drift'.
    """
    out = []
    for t in texts:
        words = re.findall(r"\w+", t.lower())
        v = [float(t.lower().count(k)) for k in KEYWORDS] + [0.0] * 64
        for w in set(words):
            v[len(KEYWORDS) + zlib.crc32(w.encode()) % 64] += 0.1
        n = math.sqrt(sum(x * x for x in v)) or 1.0
        out.append([x / n for x in v])
    return out


def test_sections_follow_heading_hierarchy_and_ignore_fenced_headings():
    sections = split_markdown_sections(DOC)
    paths = [p for p, _ in sections]
    assert ["TerraOps"] in paths
    assert ["TerraOps", "Sprint 4 — Monitoring", "Concept n°1 — Data drift vs concept drift"] in paths
    assert all("a heading inside a fence" not in " ".join(p) for p in paths)


def test_chunks_carry_citation_and_heading_context():
    chunks = chunk_document(DOC, "learning.md")
    c = next(c for c in chunks if "Concept n°1" in c.citation)
    assert c.citation.startswith("learning.md § TerraOps › Sprint 4")
    # only the two nearest headings are prepended (MiniLM's 128-token window is small)
    assert c.text.startswith("Sprint 4 — Monitoring › Concept n°1")


def test_window_overlaps_long_text():
    text = "\n\n".join(f"paragraph {i} " + "x" * 200 for i in range(10))
    pieces = window(text, size=600, overlap=100)
    assert len(pieces) > 1 and all(len(p) <= 600 + 2 for p in pieces)


@pytest.fixture
def store(tmp_path):
    s = VectorStore(tmp_path / "store", fake_embed)
    s.rebuild(chunk_document(DOC, "learning.md"))
    return s


@pytest.fixture
def retriever(store):
    return HybridRetriever(store)


def test_store_round_trip_ranks_relevant_chunk_first(store):
    hits = store.search("what is drift", k=2)
    assert hits and "drift" in hits[0].text.lower()
    assert hits[0].citation.startswith("learning.md § ")


def test_hybrid_merges_both_channels(retriever):
    hits = retriever.search("wasserstein p-value", k=2)
    assert hits and "wasserstein" in hits[0].text.lower()
    assert "lexical" in hits[0].channels and hits[0].lexical_score > 0
    # a second identical query must give identical results (no leaked state)
    assert [h.id for h in retriever.search("wasserstein p-value", k=2)] == [h.id for h in hits]


def test_stopwords_do_not_match(retriever):
    from terraops_copilot.rag.lexical import tokenize
    assert tokenize("c'est quoi la dérive ?") == ["derive"]
    assert tokenize("What is the min_delta of the gate?") == ["min_delta", "gate"]


def test_tool_returns_citations_and_caps_k(retriever):
    reg = ToolRegistry([build_docs_tool(retriever)])
    ok = reg.execute(ToolCall("1", "search_documentation", {"query": "drift", "k": 2}))
    assert not ok.is_error and '"citation": "learning.md §' in ok.content
    too_many = reg.execute(ToolCall("2", "search_documentation", {"query": "drift", "k": MAX_K + 5}))
    assert too_many.is_error   # validation, before any retrieval


def test_tool_reports_no_relevant_passage(retriever):
    reg = ToolRegistry([build_docs_tool(retriever)])
    res = reg.execute(ToolCall("1", "search_documentation", {"query": "pizza delivery"}))
    assert not res.is_error and '"passages": []' in res.content
