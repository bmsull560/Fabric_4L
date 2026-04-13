"""API key management routes (tenant_admin only).

POST   /v1/api-keys              — create an API key
GET    /v1/api-keys              — list API keys for caller's tenant
DELETE /v1/api-keys/{key_id}     — revoke (soft-delete) an API key
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.identity.context import RequestContext
from shared.identity.dependencies import require_tenant_admin
from shared.identity.models import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyModel,
)

from ....database import get_db
from ...service import create_api_key, list_api_keys, revoke_api_key

router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post("", response_model=APIKeyCreateResponse, status_code=status.HTTP_201_CREATED)
async def api_create_key(
    request: APIKeyCreateRequest,
    ctx: RequestContext = Depends(require_tenant_admin),
    db: AsyncSession = Depends(get_db),
) -> APIKeyCreateResponse:
    """Create a new API key scoped to the caller's tenant.

    The raw secret is returned **once** in ``api_key``; store it securely.
    Requires ``tenant_admin`` role.
    """
    from uuid import UUID

    user_id = UUID(ctx.user_id) if ctx.user_id else None
    return await create_api_key(db, ctx.tenant_id, request, user_id=user_id)


@router.get("", response_model=List[APIKeyModel])
async def api_list_keys(
    enabled_only: bool = Query(True),
    ctx: RequestContext = Depends(require_tenant_admin),
    db: AsyncSession = Depends(get_db),
) -> List[APIKeyModel]:
    """List API keys for the caller's tenant. Requires ``tenant_admin`` role."""
    return await list_api_keys(db, ctx.tenant_id, enabled_only=enabled_only)


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_revoke_key(
    key_id: str,
    ctx: RequestContext = Depends(require_tenant_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Revoke an API key. Requires ``tenant_admin`` role."""
    revoked = await revoke_api_key(db, ctx.tenant_id, key_id)
    if not revoked:
        raise HTTPException(status_code=404, detail=f"API key {key_id!r} not found")
