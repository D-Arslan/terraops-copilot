"""Deterministic graders. Each returns an atomic verdict; the runner aggregates.

Design rules (from the eval checklist):
- atomic checks, not one blended score: tool_choice, facts, citation, refusal and
  hallucination are separate columns, so a failure is diagnosable;
- grade the OUTCOME (facts in the answer) plus the ROUTE (tool choice) as two
  different metrics - conflating them hides 'right answer, wrong tool';
- normalise before matching (case, accents, thousands/decimal separators) so a
  correct answer is not failed on formatting;
- 'no answer' is not 'negative answer': an empty/errored answer is reported as an
  error row upstream, never graded as a refusal or a wrong fact.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from ..agent.loop import AgentResult
from .cases import Expect

REFUSAL_MARKERS = [
    "je ne peux pas", "je ne suis pas en mesure", "impossible de", "pas d'outil", "aucun outil",
    "ne permet pas", "ne permettent pas", "ne dispose pas", "hors de mon périmètre", "hors périmètre",
    "je ne dispose", "n'est pas disponible", "pas disponible", "je n'ai pas accès", "n'ai pas d'accès",
    "ne peut pas être", "pas possible", "je ne sais pas", "ne couvre pas", "ne mentionne pas",
    "cannot", "can't", "unable", "not able", "no tool", "don't have", "not available", "out of scope",
    "ne peux pas prédire", "impossible à prédire", "ne peux pas prévoir", "il faudrait",
    "pas capable", "pas en mesure", "n'ont pas pu", "ne fournit pas", "ne fournissent pas",
]

CITATION = re.compile(r"\[([^\[\]]+?)\s*§\s*([^\[\]]+?)\]")
# Units may follow a number ("31,91ms", "98,1%"): only digits/dots are excluded around it,
# otherwise "31,91ms" was captured as the unsupported number "31" (seen in run 4).
NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)?(?!\d)")   # "224," counts; "p95" does not


def norm(s: str) -> str:
    s = re.sub(r"[*_`]+", "", s)          # markdown emphasis: "version **1**" == "version 1"
    s = unicodedata.normalize("NFKD", s.lower())
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", s)


NUMERIC_ALT = re.compile(r"^[\d.,\s%]+$")


def contains(haystack: str, needle: str) -> bool:
    """Substring match after normalisation; a purely numeric needle must sit on
    word boundaries ('1' must not match inside '1234' or '0.1')."""
    h, n = norm(haystack), norm(needle).strip()
    if NUMERIC_ALT.match(n):
        # Trailing zeros are the same number: '0.981' must accept '0.9810' (found in
        # the first real run), but '1' must still reject '1234' and '0.98' reject '0.981'.
        tail = r"0*" if "." in n or "," in n else ""
        return re.search(rf"(?<![\d.,]){re.escape(n)}{tail}(?![\d.,])", h) is not None
    # Start-of-word boundary for text: 'charge' must not match inside 'recharge'.
    # The end stays open so 'derive' still matches 'derives' / 'derivee'.
    return re.search(rf"(?<!\w){re.escape(n)}", h) is not None


@dataclass
class Grade:
    tool_choice: bool | None = None       # None = not applicable
    facts: bool | None = None
    missing_facts: list[list[str]] = field(default_factory=list)
    citation: bool | None = None
    refusal: bool | None = None           # refuse cases: did it refuse properly
    over_refusal: bool = False            # non-refuse cases: refused instead of answering
    forbidden_hit: list[str] = field(default_factory=list)
    unsupported_numbers: list[str] = field(default_factory=list)
    hallucination: bool = False           # forbidden phrase OR unsupported number (OR judge)
    tools_called: list[str] = field(default_factory=list)


def grade_tool_choice(called: list[str], exp: Expect) -> bool:
    called_set = set(called)
    if not exp.required_tools.issubset(called_set):
        return False
    return called_set.issubset(exp.allowed_tools) if exp.allowed_tools or not called else True


def grade_facts(answer: str, facts: list[list[str]]) -> tuple[bool, list[list[str]]]:
    missing = [group for group in facts if not any(contains(answer, alt) for alt in group)]
    return not missing, missing


def returned_citations(result: AgentResult) -> list[str]:
    """Citations the search tool actually returned (from the tool results)."""
    cites = []
    for step in result.steps:
        for r in step.results:
            if r.name == "search_documentation" and not r.is_error:
                cites += re.findall(r'"citation": "([^"]+)"', r.content)
    return cites


def grade_citation(answer: str, result: AgentResult) -> bool:
    """A [source § section] in the answer must match a returned passage: source
    equal and the section fragment contained in the real citation. A citation the
    tool never returned is itself a hallucination."""
    returned = [norm(c) for c in returned_citations(result)]
    for src, sec in CITATION.findall(answer):
        src_n, sec_n = norm(src.strip()), norm(sec.strip())
        for rc in returned:
            if rc.startswith(src_n) and (sec_n in rc or any(
                    part.strip() and part.strip() in rc for part in sec_n.split("›"))):
                return True
    return False


def refused(answer: str) -> bool:
    return any(contains(answer, m) for m in REFUSAL_MARKERS)


def numbers_in(text: str) -> set[str]:
    return {n.replace(",", ".") for n in NUMBER.findall(text)}


def unsupported_numbers(answer: str, question: str, result: AgentResult, exp: Expect) -> list[str]:
    """Numbers in the answer that appear nowhere in: question, tool results, expected
    facts. Cheap hallucination detector for factual answers. Small integers (<=12,
    e.g. '2 outils', '7 jours') are ignored to avoid flagging ordinary prose."""
    support = numbers_in(question)
    for step in result.steps:
        for r in step.results:
            support |= numbers_in(r.content)
    for group in exp.facts:
        for alt in group:
            support |= numbers_in(alt)
    out = []
    for n in sorted(numbers_in(answer)):
        try:
            v = float(n)
        except ValueError:
            continue
        if n in support or any(abs(v - float(s)) < 1e-9 for s in support if _isnum(s)):
            continue
        if v.is_integer() and v <= 12:
            continue
        # percentages written 98.1 while support has 0.981 (or the reverse)
        if any(_isnum(s) and (abs(v / 100 - float(s)) < 1e-6 or abs(v * 100 - float(s)) < 1e-6)
               for s in support):
            continue
        out.append(n)
    return out


def _isnum(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def grade(case_question: str, result: AgentResult, exp: Expect) -> Grade:
    answer = result.answer or ""
    g = Grade(tools_called=result.tools_called)
    g.tool_choice = grade_tool_choice(result.tools_called, exp)
    g.forbidden_hit = [p for p in exp.forbidden if contains(answer, p)]
    g.unsupported_numbers = unsupported_numbers(answer, case_question, result, exp)
    is_refusal = refused(answer)

    if exp.refuse:
        g.refusal = is_refusal and not g.unsupported_numbers and not g.forbidden_hit
        g.hallucination = bool(g.unsupported_numbers or g.forbidden_hit) or (
            not is_refusal and bool(numbers_in(answer)))
    else:
        g.facts, g.missing_facts = grade_facts(answer, exp.facts)
        g.over_refusal = is_refusal and not g.facts
        g.hallucination = bool(g.unsupported_numbers or g.forbidden_hit)
        if exp.cite:
            g.citation = grade_citation(answer, result)
            if CITATION.search(answer) and not g.citation:
                g.hallucination = True      # invented citation
    return g
