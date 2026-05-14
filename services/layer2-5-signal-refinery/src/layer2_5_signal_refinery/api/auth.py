"""Auth helpers for L2.5 Signal Refinery.

Wraps value_fabric.shared.identity with a graceful fallback for
environments where the shared package is not installed (e.g. isolated tests).
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import Depends, HTTPException, Request, status

from ..config import get_settings

logger = logging.getLogger(__name__)

try:
    from value_fabric.shared.identity.context import RequestContext, get_request_context
    from value_fabric.shared.identity.dependencies import require_authenticated

    SHARED_IDENTITY_AVAILABLE = True
except ImportError:
    SHARED_IDENTITY_AVAILABLE = False
    RequestContext = Any  # type: ignore[assignment,misc]

    def get_request_context() -> Any:  # type: ignore[misc]
        return None

    def require_authenticated() -> Any:  # type: ignore[misc]
        return None


def get_tenant_id_from_context(request: Request) -> str:
    """Extract tenant_id from RequestContext. Fail closed if missing.

    In production-like environments the X-Tenant-ID header fallback is
    disabled — tenant identity must come from the authenticated RequestContext.
    The fallback is permitted only in non-production environments (e.g. tests,
    local development) where GovernanceMiddleware may not be present.
    """
    ctx = get_request_context()
    if ctx is not None and getattr(ctx, "tenant_id", None):
        return str(ctx.tenant_id)

    # In production, refuse to fall back to a caller-supplied header.
    if get_settings().is_production:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context required.",
        )

    # Non-production fallback: X-Tenant-ID header (tests, local dev, service-to-service).
    tenant_id = request.headers.get("X-Tenant-ID")
    if tenant_id:
        return tenant_id

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tenant context required.",
    )
