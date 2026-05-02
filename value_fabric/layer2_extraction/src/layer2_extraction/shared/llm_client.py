"""Unified async LLM client with cost tracking for OpenAI and Anthropic.

Provides a provider-agnostic interface for LLM API calls with automatic
cost tracking, retry logic, and token counting.

SECURITY: Week 4 - Integrated with llm_safety module for prompt injection,
PII redaction, token limits, output validation, and observability.
"""

import asyncio
import logging
import os
import random
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel
from shared.models.typed_dict import TypedDictModel


class CostRecord_to_dictResult(TypedDictModel):
    cost_usd: Any
    endpoint: Any
    extraction_job_id: Any
    input_tokens: Any
    model: Any
    output_tokens: Any
    provider: Any
    timestamp: Any

# Import LLM safety module (Week 4 hardening)
# Add shared/ to path if needed for imports
_SHARED_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "shared")
if _SHARED_PATH not in sys.path:
    sys.path.insert(0, _SHARED_PATH)

try:
    from llm_safety import (
        LLMSafetyError,
        OutputValidationError,
        PIIGuard,
        PromptGuard,
        TokenLimiter,
    )
    from llm_safety.observability import LLMCallContext, get_observability

    LLM_SAFETY_AVAILABLE = True
except ImportError:
    LLM_SAFETY_AVAILABLE = False
    PromptGuard = None  # type: ignore
    PIIGuard = None  # type: ignore
    TokenLimiter = None  # type: ignore
    LLMCallContext = None  # type: ignore
    get_observability = None  # type: ignore

# Import Prometheus metrics for LLM cost tracking (Task 85)
try:
    from ..metrics.prometheus_metrics import get_metrics as get_prometheus_metrics

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    get_prometheus_metrics = None

# OpenAI import with graceful fallback
try:
    from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
    from openai.types.chat import ChatCompletion

    OPENAI_AVAILABLE = True
    OPENAI_RETRY_EXCEPTIONS = (APIError, APITimeoutError, RateLimitError)
except ImportError:
    OPENAI_AVAILABLE = False
    AsyncOpenAI = None
    ChatCompletion = None
    OPENAI_RETRY_EXCEPTIONS = ()

# Anthropic import with graceful fallback
try:
    from anthropic import AsyncAnthropic, APIError as AnthropicAPIError
    from anthropic import RateLimitError as AnthropicRateLimitError

    ANTHROPIC_AVAILABLE = True
    ANTHROPIC_RETRY_EXCEPTIONS = (AnthropicAPIError, AnthropicRateLimitError)
except ImportError:
    ANTHROPIC_AVAILABLE = False
    AsyncAnthropic = None
    ANTHROPIC_RETRY_EXCEPTIONS = ()


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


@dataclass
class CostRecord:
    """Cost tracking record for a single API call."""

    extraction_job_id: str
    provider: str
    model: str
    endpoint: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return CostRecord_to_dictResult.model_validate({
            "extraction_job_id": self.extraction_job_id,
            "provider": self.provider,
            "model": self.model,
            "endpoint": self.endpoint,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost_usd": round(self.cost_usd, 6),
            "timestamp": self.timestamp.isoformat(),
        })


