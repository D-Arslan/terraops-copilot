"""The UI renders the loop's events: tool choice, reason, result, sources, answer.

Uses Streamlit's AppTest with the agent replaced by a FakeLLM-driven one, so no
provider, no TerraOps, no vector store is needed.
"""
import json

from fake_llm import FakeLLM, text_reply, tool_reply
from streamlit.testing.v1 import AppTest

from terraops_copilot.agent.loop import Agent
from terraops_copilot.llm.types import LLMReply, ToolCall
from terraops_copilot.tools.base import NoArgs, Tool, ToolRegistry

PASSAGES = {"passages": [{"citation": "learning.md § Sprint 4 › Concept n°1 — Data drift",
                          "matched_by": ["dense", "lexical"], "text": "La dérive..."}]}


def fake_agent():
    reg = ToolRegistry([Tool("search_documentation", "docs", NoArgs, lambda a: PASSAGES),
                        Tool("get_served_model", "served", NoArgs, lambda a: {"model_version": "1"})])
    reason = LLMReply(text="Je consulte la documentation, car c'est une question de concept.",
                      tool_calls=[ToolCall("c1", "search_documentation", {})], stop_reason="tool_use")
    return Agent(FakeLLM([reason, text_reply("La dérive est ... [learning.md § Concept n°1 — Data drift]")]), reg)


def test_loop_emits_events_in_order():
    events = []
    fake_agent().run("c'est quoi la dérive ?", on_event=lambda e: events.append(e[0]))
    assert events == ["thinking", "tool_call", "tool_result", "thinking", "answer"]


def test_ui_shows_reason_tool_sources_and_answer(monkeypatch):
    import terraops_copilot.cli as cli
    monkeypatch.setattr(cli, "build_agent", lambda with_rag=True: fake_agent())
    at = AppTest.from_file("ui/app.py", default_timeout=60)
    at.run()
    at.chat_input[0].set_value("c'est quoi la dérive ?").run()
    page = "\n".join(str(getattr(el, "value", el)) for el in at.main)
    assert "search_documentation" in page                 # tool chosen
    assert "Je consulte la documentation" in page          # the 'why'
    assert "learning.md § Sprint 4" in page                # RAG source rendered
    assert "[learning.md § Concept n°1" in page            # cited answer
    assert not at.exception
