"""Minimal LLM provider abstraction for Layer 4 runtime calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class LLMUsage:
    """Token usage returned by an LLM provider."""

    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass(frozen=True)
class LLMTextResponse:
    """Text response returned by an LLM provider."""

    content: str
    usage: LLMUsage


@dataclass(frozen=True)
class LLMEmbeddingResponse:
    """Embedding response returned by an LLM provider."""

    embedding: list[float]


class LLMProvider(Protocol):
    """Provider contract used by workflows and tools."""

    async def complete_text(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMTextResponse:
        """Return a text completion."""

    async def embed(self, *, model: str, text: str) -> LLMEmbeddingResponse:
        """Return an embedding for the given text."""


class OpenAIProvider:
    """OpenAI-backed provider implementation."""

    def __init__(self, *, api_key: str | None = None) -> None:
        self._api_key = api_key
        self._client: Any | None = None

    def _get_client(self) -> Any:
        if self._client is None:
            from openai import AsyncOpenAI

            self._client = AsyncOpenAI(api_key=self._api_key)
        return self._client

    async def complete_text(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int | None = None,
        response_format: dict[str, Any] | None = None,
    ) -> LLMTextResponse:
        kwargs: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens is not None:
            kwargs["max_tokens"] = max_tokens
        if response_format is not None:
            kwargs["response_format"] = response_format

        response = await self._get_client().chat.completions.create(**kwargs)
        usage = response.usage
        return LLMTextResponse(
            content=(response.choices[0].message.content or "").strip(),
            usage=LLMUsage(
                prompt_tokens=usage.prompt_tokens if usage else 0,
                completion_tokens=usage.completion_tokens if usage else 0,
            ),
        )

    async def embed(self, *, model: str, text: str) -> LLMEmbeddingResponse:
        response = await self._get_client().embeddings.create(model=model, input=text)
        return LLMEmbeddingResponse(embedding=response.data[0].embedding)


def get_openai_provider(config: dict[str, Any] | None = None) -> OpenAIProvider:
    """Build the default OpenAI provider from an optional tool/workflow config."""
    api_key = config.get("openai_api_key") if config else None
    return OpenAIProvider(api_key=api_key)
