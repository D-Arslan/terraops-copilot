"""Heading-aware chunking for Markdown (and a plain fallback for YAML/py).

Why not fixed-size windows: a chunk that starts mid-sentence in the middle of
'Concept n°2' and ends inside 'Concept n°3' embeds as a blur of both. Cutting on
headings keeps one idea per chunk, and the heading path becomes the citation
('learning.md § Sprint 4 › Concept n°1 — Data drift vs concept drift').

Long sections are then windowed with overlap so a sentence cut at the boundary
still appears whole in one of the two pieces.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

HEADING = re.compile(r"^(#{1,4})\s+(.*)$")


@dataclass
class Chunk:
    text: str
    source: str                 # file name
    heading_path: list[str] = field(default_factory=list)
    index: int = 0              # position inside the section (0 if not windowed)

    @property
    def citation(self) -> str:
        path = " › ".join(self.heading_path) if self.heading_path else "(top)"
        return f"{self.source} § {path}"

    @property
    def id(self) -> str:
        return f"{self.source}::{'/'.join(self.heading_path)}::{self.index}"


def split_markdown_sections(text: str) -> list[tuple[list[str], str]]:
    """-> [(heading_path, body)] in document order. Fenced code stays intact."""
    sections: list[tuple[list[str], str]] = []
    path: list[str] = []
    buf: list[str] = []
    in_fence = False

    def flush():
        body = "\n".join(buf).strip()
        if body:
            sections.append((list(path), body))
        buf.clear()

    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        m = HEADING.match(line) if not in_fence else None
        if m:
            flush()
            level, title = len(m.group(1)), m.group(2).strip()
            path = path[: level - 1] + [title]
        else:
            buf.append(line)
    flush()
    return sections


def window(text: str, size: int, overlap: int) -> list[str]:
    """Split on paragraph boundaries first, then hard-cut only if a paragraph is huge."""
    if len(text) <= size:
        return [text]
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces, cur = [], ""
    for p in paras:
        while len(p) > size:                      # a single giant paragraph
            pieces.append((cur + "\n\n" + p[:size]).strip() if cur else p[:size])
            p, cur = p[size - overlap:], ""
        if len(cur) + len(p) + 2 <= size:
            cur = f"{cur}\n\n{p}" if cur else p
        else:
            if cur:
                pieces.append(cur)
            # carry the tail of the previous piece as overlap
            tail = cur[-overlap:] if cur and overlap else ""
            cur = f"{tail}\n\n{p}".strip() if tail else p
    if cur:
        pieces.append(cur)
    return pieces


def chunk_document(text: str, source: str, size: int = 450, overlap: int = 75,
                   min_chars: int = 40, context_depth: int = 2) -> list[Chunk]:
    """size=450 chars ≈ 110 tokens: under MiniLM's 128-token window (see store.py).
    context_depth=2: prepend only the two nearest headings. The full path
    ('TerraOps — Learning Log › Sprint 4 › …') ate a third of the window for nothing."""
    chunks: list[Chunk] = []
    if source.endswith((".md", ".markdown")):
        sections = split_markdown_sections(text)
    else:                                          # yaml / py: one flat document
        sections = [([source], text)]
    for path, body in sections:
        for i, piece in enumerate(window(body, size, overlap)):
            if len(piece) < min_chars:
                continue
            # Prepend the heading path: the embedding then carries the topic even
            # for a paragraph that never repeats the section's subject.
            context = " › ".join(path[-context_depth:]) if context_depth else ""
            chunks.append(Chunk(text=f"{context}\n\n{piece}" if context else piece,
                                source=source, heading_path=path, index=i))
    return chunks
