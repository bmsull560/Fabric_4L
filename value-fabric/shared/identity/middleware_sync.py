"""Synchronous governance middleware stub for local validation.

This stub provides the minimal interfaces required by database.py
when the full async middleware is not available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional
from uuid import UUID

from fastapi import Header, HTTPException, Request, status

from .permissions import Permission, Role


@dataclass
class SyncRequestContext:
    """Synchronous request context stub."""

    tenant_id: UUID
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    api_key_id: Optional[str] = None
    permissions: FrozenSet[Permission] = field(default_factory=frozenset)
    source: str = "unknown"
    raw: Dict[str, Any] = field(default_factory=dict)


def get_request_context_sync(
    request: Request,
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SyncRequestContext:
    """Stub dependency that extracts tenant from X-Organization-ID header."""
    if x_organization_id:
        try:
            tenant_id = UUID(x_organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Organization-ID header",
            )
    else:
        # P0 FIX: Never fall back to a hardcoded tenant — require authentication
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return SyncRequestContext(tenant_id=tenant_id, source="header")


def require_request_context_sync(
    request: Request,
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SyncRequestContext:
    """Stub dependency that requires tenant from X-Organization-ID header."""
    if not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Organization-ID header required",
        )
    try:
        tenant_id = UUID(x_organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Organization-ID header",
        )

    return SyncRequestContext(tenant_id=tenant_id, source="header")
