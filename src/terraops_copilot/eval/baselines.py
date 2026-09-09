"""Control agents to validate the harness BEFORE spending on a real model.

- oracle : calls exactly the required tools, then writes an answer containing the
           expected facts and a real citation. Must score ~100%. If it doesn't, the
           harness or a case is broken - not the model.
- null   : never calls a tool, always says 'je ne sais pas'. Must score ~0% on facts,
           100% refusal on refuse cases, and 100% over-refusal elsewhere.
- liar   : never calls a tool, answers confidently with invented numbers. Must light
           up the hallucination column. If it doesn't, the grader is too lenient.

They are LLMClient implementations, so they run through the SAME Agent loop and the
SAME tools as a real model - only the 'brain' is swapped.
"""
from __future__ import annotations

import json

from ..llm.base import LLMClient
from ..llm.types import LLMReply, Message, ToolCall, ToolResultMessage, ToolSpec, UserMessage
from .cases import Case, Expect

DEFAULT_ARGS = {"search_documentation": lambda q: {"query": q},
                "get_drift_report": lambda q: {"since_days": 7},
                "get_registry_champion": lambda q: {"alias": "champion"}}


class OracleLLM(LLMClient):
    name = "oracle"
    model = "oracle"

    def __init__(self):
        self.case: Case | None = None
        self.exp: Expect | None = None

    def bind(self, case: Case, exp: Expect) -> None:
        self.case, self.exp = case, exp

    def chat(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMReply:
        question = next(m.text for m in messages if isinstance(m, UserMessage))
        results = [m for m in messages if isinstance(m, ToolResultMessage)]
        if self.exp.required_tools and not results:
            calls = [ToolCall(id=f"o{i}", name=t, arguments=DEFAULT_ARGS.get(t, lambda q: {})(question))
                     for i, t in enumerate(sorted(self.exp.required_tools))]
            return LLMReply(text=None, tool_calls=calls, stop_reason="tool_use")
        if self.exp.refuse:
            return LLMReply(text="Je ne peux pas répondre : aucun outil disponible ne fournit "
                                 "cette information. Il faudrait un outil dédié.",
                            tool_calls=[], stop_reason="end_turn")
        parts = ["D'après " + ", ".join(sorted(self.exp.required_tools)) + " :"]
        parts += [group[0] for group in self.exp.facts]          # first alternative of each fact
        if self.exp.cite:
            for r in results:
                if r.name == "search_documentation":
                    passages = json.loads(r.content).get("passages", [])
                    if passages:
                        parts.append(f"[{passages[0]['citation']}]")
        return LLMReply(text=" ".join(parts), tool_calls=[], stop_reason="end_turn")


class NullLLM(LLMClient):
    name = "null"
    model = "null"

    def chat(self, system, messages, tools) -> LLMReply:
        return LLMReply(text="Je ne sais pas.", tool_calls=[], stop_reason="end_turn")


class LiarLLM(LLMClient):
    name = "liar"
    model = "liar"

    def chat(self, system, messages, tools) -> LLMReply:
        return LLMReply(text="Bien sûr. La version servie est la 7, le champion a 0.42 d'accuracy "
                             "au gate, il y a 1234 prédictions cette semaine et pas de dérive. "
                             "Le modèle a été rechargé. [README.md § Architecture]",
                        tool_calls=[], stop_reason="end_turn")
