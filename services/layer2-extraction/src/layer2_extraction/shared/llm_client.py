"""Shared LLM client for Layer 2 extraction services."""

from __future__ import annotations

import os
from enum import Enum
from typing import Any


class LLMProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """Unified LLM client supporting OpenAI and Anthropic providers."""

    def __init__(
        self,
        provider: str | LLMProvider = LLMProvider.OPENAI,
        api_key: str | None = None,
    ) -> None:
        if isinstance(provider, str):
            try:
                self.provider = LLMProvider(provider)
            except ValueError as exc:
                raise ValueError(f"'{provider}' is not a valid LLMProvider") from exc
        else:
            self.provider = provider

        self._api_key = api_key

        if self.provider == LLMProvider.OPENAI:
            key = api_key or os.environ.get("OPENAI_API_KEY", "")
            if not key:
                raise ValueError("OpenAI API key required")
            self._api_key = key
            import openai
            self._client: Any = openai.AsyncOpenAI(api_key=key)
        elif self.provider == LLMProvider.ANTHROPIC:
            key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
            if not key:
                raise ValueError("Anthropic API key required")
            self._api_key = key
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(api_key=key)
            except ImportError:
                self._client = None
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    async def complete(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        """Send a completion request and return the text response."""
        if self.provider == LLMProvider.OPENAI:
            resp = await self._client.chat.completions.create(
                model=kwargs.get("model", "gpt-4o"),
                messages=messages,
                temperature=kwargs.get("temperature", 0.0),
            )
            return resp.choices[0].message.content or ""
        elif self.provider == LLMProvider.ANTHROPIC:
            if self._client is None:
                raise RuntimeError("Anthropic client not available")
            resp = await self._client.messages.create(
                model=kwargs.get("model", "claude-3-sonnet-20240229"),
                max_tokens=kwargs.get("max_tokens", 1024),
                messages=messages,
                temperature=kwargs.get("temperature", 0.0),
            )
            return resp.content[0].text if resp.content else ""
        raise ValueError(f"Unsupported provider: {self.provider}")