# Pricing per 1M tokens (as of April 2026)
PRICING = {
    "openai": {
        "gpt-4o": {"input": 2.50, "output": 10.00},
        "gpt-4o-mini": {"input": 0.15, "output": 0.60},
        "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    },
    "anthropic": {
        "claude-3-5-sonnet": {"input": 3.00, "output": 15.00},
        "claude-3-5-haiku": {"input": 0.80, "output": 4.00},
        "claude-3-opus": {"input": 15.00, "output": 75.00},
    },
}

# Retry configuration
RETRY_BACKOFF_BASE_SECONDS = 2.0
RETRY_JITTER_MAX_SECONDS = 0.25


class LLMClient:
    """Unified LLM client with cost tracking.

    Supports both OpenAI and Anthropic with automatic provider switching,
    cost calculation, and retry logic.

    Example:
        client = LLMClient(provider="openai", model="gpt-4o")

        response, cost = await client.chat_completion(
            messages=[{"role": "user", "content": "Hello"}],
            extraction_job_id="job_123",
            endpoint="entity_extraction"
        )
    """

    def __init__(
        self,
        provider: str | LLMProvider = "openai",
        model: str | None = None,
        api_key: str | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        cost_tracking_enabled: bool = True,
        resolve_model_from_registry: bool = False,
        registry_tenant_id: str | None = None,
        registry_api_token: str | None = None,
    ):
        """Initialize LLM client.

        Args:
            provider: "openai" or "anthropic"
            model: Model name (uses env var default if not provided)
            api_key: API key (uses env var if not provided)
            timeout: Request timeout in seconds
            max_retries: Max retry attempts for failed requests
            cost_tracking_enabled: Whether to track costs
            resolve_model_from_registry: Whether to resolve model from L4 registry
            registry_tenant_id: Tenant ID for registry lookup (required if resolve_model_from_registry=True)
            registry_api_token: API token for L4 registry authentication (optional)
        """
        self.provider = LLMProvider(provider)
        self.timeout = timeout
        self.max_retries = max_retries
        self.cost_tracking_enabled = cost_tracking_enabled
        self._cost_records: list[CostRecord] = []
        self._resolve_from_registry_enabled = resolve_model_from_registry
        self._registry_tenant_id = registry_tenant_id
        self._registry_api_token = registry_api_token

        # Week 4: Initialize safety guards
        if LLM_SAFETY_AVAILABLE:
            self._prompt_guard = PromptGuard()
            self._pii_guard = PIIGuard()
            self._token_limiter = TokenLimiter()
            self._observability = get_observability()
        else:
            self._prompt_guard = None
            self._pii_guard = None
            self._token_limiter = None
            self._observability = None

        # Set model with fallback to env vars
        if model:
            self.model = model
        elif self.provider == LLMProvider.OPENAI:
            self.model = os.getenv("L2_OPENAI_MODEL", "gpt-4o")
        else:
            self.model = os.getenv("L2_ANTHROPIC_MODEL", "claude-3-5-sonnet")

        # Initialize provider client
        if self.provider == LLMProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("openai package not installed. Run: pip install openai")
            api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key required (pass api_key or set OPENAI_API_KEY)")
            self._client = AsyncOpenAI(api_key=api_key, timeout=timeout)

        elif self.provider == LLMProvider.ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("anthropic package not installed. Run: pip install anthropic")
            api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError(
                    "Anthropic API key required (pass api_key or set ANTHROPIC_API_KEY)"
                )
            self._client = AsyncAnthropic(api_key=api_key, timeout=timeout)

    async def chat_completion(
        self,
        messages: list[dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        temperature: float = 0.0,
        tools: list[dict] | None = None,
        tool_choice: dict | None = None,
        logprobs: bool = False,
        top_logprobs: int | None = None,
    ) -> tuple[ChatCompletion, CostRecord | None]:
        """Execute chat completion with cost tracking.

        SECURITY: Runs pre-flight safety checks (prompt injection, PII redaction,
        token limits) and post-response validation.

        Args:
            messages: Chat messages
            extraction_job_id: Job ID for cost attribution
            endpoint: Endpoint name for cost tracking
            temperature: Sampling temperature
            tools: Function calling tools (OpenAI only)
            tool_choice: Force specific tool (OpenAI only)
            logprobs: Request logprobs (OpenAI only)
            top_logprobs: Number of alternative logprobs per token (OpenAI only)

        Returns:
            Tuple of (response, cost_record)
        """
        # Week 4: Pre-flight safety checks
        safe_messages = self._run_safety_checks(messages, extraction_job_id)

        if self.provider == LLMProvider.OPENAI:
            return await self._openai_completion(
                safe_messages,
                extraction_job_id,
                endpoint,
                temperature,
                tools,
                tool_choice,
                logprobs,
                top_logprobs,
            )
        else:
            return await self._anthropic_completion(
                safe_messages, extraction_job_id, endpoint, temperature
            )

    async def chat_completion_structured(
        self,
        messages: list[dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        response_format: type[BaseModel],
        temperature: float = 0.0,
    ) -> tuple[BaseModel, CostRecord | None]:
        """Execute structured output completion with Pydantic model validation.

        Uses OpenAI's beta.chat.completions.parse() API for type-safe responses.
        Note: Structured outputs API does not support logprobs parameter.

        Args:
            messages: Chat messages
            extraction_job_id: Job ID for cost attribution
            endpoint: Endpoint name for cost tracking
            response_format: Pydantic model class defining the expected response structure
            temperature: Sampling temperature (default: 0.0 for deterministic extraction)

        Returns:
            Tuple of (parsed_pydantic_model, cost_record)

        Raises:
            ValueError: If provider is Anthropic (not yet supported for structured outputs)
            RuntimeError: If max retries exceeded
        """
        if self.provider == LLMProvider.OPENAI:
            return await self._openai_structured_completion(
                messages, extraction_job_id, endpoint, response_format, temperature
            )
        else:
            # Anthropic doesn't support native structured outputs yet
            # Fall back to tool-based approach
            raise ValueError(
                "Structured outputs not yet supported for Anthropic. "
                "Use chat_completion() with tools parameter instead."
            )

    async def _openai_structured_completion(
        self,
        messages: list[dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        response_format: type[BaseModel],
        temperature: float,
    ) -> tuple[BaseModel, CostRecord | None]:
        """Execute OpenAI structured output completion using parse() API."""
        if not OPENAI_AVAILABLE:
            raise ImportError("openai package not installed. Run: pip install openai>=1.40.0")

        # Resolve model from registry if enabled
        effective_model = await self._get_effective_model()

        for attempt in range(self.max_retries):
            try:
                response = await self._client.beta.chat.completions.parse(
                    model=effective_model,
                    messages=messages,
                    temperature=temperature,
                    response_format=response_format,
                )

                # Calculate cost
                cost_record = None
                if self.cost_tracking_enabled:
                    cost_record = self._calculate_cost(
                        extraction_job_id=extraction_job_id,
                        provider="openai",
                        model=effective_model,
                        endpoint=endpoint,
                        input_tokens=response.usage.prompt_tokens if response.usage else 0,
                        output_tokens=response.usage.completion_tokens if response.usage else 0,
                        tenant_id=self._registry_tenant_id,
                    )
                    self._cost_records.append(cost_record)

                # Return parsed Pydantic model directly
                parsed_result = response.choices[0].message.parsed
                return parsed_result, cost_record

            except OPENAI_RETRY_EXCEPTIONS as exc:
                if attempt == self.max_retries - 1:
                    raise
                logger = logging.getLogger(__name__)
                wait_time = self._calculate_retry_wait(attempt)
                logger.warning(
                    f"OpenAI structured completion failed (attempt {attempt + 1}/{self.max_retries}): {exc}. Retrying in {wait_time:.2f}s..."
                )
                await asyncio.sleep(wait_time)
            except Exception:
                # Don't retry on unexpected errors (KeyboardInterrupt, SystemExit, etc.)
                raise

        raise RuntimeError("Max retries exceeded for OpenAI structured completion")

    async def _openai_completion(
        self,
        messages: list[dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        temperature: float,
        tools: list[dict] | None,
        tool_choice: dict | None,
        logprobs: bool,
        top_logprobs: int | None,
    ) -> tuple[ChatCompletion, CostRecord | None]:
        """Execute OpenAI chat completion."""

        # Resolve model from registry if enabled
        effective_model = await self._get_effective_model()

        for attempt in range(self.max_retries):
            try:
                # Build kwargs conditionally to ensure valid API parameters
                kwargs: dict[str, Any] = {
                    "model": effective_model,
                    "messages": messages,
                    "temperature": temperature,
                    "tools": tools,
                    "tool_choice": tool_choice,
                }
                if logprobs:
                    kwargs["logprobs"] = True
                    # top_logprobs must be an integer between 0 and 20
                    kwargs["top_logprobs"] = max(0, min(20, top_logprobs or 5))

                response = await self._client.chat.completions.create(**kwargs)

                # Calculate cost
                cost_record = None
                if self.cost_tracking_enabled:
                    cost_record = self._calculate_cost(
                        extraction_job_id=extraction_job_id,
                        provider="openai",
                        model=effective_model,
                        endpoint=endpoint,
                        input_tokens=response.usage.prompt_tokens if response.usage else 0,
                        output_tokens=response.usage.completion_tokens if response.usage else 0,
                        tenant_id=self._registry_tenant_id,
                    )
                    self._cost_records.append(cost_record)

                return response, cost_record

            except OPENAI_RETRY_EXCEPTIONS as exc:
                if attempt == self.max_retries - 1:
                    raise
                logger = logging.getLogger(__name__)
                wait_time = self._calculate_retry_wait(attempt)
                logger.warning(
                    f"OpenAI completion failed (attempt {attempt + 1}/{self.max_retries}): {exc}. Retrying in {wait_time:.2f}s..."
                )
                await asyncio.sleep(wait_time)
            except Exception:
                # Don't retry on unexpected errors (KeyboardInterrupt, SystemExit, etc.)
                raise

        raise RuntimeError("Max retries exceeded for OpenAI completion")

    async def _anthropic_completion(
        self,
        messages: list[dict[str, str]],
        extraction_job_id: str,
        endpoint: str,
        temperature: float,
    ) -> tuple[Any, CostRecord | None]:
        """Execute Anthropic chat completion."""

        # Resolve model from registry if enabled
        effective_model = await self._get_effective_model()

        # Convert messages to Anthropic format
        system_msg = None
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        for attempt in range(self.max_retries):
            try:
                kwargs = {
                    "model": effective_model,
                    "messages": anthropic_messages,
                    "temperature": temperature,
                    "max_tokens": 4096,
                }
                if system_msg:
                    kwargs["system"] = system_msg

                response = await self._client.messages.create(**kwargs)

                # Calculate cost
                cost_record = None
                if self.cost_tracking_enabled:
                    usage = response.usage
                    cost_record = self._calculate_cost(
                        extraction_job_id=extraction_job_id,
                        provider="anthropic",
                        model=effective_model,
                        endpoint=endpoint,
                        input_tokens=usage.input_tokens,
                        output_tokens=usage.output_tokens,
                        tenant_id=self._registry_tenant_id,
                    )
                    self._cost_records.append(cost_record)

                return response, cost_record

            except ANTHROPIC_RETRY_EXCEPTIONS as exc:
                if attempt == self.max_retries - 1:
                    raise
                logger = logging.getLogger(__name__)
                wait_time = self._calculate_retry_wait(attempt)
                logger.warning(
                    f"Anthropic completion failed (attempt {attempt + 1}/{self.max_retries}): {exc}. Retrying in {wait_time:.2f}s..."
                )
                await asyncio.sleep(wait_time)
            except Exception:
                # Don't retry on unexpected errors (KeyboardInterrupt, SystemExit, etc.)
                raise

        raise RuntimeError("Max retries exceeded for Anthropic completion")

    def _calculate_cost(
        self,
        extraction_job_id: str,
        provider: str,
        model: str,
        endpoint: str,
        input_tokens: int,
        output_tokens: int,
        tenant_id: str | None = None,
    ) -> CostRecord:
        """Calculate USD cost from token usage and record Prometheus metrics (Task 85)."""

        # Get pricing for model
        provider_pricing = PRICING.get(provider, {})
        if model not in provider_pricing:
            logging.getLogger(__name__).warning(
                f"Unknown model '{model}' for provider '{provider}', using zero pricing. "
                f"Update PRICING table in llm_client.py"
            )
        model_pricing = provider_pricing.get(model, {"input": 0, "output": 0})

        # Calculate cost per 1M tokens
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        total_cost = input_cost + output_cost

        # Record Prometheus metrics (Task 85)
        if PROMETHEUS_AVAILABLE and get_prometheus_metrics:
            metrics = get_prometheus_metrics()
            if metrics:
                # Record cost in USD
                metrics.record_llm_cost(
                    provider=provider,
                    model=model,
                    tenant_id=tenant_id or "unknown",
                    cost_usd=total_cost,
                )
                # Record token counts
                if input_tokens > 0:
                    metrics.record_llm_tokens(
                        provider=provider,
                        model=model,
                        token_type="prompt",
                        count=input_tokens,
                    )
                if output_tokens > 0:
                    metrics.record_llm_tokens(
                        provider=provider,
                        model=model,
                        token_type="completion",
                        count=output_tokens,
                    )

        return CostRecord(
            extraction_job_id=extraction_job_id,
            provider=provider,
            model=model,
            endpoint=endpoint,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=total_cost,
        )

    def _run_safety_checks(
        self, messages: list[dict[str, str]], extraction_job_id: str
    ) -> list[dict[str, str]]:
        """Run pre-flight safety checks on messages.

        SECURITY: Week 4 - Applies prompt injection detection, PII redaction,
        and token limit enforcement before sending to LLM.

        Args:
            messages: Original chat messages
            extraction_job_id: Job ID for context

        Returns:
            Sanitized messages safe for LLM processing

        Raises:
            PromptInjectionError: If prompt injection detected and fail-closed
            TokenLimitError: If token limit exceeded and fail-closed
        """
        if not LLM_SAFETY_AVAILABLE:
            return messages

        context = {
            "tenant_id": self._registry_tenant_id,
            "extraction_job_id": extraction_job_id,
        }

        # Check token limits first (most efficient)
        if self._token_limiter:
            self._token_limiter.check_limit(messages, context=context)

        # Scan each message for prompt injection and PII
        safe_messages: list[dict[str, str]] = []
        for msg in messages:
            content = msg.get("content", "")

            # F-13: Check for prompt injection
            if self._prompt_guard:
                self._prompt_guard.check(content, context=context)

            # F-14: Redact PII
            if self._pii_guard:
                result = self._pii_guard.redact(content, context=context)
                content = result.sanitized_text

            safe_messages.append({**msg, "content": content})

        return safe_messages

    def _calculate_retry_wait(self, attempt: int) -> float:
        """Calculate exponential backoff with jitter for retry delays.

        Args:
            attempt: Current retry attempt (0-indexed)

        Returns:
            Wait time in seconds before next retry
        """
        return (RETRY_BACKOFF_BASE_SECONDS**attempt) + random.uniform(
            0, RETRY_JITTER_MAX_SECONDS
        )

    async def _resolve_from_registry(self) -> str | None:
        """Resolve model from L4 registry if enabled.

        Returns:
            Model name from registry, or None if not enabled/failed
        """
        if not self._resolve_from_registry_enabled:
            return None

        if not self._registry_tenant_id:
            # Registry resolution enabled but no tenant ID - warn and skip
            import logging

            logging.getLogger(__name__).warning(
                "Model registry resolution enabled but no tenant_id provided. "
                "Set registry_tenant_id or disable resolve_model_from_registry."
            )
            return None

        try:
            from ..integration.model_registry_client import ModelRegistryClient

            async with ModelRegistryClient() as client:
                model = await client.resolve_model(
                    tenant_id=self._registry_tenant_id,
                    provider=self.provider.value,
                    api_token=self._registry_api_token,
                )
                return model if model != self.model else None  # Only update if different
        except Exception as exc:
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to resolve model from registry: {exc}. Using default: {self.model}"
            )
            return None

    async def _get_effective_model(self) -> str:
        """Get model name, resolving from registry if enabled.

        Returns:
            Model name to use for API calls
        """
        if self._resolve_from_registry_enabled:
            registry_model = await self._resolve_from_registry()
            if registry_model:
                return registry_model
        return self.model

    def get_cost_records(self) -> list[CostRecord]:
        """Get all recorded costs."""
        return self._cost_records.copy()

    def get_total_cost(self) -> float:
        """Get total cost of all requests."""
        return sum(record.cost_usd for record in self._cost_records)

    def clear_cost_records(self) -> None:
        """Clear cost history."""
        self._cost_records.clear()
