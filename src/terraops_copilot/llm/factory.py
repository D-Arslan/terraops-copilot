"""Pick the provider from LLM_PROVIDER. The agent never imports a concrete client."""
from __future__ import annotations

import os

from .base import LLMClient

PROVIDERS = ("anthropic", "lmstudio")


def make_llm_client() -> LLMClient:
    provider = os.getenv("LLM_PROVIDER", "anthropic").lower()
    if provider == "anthropic":
        from .anthropic_client import AnthropicClient
        return AnthropicClient()
    if provider in ("lmstudio", "openai-compat", "ollama"):
        from .openai_compat_client import OpenAICompatClient
        return OpenAICompatClient()
    raise ValueError(f"Unknown LLM_PROVIDER={provider!r}; expected one of {PROVIDERS}")
