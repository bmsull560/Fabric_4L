"""Proxy rotation for Playwright crawler.

Supports ROUND_ROBIN, RANDOM, and LEAST_USED strategies with health tracking.
"""

import random
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class ProxyConfig:
    """Single proxy configuration."""

    id: str
    host: str
    port: int
    protocol: str = "http"
    username: str | None = None
    password: str | None = None
    country: str | None = None
    status: str = "ACTIVE"
    failure_count: int = 0
    last_used_at: datetime | None = None
    last_success_at: datetime | None = None
    average_response_time_ms: float = 0.0

    @property
    def server_url(self) -> str:
        """Playwright-compatible proxy server URL."""
        return f"{self.protocol}://{self.host}:{self.port}"

    def to_playwright_dict(self) -> dict[str, Any]:
        """Convert to Playwright proxy parameter dict."""
        proxy: dict[str, Any] = {"server": self.server_url}
        if self.username:
            proxy["username"] = self.username
        if self.password:
            proxy["password"] = self.password
        return proxy

    def mark_used(self) -> None:
        """Update last_used timestamp."""
        self.last_used_at = datetime.now(UTC)

    def mark_success(self, response_time_ms: float) -> None:
        """Record successful use and update average response time."""
        self.last_success_at = datetime.now(UTC)
        # Exponential moving average with alpha=0.3
        self.average_response_time_ms = (
            0.3 * response_time_ms + 0.7 * self.average_response_time_ms
        )
        self.failure_count = 0

    def mark_failure(self) -> None:
        """Record a failure."""
        self.failure_count += 1

    @property
    def is_healthy(self) -> bool:
        """Check if proxy is healthy and usable."""
        return self.status == "ACTIVE" and self.failure_count < 3


class ProxyRotator:
    """Rotate through a pool of proxies with configurable strategy."""

    def __init__(
        self,
        proxies: list[dict[str, Any]],
        strategy: str = "ROUND_ROBIN",
        max_failures_before_quarantine: int = 3,
    ):
        self._proxies = [ProxyConfig(**p) for p in proxies]
        self.strategy = strategy.upper()
        self.max_failures = max_failures_before_quarantine
        self._index = 0

    def _active_proxies(self) -> list[ProxyConfig]:
        """Return only healthy, active proxies."""
        active = [p for p in self._proxies if p.is_healthy]
        if not active:
            logger.warning("proxy_rotator_no_active_proxies", total=len(self._proxies))
        return active

    def get_next(self) -> ProxyConfig | None:
        """Select next proxy based on rotation strategy."""
        active = self._active_proxies()
        if not active:
            return None

        if self.strategy == "ROUND_ROBIN":
            proxy = active[self._index % len(active)]
            self._index += 1
        elif self.strategy == "RANDOM":
            proxy = random.choice(active)
        elif self.strategy == "LEAST_USED":
            proxy = min(
                active,
                key=lambda p: (p.last_used_at or datetime.min.replace(tzinfo=UTC)),
            )
        else:
            # Default to round-robin for unknown strategies
            proxy = active[self._index % len(active)]
            self._index += 1

        proxy.mark_used()
        logger.debug(
            "proxy_rotator_selected",
            proxy_id=proxy.id,
            strategy=self.strategy,
            host=proxy.host,
            country=proxy.country,
        )
        return proxy

    def report_result(self, proxy_id: str, success: bool, response_time_ms: float = 0.0) -> None:
        """Report crawl result for a proxy."""
        for proxy in self._proxies:
            if proxy.id == proxy_id:
                if success:
                    proxy.mark_success(response_time_ms)
                else:
                    proxy.mark_failure()
                    if proxy.failure_count >= self.max_failures:
                        proxy.status = "QUARANTINED"
                        logger.warning(
                            "proxy_quarantined",
                            proxy_id=proxy.id,
                            host=proxy.host,
                            failure_count=proxy.failure_count,
                        )
                break

    def get_stats(self) -> dict[str, Any]:
        """Return rotation statistics."""
        total = len(self._proxies)
        active = sum(1 for p in self._proxies if p.is_healthy)
        quarantined = sum(1 for p in self._proxies if p.status == "QUARANTINED")
        return {
            "total": total,
            "active": active,
            "quarantined": quarantined,
            "failed": total - active - quarantined,
            "strategy": self.strategy,
        }
