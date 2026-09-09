"""A scripted LLMClient: lets us test the LOOP without any network or API key.

Each call pops the next scripted reply. This is also the trick the eval will reuse:
the loop's behaviour must not depend on which provider is plugged in.
"""
from __future__ import annotations

from terraops_copilot.llm.base import LLMClient
from terraops_copilot.llm.types import LLMReply, Message, ToolCall, ToolSpec


class FakeLLM(LLMClient):
    name = "fake"

    def __init__(self, replies: list[LLMReply]):
        self._replies = list(replies)
        self.calls: list[tuple[str, list[Message], list[ToolSpec]]] = []

    def chat(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMReply:
        self.calls.append((system, list(messages), list(tools)))
        if not self._replies:
            return LLMReply(text="(no more scripted replies)", tool_calls=[], stop_reason="end_turn")
        return self._replies.pop(0)


def tool_reply(name: str, arguments: dict | None = None, call_id: str = "c1") -> LLMReply:
    return LLMReply(text=None, stop_reason="tool_use",
                    tool_calls=[ToolCall(id=call_id, name=name, arguments=arguments or {})])


def text_reply(text: str) -> LLMReply:
    return LLMReply(text=text, tool_calls=[], stop_reason="end_turn")
