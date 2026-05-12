"""Smart Router stub — restores the import surface needed by benchmark_router.py.

The full implementation was removed from the repo in an earlier refactor.
This stub exists only so the benchmark script remains importable and
syntax-checkable until a proper Layer 1 source tree is restored.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RouteType(Enum):
    """Routing strategy chosen by the smart router."""

    FAST = "fast"
    FAST_WITH_FALLBACK = "fast_with_fallback"
    BROWSER = "browser"


@dataclass
class RouteDecision:
    """Result of a routing decision."""

    route: RouteType
    reason: str


class SmartRouter:
    """Minimal stub that always routes to the browser path."""

    def decide(self, url: str, route_type: RouteType) -> RouteDecision:
        return RouteDecision(route=RouteType.BROWSER, reason="stub")
