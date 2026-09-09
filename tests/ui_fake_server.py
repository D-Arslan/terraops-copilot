"""Test-only launcher: the real UI with a scripted brain, to exercise the recording
script without a provider.  NOT part of the product.

    streamlit run tests/ui_fake_server.py --server.port 8599 --server.headless true
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "tests")]

import terraops_copilot.cli as cli                                   # noqa: E402
from terraops_copilot.agent.loop import Agent                        # noqa: E402
from terraops_copilot.llm.base import LLMClient                      # noqa: E402
from terraops_copilot.llm.types import LLMReply, ToolCall, ToolResultMessage, UserMessage  # noqa: E402
from terraops_copilot.tools.base import NoArgs, Tool, ToolRegistry   # noqa: E402


class KeywordBrain(LLMClient):
    """Routes on keywords; answers from the tool result. Deterministic, offline."""
    name, model = "fake", "keyword-brain"

    def chat(self, system, messages, tools):
        q = next(m.text for m in messages if isinstance(m, UserMessage)).lower()
        results = [m for m in messages if isinstance(m, ToolResultMessage)]
        if results:
            r = results[-1]
            data = json.loads(r.content) if not r.is_error else {}
            if r.name == "search_documentation":
                p = data["passages"][0]
                return LLMReply(text=f"{p['text'][:160]}… [{p['citation']}]", tool_calls=[], stop_reason="end_turn")
            return LLMReply(text=f"D'après `{r.name}` : {json.dumps(data, ensure_ascii=False)[:200]}",
                            tool_calls=[], stop_reason="end_turn")
        if "c'est quoi" in q or "qu'est-ce" in q:
            return LLMReply(text="Je consulte la documentation, car c'est une question de concept.",
                            tool_calls=[ToolCall("c1", "search_documentation", {"query": q})], stop_reason="tool_use")
        if "dérive" in q or "drift" in q:
            return LLMReply(text="Je lance le rapport de dérive, car la question porte sur l'état actuel.",
                            tool_calls=[ToolCall("c1", "get_drift_report", {"since_days": 7})], stop_reason="tool_use")
        if "champion" in q:
            return LLMReply(text="Je consulte le registry MLflow, car la question porte sur l'état actuel.",
                            tool_calls=[ToolCall("c1", "get_registry_champion", {"alias": "champion"})], stop_reason="tool_use")
        return LLMReply(text="Je ne peux pas répondre : aucun outil disponible ne mesure la latence. "
                             "Il faudrait un outil sur /metrics.", tool_calls=[], stop_reason="end_turn")


def fake_agent(with_rag=True):
    from pydantic import BaseModel
    class Q(BaseModel):
        query: str = ""
        k: int = 4
    class D(BaseModel):
        since_days: int = 7
        source: str | None = None
    class A(BaseModel):
        alias: str = "champion"
    passages = {"passages": [{"citation": "learning.md § Sprint 4 — Monitoring, dérive et Continuous Training › Concept n°1 — Data drift vs concept drift",
                              "matched_by": ["dense", "lexical"],
                              "text": "Data drift : la distribution des ENTRÉES change (nuages, saison, capteur). Concept drift : la relation entrée→label change. Sans labels en production, seule la première est détectable."}]}
    reg = ToolRegistry([
        Tool("search_documentation", "docs", Q, lambda a: passages),
        Tool("get_drift_report", "drift", D, lambda a: {"window_days": 7, "status": "insufficient_data", "n_rows_in_window": 6, "min_rows_required": 200, "verdict": "inconclusive"}),
        Tool("get_registry_champion", "reg", A, lambda a: {"name": "terraops-eurosat", "version": "1", "aliases": ["champion"], "tags": {"gate_accuracy": "0.9810", "gate_result": "promoted"}}),
    ])
    return Agent(KeywordBrain(), reg)


cli.build_agent = fake_agent
exec(compile((ROOT / "ui" / "app.py").read_text(encoding="utf-8"), str(ROOT / "ui" / "app.py"), "exec"))
