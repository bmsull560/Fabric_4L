"""Token limit enforcement for LLM requests (F-17).

Prevents requests that would exceed token limits, protecting against:
- Accidental token exhaustion
- Denial-of-wallet attacks (cost flooding)
- Context window overflow
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from .exceptions import TokenLimitError
from value_fabric.shared.models.typed_dict import TypedDictModel


class TokenLimiter_get_limit_infoResult(TypedDictModel):
    max_input_tokens: Any
    max_output_tokens: Any
    total_limit: Any

logger = logging.getLogger(__name__)


@dataclass
class TokenEstimate:
    """Estimated token count for a request."""

    estimated_tokens: int
    input_tokens: int
    max_output_tokens: int
    total_estimate: int
    exceeds_limit: bool


# Default estimation constants
DEFAULT_CHARS_PER_TOKEN = 4  # Conservative estimate for English text
DEFAULT_TOKEN_BUFFER = 50  # Safety buffer for estimation error
MIN_CHARS_PER_TOKEN = 1  # Minimum to prevent division issues


class TokenLimiter:
    """Enforce token limits on LLM requests.

    Rough estimation: ~4 characters per token for English text.
    This is conservative - actual tokenization varies by model and language.
    """

    def __init__(
        self,
        max_input_tokens: int | None = None,
        max_output_tokens: int | None = None,
        chars_per_token: int | None = None,
        token_buffer: int | None = None,
        fail_closed: bool | None = None,
    ) -> None:
        """Initialize TokenLimiter.

        Args:
            max_input_tokens: Maximum input tokens allowed. Defaults to env var.
            max_output_tokens: Maximum output tokens expected. Defaults to env var.
            chars_per_token: Characters per token estimate. Defaults to env var or 4.
            token_buffer: Safety buffer for estimation error. Defaults to 50.
            fail_closed: If True, raise exception on limit exceeded.
        """
        self.max_input_tokens = max_input_tokens or int(
            os.getenv("LLM_MAX_INPUT_TOKENS", "4000")
        )
        self.max_output_tokens = max_output_tokens or int(
            os.getenv("LLM_MAX_OUTPUT_TOKENS", "2000")
        )
        # Validate chars_per_token to prevent division issues
        cpt = chars_per_token or int(os.getenv("LLM_CHARS_PER_TOKEN", str(DEFAULT_CHARS_PER_TOKEN)))
        self.chars_per_token = max(MIN_CHARS_PER_TOKEN, cpt)
        self.token_buffer = token_buffer or DEFAULT_TOKEN_BUFFER
        self.fail_closed = (
            fail_closed
            if fail_closed is not None
            else os.getenv("LLM_SAFETY_FAIL_CLOSED", "").lower() in ("true", "1", "yes")
        )

    def estimate_tokens(self, text: str | None) -> int:
        """Estimate token count from text.

        Uses a conservative character-based estimate.
        For production, consider using tiktoken or model-specific tokenizers.

        Args:
            text: Text to estimate

        Returns:
            Estimated token count (minimum 0)
        """
        if not text or not isinstance(text, str):
            return 0
        # Conservative estimate: chars_per_token from config
        return max(0, len(text) // self.chars_per_token + self.token_buffer)

    def estimate_chat_tokens(self, messages: list[dict[str, str]]) -> TokenEstimate:
        """Estimate tokens for a chat completion request.

        Args:
            messages: List of chat messages

        Returns:
            TokenEstimate with detailed breakdown
        """
        # Estimate input tokens
        input_text = "\n".join(
            f"{msg.get('role', '')}: {msg.get('content', '')}"
            for msg in messages
        )
        input_tokens = self.estimate_tokens(input_text)

        # Add message overhead (~4 tokens per message for role/formatting)
        input_tokens += len(messages) * 4

        # Total estimate includes expected output
        total_estimate = input_tokens + self.max_output_tokens

        # Check against limit
        exceeds_limit = input_tokens > self.max_input_tokens

        return TokenEstimate(
            estimated_tokens=total_estimate,
            input_tokens=input_tokens,
            max_output_tokens=self.max_output_tokens,
            total_estimate=total_estimate,
            exceeds_limit=exceeds_limit,
        )

    def check_limit(
        self,
        messages: list[dict[str, str]],
        context: dict[str, Any] | None = None,
    ) -> TokenEstimate:
        """Check if request is within token limits.

        Args:
            messages: Chat messages to check
            context: Optional context for logging

        Returns:
            TokenEstimate with limit check results

        Raises:
            TokenLimitError: If fail_closed enabled and limit exceeded
        """
        estimate = self.estimate_chat_tokens(messages)

        if estimate.exceeds_limit:
            ctx = context or {}
            logger.warning(
                "Token limit exceeded",
                extra={
                    "estimated_input": estimate.input_tokens,
                    "max_input": self.max_input_tokens,
                    "message_count": len(messages),
                    "tenant_id": ctx.get("tenant_id"),
                    "request_id": ctx.get("request_id"),
                },
            )

            if self.fail_closed:
                raise TokenLimitError(
                    message=f"Token limit exceeded: {estimate.input_tokens} > {self.max_input_tokens}",
                    estimated_tokens=estimate.input_tokens,
                    max_tokens=self.max_input_tokens,
                    details={
                        "message_count": len(messages),
                        "context": context,
                    },
                )

        return estimate

    def get_limit_info(self) -> dict[str, int]:
        """Get current limit configuration.

        Returns:
            Dict with max_input_tokens and max_output_tokens
        """
        return TokenLimiter_get_limit_infoResult.model_validate({
            "max_input_tokens": self.max_input_tokens,
            "max_output_tokens": self.max_output_tokens,
            "total_limit": self.max_input_tokens + self.max_output_tokens,
        })


