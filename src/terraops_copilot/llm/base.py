"""The single interface the agent depends on."""
from __future__ import annotations

from abc import ABC, abstractmethod

from .types import LLMReply, Message, ToolSpec


class LLMClient(ABC):
    """Stateless: the full conversation is passed on every call.

    That is how both Anthropic and OpenAI-style APIs work anyway - the 'memory' of
    an agent is just the message list our loop keeps appending to.
    """

    name: str = "abstract"

    @abstractmethod
    def chat(self, system: str, messages: list[Message], tools: list[ToolSpec]) -> LLMReply:
        """One model turn. Must never execute a tool - only report what the model asked."""
