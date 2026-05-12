"""Minimal LLM provider abstraction for Layer 4 runtime calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from .llm_adapter_interfaces import (
    AdapterError,
    CompletionRequest,
    CompletionResult,
    ErrorCategory,
    StructuredOutputAdapter,
    ToolCall,
    ToolCallingAdapter,
)


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


class OpenAIProvider(StructuredOutputAdapter, ToolCallingAdapter):
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

    async def complete(self, request: CompletionRequest) -> CompletionResult | AdapterError:
        try:
            result = await self.complete_text(
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            return CompletionResult(content=result.content)
        except Exception as exc:  # pragma: no cover - defensive normalization
            return self._normalize_error(exc)

    async def complete_with_tools(
        self,
        request: CompletionRequest,
        tools: list[dict[str, Any]],
    ) -> CompletionResult | AdapterError:
        try:
            kwargs: dict[str, Any] = {
                "model": request.model,
                "messages": request.messages,
                "temperature": request.temperature,
                "tools": tools,
            }
            if request.max_tokens is not None:
                kwargs["max_tokens"] = request.max_tokens
            response = await self._get_client().chat.completions.create(**kwargs)
            message = response.choices[0].message
            tool_calls = tuple(
                ToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments_json=call.function.arguments,
                )
                for call in (message.tool_calls or [])
            )
            return CompletionResult(content=(message.content or "").strip(), tool_calls=tool_calls)
        except Exception as exc:  # pragma: no cover - defensive normalization
            return self._normalize_error(exc)

    async def extract_structured(
        self,
        request: CompletionRequest,
        *,
        schema: dict[str, Any],
    ) -> dict[str, Any] | AdapterError:
        try:
            response = await self._get_client().chat.completions.create(
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                response_format={"type": "json_schema", "json_schema": schema},
            )
            import json

            return json.loads(response.choices[0].message.content or "{}")
        except Exception as exc:  # pragma: no cover - defensive normalization
            return self._normalize_error(exc)

    def _normalize_error(self, exc: Exception) -> AdapterError:
        msg = str(exc)
        lowered = msg.lower()
        if "timeout" in lowered:
            return AdapterError(ErrorCategory.TIMEOUT, msg, retryable=True)
        if "rate" in lowered and "limit" in lowered:
            return AdapterError(ErrorCategory.RATE_LIMIT, msg, retryable=True)
        return AdapterError(ErrorCategory.PROVIDER, msg, retryable=False)


def get_openai_provider(config: dict[str, Any] | None = None) -> OpenAIProvider:
    """Build the default OpenAI provider from an optional tool/workflow config."""
    api_key = config.get("openai_api_key") if config else None
    return OpenAIProvider(api_key=api_key)


def get_provider_adapters(config: dict[str, Any] | None = None) -> dict[str, OpenAIProvider]:
    """Registry of configured provider adapters for conformance tests and orchestration wiring."""
    return {"openai": get_openai_provider(config)}
