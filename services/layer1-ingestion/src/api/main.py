"""Thin FastAPI composition root for Layer 1.

The historical API implementation is kept in ``app_monolith`` while we extract
domain routers and shared framework setup. This file remains the stable ASGI
entrypoint for ``uvicorn src.api.main:app``.
"""

from __future__ import annotations

from .app_monolith import (
    _security_config_l1,
    app,
    get_current_user_id,
    get_tenant_id,
    layer1_http_exception_handler,
)

__all__ = [
    "_security_config_l1",
    "app",
    "get_current_user_id",
    "get_tenant_id",
    "layer1_http_exception_handler",
]
