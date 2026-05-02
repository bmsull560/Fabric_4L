"""Tenant-level LLM budget guardrails with throttling and escalation signals."""

from __future__ import annotations

import asyncio
import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from shared.identity.context import require_context

from ..metrics import get_metrics

logger = logging.getLogger(__name__)


class LLMBudgetExceededError(RuntimeError):
    """Raised when a tenant exceeds a hard budget threshold."""


@dataclass(slots=True)
class LLMBudgetDecision:
    """Result of pre-flight budget validation for an LLM request."""

    model: str
    throttle_seconds: int
    escalation_required: bool


class LLMBudgetGuardrails:
    """In-memory per-tenant budget guardrails.

    Caps and thresholds are configured by environment variables:
    - ``LLM_BUDGET_HOURLY_CAP_USD`` (default: 100)
    - ``LLM_BUDGET_DAILY_CAP_USD`` (default: 1000)
    - ``LLM_BUDGET_SOFT_THRESHOLD_RATIO`` (default: 0.8)
    - ``LLM_BUDGET_THROTTLE_SECONDS`` (default: 15)
    - ``LLM_BUDGET_FALLBACK_MODEL`` (default: gpt-4o-mini)
    """

    def __init__(self) -> None:
        self.hourly_cap_usd = float(os.getenv("LLM_BUDGET_HOURLY_CAP_USD", "100"))
        self.daily_cap_usd = float(os.getenv("LLM_BUDGET_DAILY_CAP_USD", "1000"))
        self.soft_threshold_ratio = float(os.getenv("LLM_BUDGET_SOFT_THRESHOLD_RATIO", "0.8"))
        self.throttle_seconds = int(os.getenv("LLM_BUDGET_THROTTLE_SECONDS", "15"))
        self.fallback_model = os.getenv("LLM_BUDGET_FALLBACK_MODEL", "gpt-4o-mini")

        self._usage_events: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def precheck_or_raise(self, model: str) -> LLMBudgetDecision:
        """Check budget state and return throttling/escalation decision.

        Raises:
            LLMBudgetExceededError: if hard cap was exceeded and request must be blocked.
        """
        ctx = require_context()
        tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "unknown"
        normalized_tenant = tenant_id.strip() or "unknown"

        async with self._lock:
            now = datetime.now(timezone.utc)  # noqa: UP017 (Python 3.10 compatibility)
            hourly_spend, daily_spend = self._window_spend_locked(normalized_tenant, now)

        if hourly_spend >= self.hourly_cap_usd or daily_spend >= self.daily_cap_usd:
            self._record_event(normalized_tenant, "blocked", "hard_cap_exceeded")
            raise LLMBudgetExceededError(
                "LLM budget hard cap exceeded "
                f"(hourly=${hourly_spend:.2f}/${self.hourly_cap_usd:.2f}, "
                f"daily=${daily_spend:.2f}/${self.daily_cap_usd:.2f})"
            )

        hourly_ratio = hourly_spend / self.hourly_cap_usd if self.hourly_cap_usd > 0 else 0.0
        daily_ratio = daily_spend / self.daily_cap_usd if self.daily_cap_usd > 0 else 0.0
        ratio = max(hourly_ratio, daily_ratio)

        if ratio >= self.soft_threshold_ratio:
            self._record_event(normalized_tenant, "throttled", "soft_cap_threshold")
            return LLMBudgetDecision(
                model=self.fallback_model,
                throttle_seconds=self.throttle_seconds,
                escalation_required=True,
            )

        return LLMBudgetDecision(model=model, throttle_seconds=0, escalation_required=False)

    async def record_usage(self, cost_usd: float) -> None:
        """Record observed LLM usage for budget window accounting."""
        ctx = require_context()
        tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "unknown"
        normalized_tenant = tenant_id.strip() or "unknown"
        if cost_usd <= 0:
            return

        async with self._lock:
            now = datetime.now(timezone.utc)  # noqa: UP017 (Python 3.10 compatibility)
            self._usage_events[normalized_tenant].append((now, cost_usd))
            self._prune_locked(normalized_tenant, now)

    def _window_spend_locked(self, tenant_id: str, now: datetime) -> tuple[float, float]:
        self._prune_locked(tenant_id, now)
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)

        hourly_spend = 0.0
        daily_spend = 0.0
        for ts, cost in self._usage_events[tenant_id]:
            if ts >= one_day_ago:
                daily_spend += cost
            if ts >= one_hour_ago:
                hourly_spend += cost

        return hourly_spend, daily_spend

    def _prune_locked(self, tenant_id: str, now: datetime) -> None:
        one_day_ago = now - timedelta(days=1)
        self._usage_events[tenant_id] = [
            event for event in self._usage_events[tenant_id] if event[0] >= one_day_ago
        ]

    def _record_event(self, tenant_id: str, action: str, reason: str) -> None:
        logger.warning(
            "LLM budget guardrail triggered",
            extra={"tenant_id": tenant_id, "action": action, "reason": reason},
        )
        metrics = get_metrics()
        if metrics:
            metrics.increment_llm_budget_guardrail_event(
                tenant_id=tenant_id,
                action=action,
                reason=reason,
            )


_budget_guardrails: LLMBudgetGuardrails | None = None


def get_llm_budget_guardrails() -> LLMBudgetGuardrails:
    """Return process-wide budget guardrails singleton."""
    global _budget_guardrails
    if _budget_guardrails is None:
        _budget_guardrails = LLMBudgetGuardrails()
    return _budget_guardrails
