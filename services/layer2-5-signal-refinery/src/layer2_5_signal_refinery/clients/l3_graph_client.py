"""L3 Knowledge Graph client for L2.5 Signal Refinery.

Pushes ValueSignal objects to L3 as graph nodes after refinement.
All operations are best-effort — L2.5 remains operational if L3 is unavailable.

Durability features:
  - Exponential backoff retry (3 attempts)
  - Circuit breaker: opens after 5 consecutive failures, closes after 30s
"""

from __future__ import annotations

import logging
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import get_settings

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """Simple in-memory circuit breaker for L3 calls."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._last_failure_time: float | None = None
        self._state = "closed"  # closed, open, half_open

    def record_success(self) -> None:
        self._failures = 0
        self._state = "closed"

    def record_failure(self) -> None:
        self._failures += 1
        self._last_failure_time = time.time()
        if self._failures >= self.failure_threshold:
            self._state = "open"

    def can_execute(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            if self._last_failure_time and (time.time() - self._last_failure_time) >= self.recovery_timeout:
                self._state = "half_open"
                return True
            return False
        return True  # half_open allows one probe

    @property
    def state(self) -> str:
        return self._state


class L3GraphClient:
    """Async HTTP client for the L3 Knowledge Graph signal endpoints.

    Uses a single shared httpx.AsyncClient for connection pooling across calls.
    Call ``aclose()`` during application shutdown to release connections.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._client = httpx.AsyncClient(timeout=10.0)
        self._circuit_breaker = CircuitBreaker()

    @property
    def _base_url(self) -> str:
        return self._settings.layer3_base_url.rstrip("/")

    async def aclose(self) -> None:
        """Close the underlying HTTP client. Call during application shutdown."""
        await self._client.aclose()

    async def push_signal(
        self,
        signal: dict[str, Any],
        tenant_id: str,
        request_id: str | None = None,
    ) -> bool:
        """Push a ValueSignal to L3 as a graph node.

        Returns True on success, False on any failure (non-blocking).
        Implements retry with exponential backoff and circuit breaker.
        """
        if not self._circuit_breaker.can_execute():
            logger.warning(
                "Circuit breaker OPEN for L3 — skipping signal %s",
                signal.get("id"),
            )
            return False

        headers = {"X-Tenant-ID": tenant_id}
        if request_id:
            headers["X-Request-ID"] = request_id

        @retry(
            retry=retry_if_exception_type((httpx.NetworkError, httpx.TimeoutException)),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        )
        async def _do_push() -> httpx.Response:
            return await self._client.post(
                f"{self._base_url}/api/v1/graph/signals",
                json=signal,
                headers=headers,
            )

        try:
            response = await _do_push()
            if response.status_code in (200, 201):
                self._circuit_breaker.record_success()
                return True
            logger.warning(
                "L3 signal push returned %s for signal %s",
                response.status_code,
                signal.get("id"),
            )
            self._circuit_breaker.record_failure()
            return False
        except Exception:
            self._circuit_breaker.record_failure()
            logger.warning(
                "L3 signal push failed for signal %s — L3 may be unavailable",
                signal.get("id"),
                exc_info=True,
            )
            return False

    async def get_account_signals(
        self,
        account_id: str,
        tenant_id: str,
        *,
        lifecycle_states: list[str] | None = None,
        signal_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Query L3 for ValueSignal nodes for an account.

        Returns empty list on failure.
        """
        params: dict[str, Any] = {"account_id": account_id}
        if lifecycle_states:
            params["lifecycle_states"] = lifecycle_states
        if signal_types:
            params["types"] = signal_types

        headers = {"X-Tenant-ID": tenant_id}
        try:
            response = await self._client.get(
                f"{self._base_url}/api/v1/graph/signals",
                params=params,
                headers=headers,
            )
            if response.status_code == 200:
                return response.json().get("items", [])
            return []
        except Exception:
            logger.warning("L3 signal query failed", exc_info=True)
            return []


_client: L3GraphClient | None = None


def get_l3_client() -> L3GraphClient:
    global _client
    if _client is None:
        _client = L3GraphClient()
    return _client
