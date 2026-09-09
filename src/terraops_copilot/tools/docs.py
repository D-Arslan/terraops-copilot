"""search_documentation: the RAG tool.

Retrieval is exposed to the model as ONE MORE TOOL, with the same validation path
as the API tools. The model decides between 'look it up in the docs' and 'ask the
live system' from the descriptions alone - that decision is the whole point of
Sprint 2, so the description below draws the line explicitly.

Over-retrieval guard rails, all on our side:
- k is capped (default 4, max 6): more chunks = more tokens = more chances for the
  model to pick a distractor;
- a hit is kept only if the dense similarity clears a floor OR a query term occurs
  literally in the chunk; an empty result tells the model to say so rather than
  answer from memory;
- each hit is returned with its citation so the answer can be sourced.
"""
from __future__ import annotations

from pydantic import BaseModel, Field

from ..rag.store import HybridRetriever
from .base import Tool

MAX_K = 6
MIN_DENSE = 0.25   # cosine floor for a chunk found by embeddings only
MAX_PER_SECTION = 2


class SearchArgs(BaseModel):
    model_config = {"extra": "forbid"}
    query: str = Field(description="What to look up, as a short natural-language question or "
                                   "topic (French or English), e.g. 'data drift vs concept drift', "
                                   "'seuils du gate de promotion'.")
    k: int = Field(default=4, ge=1, le=MAX_K,
                   description="Number of passages to return (1-6). Keep the default unless "
                               "the first search was clearly incomplete.")


def build_docs_tool(retriever: HybridRetriever) -> Tool:
    def run(args: SearchArgs) -> dict:
        hits, per_section = [], {}
        for h in retriever.search(args.query, k=args.k * 2):
            if not (h.lexical_score > 0 or h.dense_score >= MIN_DENSE):
                continue
            # Overlapping windows of one section are near-duplicates: at most two
            # per section, so the model sees breadth rather than the same idea 4x.
            if per_section.get(h.citation, 0) >= MAX_PER_SECTION:
                continue
            per_section[h.citation] = per_section.get(h.citation, 0) + 1
            hits.append(h)
            if len(hits) == args.k:
                break
        if not hits:
            return {"passages": [], "note": "No relevant passage in the documentation. "
                                            "Tell the user the docs do not cover this."}
        return {"passages": [{"citation": h.citation, "matched_by": h.channels,
                              "text": h.text} for h in hits]}

    return Tool(
        name="search_documentation",
        description=(
            "Search the TerraOps project documentation (README, learning journal, design "
            "notes, params.yaml comments, alerting rules) and return the most relevant "
            "passages with their citations. Use it for CONCEPTUAL or 'how/why' questions "
            "whose answer is written knowledge that does not change at runtime: what "
            "drift is, how the champion/challenger promotion gate works and its "
            "thresholds, why Wasserstein rather than a p-value, what train/serving skew "
            "is, the known limits of the project, how CI/CT is wired. Do NOT use it for "
            "the CURRENT STATE of the system (is there drift now, which version is "
            "served, is the API up, metrics): those need the live tools. Every answer "
            "built from these passages must cite them as [source § section]."
        ),
        args_model=SearchArgs,
        run=run,
    )
