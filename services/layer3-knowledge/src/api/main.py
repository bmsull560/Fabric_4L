"""Thin FastAPI composition root for Layer 3.

Migration ledger:
- moved router groups: system, entity/browser, value tree, formulas, benchmarks, query/search helpers.
- remaining in app_monolith: app wiring, legacy alias decorators, deprecation compatibility headers.

Canonical route ownership:
- Business logic must live in modules under `api/routes/`.
- `app_monolith` handlers are compatibility shims only and should delegate to
  route module implementations for backward compatibility endpoints.
"""

from __future__ import annotations

from ..api.app_monolith import (
    _security_config_l3,
    app,
    close_app_state,
    init_app_state,
    init_telemetry,
    lifespan,
)
from ..api.routes.system import get_system_metrics, set_app_metrics

__all__ = [
    "_security_config_l3",
    "app",
    "close_app_state",
    "get_system_metrics",
    "init_app_state",
    "init_telemetry",
    "lifespan",
    "set_app_metrics",
]
