"""Thin FastAPI composition root for Layer 3.

The large historical implementation lives in ``app_monolith`` while endpoint
groups continue to be extracted into focused route modules. This module is the
stable ASGI import target used by uvicorn and tests.
"""

from __future__ import annotations

from .app_monolith import (
    _security_config_l3,
    app,
    get_system_metrics,
    init_telemetry,
    set_app_metrics,
)

__all__ = [
    "_security_config_l3",
    "app",
    "get_system_metrics",
    "init_telemetry",
    "set_app_metrics",
]
