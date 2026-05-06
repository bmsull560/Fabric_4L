"""Thin FastAPI composition root for Layer 1.

Migration ledger:
- moved router groups: compatibility and security boundary endpoints under api/routes/.
- remaining in app_monolith: core ingestion endpoints and framework bootstrap.
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
