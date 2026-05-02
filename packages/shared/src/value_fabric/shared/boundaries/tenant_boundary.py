"""Tenant context boundary enforcement — runtime security gate.

This module provides the ONLY authorized path for retrieving tenant context.
All code must use these functions instead of direct header access.

Enforcement:
- Import this module exclusively from shared.boundaries
- Direct headers['x-tenant-id'] access is a P0 violation (blocked by CI)
- require_tenant_context() raises TenantBoundaryError on missing context (fails closed)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional
from uuid import UUID

# Avoid importing FastAPI at module level to prevent circular import issues
if TYPE_CHECKING:
    from fastapi import Request

from ..identity.context import (
    RequestContext,
    get_request_context,
    require_context as _require_context,
)

logger = logging.getLogger(__name__)


class TenantBoundaryError(RuntimeError):
    """Raised when tenant context is required but not available.
    
    This is a security exception — the boundary fails closed.
    Do NOT catch and return None; let it propagate for proper HTTP 401/403 handling.
    """
    pass


def get_tenant_context() -> Optional[RequestContext]:
    """Get tenant context if available, or None.
    
    Use this for optional context retrieval (e.g., logging, optional filtering).
    For mandatory tenant checks, use require_tenant_context().
    
    Returns:
        RequestContext if authenticated, None otherwise.
    """
    return get_request_context()


def require_tenant_context() -> RequestContext:
    """Require tenant context — fails closed with TenantBoundaryError.
    
    This is the canonical replacement for:
    - headers['x-tenant-id']
    - headers.get('x-tenant-id')
    - request.headers.get('X-Tenant-ID')
    
    Raises:
        TenantBoundaryError: If no context is set (not authenticated).
    
    Returns:
        RequestContext with validated tenant_id.
    """
    ctx = get_request_context()
    if ctx is None:
        raise TenantBoundaryError(
            "Tenant context required but not set. "
            "Ensure GovernanceMiddleware is installed and request is authenticated."
        )
    return ctx


def require_tenant_from_request(request: Optional[object] = None) -> UUID:
    """Extract and validate tenant ID from request — fails closed.
    
    This replaces direct header access patterns:
    ❌ tenant_id = request.headers['X-Tenant-ID']
    ❌ tenant_id = request.headers.get('X-Tenant-ID')
    ✅ tenant_id = require_tenant_from_request(request)
    
    Args:
        request: FastAPI Request object (optional, for API compatibility).
    
    Raises:
        TenantBoundaryError: If tenant context cannot be resolved.
    
    Returns:
        Validated tenant UUID.
    """
    # First try the context var (set by GovernanceMiddleware)
    ctx = get_request_context()
    if ctx is not None:
        return ctx.tenant_id
    
    # Fail closed — do NOT fall back to direct header access
    raise TenantBoundaryError(
        "Cannot resolve tenant from request: no governance context set. "
        "Direct header access is prohibited — use shared.boundaries module."
    )


def get_tenant_id() -> Optional[UUID]:
    """Get tenant ID if available, or None.
    
    Returns:
        Tenant UUID if authenticated, None otherwise.
    """
    ctx = get_request_context()
    if ctx is not None:
        return ctx.tenant_id
    return None


def require_tenant_id() -> UUID:
    """Require tenant ID — fails closed.
    
    Raises:
        TenantBoundaryError: If no tenant context is available.
    
    Returns:
        Validated tenant UUID.
    """
    ctx = require_tenant_context()
    return ctx.tenant_id
