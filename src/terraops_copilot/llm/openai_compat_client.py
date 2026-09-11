"""OpenAI-compatible adapter: LM Studio (local, free), also Ollama or OpenAI itself.

LM Studio serves http://localhost:1234/v1 speaking the OpenAI Chat Completions dialect.
Wire format specifics absorbed here:
- tools are wrapped as {"type": "function", "function": {...,"parameters": schema}};
- the model's requests come as `message.tool_calls[]` with `function.arguments` as a
  JSON *string* (must be parsed - and may be invalid JSON on small local models);
- our observations go back as a separate message with role "tool";
- `finish_reason == "tool_calls"` means 'waiting for results'.
"""
from __future__ import annotations

import json
import os
import re

from openai import OpenAI

from .base import LLMClient
from .types import (AssistantMessage, LLMReply, Message, ToolCall, ToolResultMessage,
                    ToolSpec, UserMessage)


TEXT_TOOL_CALL = re.compile(
    r"\[(?P<tag>TOOL_REQUEST|[A-Za-z_]\w*)\]\s*(?P<json>\{.*?\})\s*\[END_TOOL_REQUEST\]", re.S)


def salvage_text_tool_calls(text: str) -> tuple[str | None, list[ToolCall]]:
    """Turn '[tool_name] {json} [END_TOOL_REQUEST]' (or '[TOOL_REQUEST] {"name":..,
    "arguments":..} [END_TOOL_REQUEST]') written in the assistant text into ToolCalls.
    Returns the remaining text (the model's 'why' sentence) and the calls. Malformed
    JSON is left in the text untouched: the loop will then end the turn normally."""
    calls: list[ToolCall] = []

    def _sub(m: re.Match) -> str:
        try:
            payload = json.loads(m.group("json"))
        except json.JSONDecodeError:
            return m.group(0)
        if m.group("tag") == "TOOL_REQUEST":
            name, args = payload.get("name"), payload.get("arguments", {})
        else:
            name, args = m.group("tag"), payload
        if not name or not isinstance(args, dict):
            return m.group(0)
        calls.append(ToolCall(id=f"salvaged-{len(calls)}", name=name, arguments=args))
        return ""

    remaining = TEXT_TOOL_CALL.sub(_sub, text).strip()
    return (remaining or None), calls


class OpenAICompatClient(LLMClient):
    name = "openai-compat"

    def __init__(self, base_url: str | None = None, api_key: str | None = None,
                 model: str | None = None, max_tokens: int = 2048):
        self._client = OpenAI(
            base_url=base_url or os.getenv("OPENAI_COMPAT_BASE_URL", "http://localhost:1234/v1"),
            api_key=api_key or os.getenv("OPENAI_COMPAT_API_KEY", "lm-studio"),
        )
        self.model = model or os.getenv("OPENAI_COMPAT_MODEL") or self._first_loaded_model()
        self.max_tokens = max_tokens

    def _first_loaded_model(self) -> str:
        """LM Studio needs a model id; default to whatever is loaded in the UI."""
        models = self._client.models.list().data
        if not models:
            raise RuntimeError("No model loaded in the local server (LM Studio). "
                               "Load one, or set OPENAI_COMPAT_MODEL.")
        return models[0].id

    # -- neutral -> OpenAI ----------------------------------------------------
    @staticmethod
    def _to_tool(spec: ToolSpec) -> dict:
        return {"type": "function",
                "function": {"name": spec.name, "description": spec.description,
                             "parameters": spec.parameters}}

    @staticmethod
    def _to_messages(system: str, messages: list[Message]) -> list[dict]:
        out: list[dict] = [{"role": "system", "content": system}]
        for m in messages:
            if isinstance(m, UserMessage):
                out.append({"role": "user", "content": m.text})
            elif isinstance(m, AssistantMessage):
                msg: dict = {"role": "assistant", "content": m.text or ""}
                if m.tool_calls:
                    msg["tool_calls"] = [{
                        "id": c.id, "type": "function",
                        "function": {"name": c.name, "arguments": json.dumps(c.arguments)},
                    } for c in m.tool_calls]
                out.append(msg)
            elif isinstance(m, ToolResultMessage):
                content = m.content if not m.is_error else f"ERROR: {m.content}"
                out.append({"role": "tool", "tool_call_id": m.call_id, "content": content})
        return out

    # -- the call -------------------------------------------------------------
    def chat(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMReply:
        kwargs = {}
        if tools:  # some local servers reject an empty tools list
            kwargs["tools"] = [self._to_tool(t) for t in tools]
        response = self._client.chat.completions.create(
            model=self.model,
            messages=self._to_messages(system, messages),
            max_tokens=self.max_tokens,
            **kwargs,
        )
        choice = response.choices[0]
        text = choice.message.content or None
        calls = []
        for tc in choice.message.tool_calls or []:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                # Small local models do emit broken JSON. Surface it as a call with a
                # marker so the registry rejects it and the model gets to retry.
                args = {"__invalid_json__": tc.function.arguments}
            calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))
        if not calls and text:
            # Measured on Qwen2.5-7B via LM Studio: when the model writes a sentence
            # BEFORE the call, the server fails to parse its tool-request markup and
            # returns it as plain text. The decision was right; only the transport lost
            # it. Salvage it here - this is exactly what an adapter is for.
            text, calls = salvage_text_tool_calls(text)
        usage = response.usage
        return LLMReply(
            text=text,
            tool_calls=calls,
            stop_reason=choice.finish_reason or "",
            usage={"input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                   "output_tokens": getattr(usage, "completion_tokens", 0) or 0},
        )
