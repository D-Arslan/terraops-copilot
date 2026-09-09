"""Anthropic adapter (reference provider).

Wire format specifics absorbed here and nowhere else:
- tools carry `input_schema` (not `parameters`);
- the model's tool requests are `tool_use` content blocks inside an assistant message;
- our observations go back as `tool_result` blocks inside a USER message, matched by id;
- `stop_reason == "tool_use"` means 'I am waiting for results'.
"""
from __future__ import annotations

import json
import os

import anthropic

from .base import LLMClient
from .types import (AssistantMessage, LLMReply, Message, ToolCall, ToolResultMessage,
                    ToolSpec, UserMessage)

DEFAULT_MODEL = "claude-opus-5"


class AnthropicClient(LLMClient):
    name = "anthropic"

    def __init__(self, model: str | None = None, max_tokens: int = 4096):
        # Zero-arg constructor: reads ANTHROPIC_API_KEY (or an `ant auth login` profile).
        self._client = anthropic.Anthropic()
        self.model = model or os.getenv("ANTHROPIC_MODEL", DEFAULT_MODEL)
        self.max_tokens = max_tokens

    # -- neutral -> Anthropic -------------------------------------------------
    @staticmethod
    def _to_tool(spec: ToolSpec) -> dict:
        return {"name": spec.name, "description": spec.description,
                "input_schema": spec.parameters}

    @staticmethod
    def _to_messages(messages: list[Message]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            if isinstance(m, UserMessage):
                out.append({"role": "user", "content": m.text})
            elif isinstance(m, AssistantMessage):
                blocks: list[dict] = []
                if m.text:
                    blocks.append({"type": "text", "text": m.text})
                for c in m.tool_calls:
                    blocks.append({"type": "tool_use", "id": c.id, "name": c.name,
                                   "input": c.arguments})
                out.append({"role": "assistant", "content": blocks})
            elif isinstance(m, ToolResultMessage):
                block = {"type": "tool_result", "tool_use_id": m.call_id,
                         "content": m.content, "is_error": m.is_error}
                # Consecutive tool results must live in ONE user message.
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
        return out

    # -- the call -------------------------------------------------------------
    def chat(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMReply:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system,
            tools=[self._to_tool(t) for t in tools],
            messages=self._to_messages(messages),
        )
        text_parts, calls = [], []
        for block in response.content:
            if block.type == "text":
                text_parts.append(block.text)
            elif block.type == "tool_use":
                # `block.input` is already a dict; never string-match on it.
                calls.append(ToolCall(id=block.id, name=block.name,
                                      arguments=dict(block.input)))
        return LLMReply(
            text="\n".join(text_parts) or None,
            tool_calls=calls,
            stop_reason=response.stop_reason or "",
            usage={"input_tokens": response.usage.input_tokens,
                   "output_tokens": response.usage.output_tokens},
        )


def _debug_dump(messages: list[Message]) -> str:  # handy when a request is rejected
    return json.dumps(AnthropicClient._to_messages(messages), indent=2, ensure_ascii=False)
