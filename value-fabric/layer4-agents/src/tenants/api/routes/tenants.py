"""Tenant management API routes (super_admin only).

POST   /v1/tenants               — create tenant
GET    /v1/tenants               — list tenants
GET    /v1/tenants/{tenant_id}   — get tenant
PATCH  /v1/tenants/{tenant_id}   — update tenant
DELETE /v1/tenants/{tenant_id}   — soft-delete tenant
"""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from shared.identity.dependencies import require_super_admin
from shared.identity.models import (
    TenantCreateRequest,
    TenantModel,
    TenantUpdateRequest,
)

from ...database import get_db
from ..service import (
    create_tenant,
    delete_tenant,
    get_tenant,
    list_tenants,
    update_tenant,
)

router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("", response_model=TenantModel, status_code=status.HTTP_201_CREATED)
async def api_create_tenant(
    request: TenantCreateRequest,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantModel:
    """Create a new tenant. Requires ``super_admin`` role."""
    return await create_tenant(db, request)


@router.get("", response_model=List[TenantModel])
async def api_list_tenants(
    tenant_status: Optional[str] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> List[TenantModel]:
    """List all tenants. Requires ``super_admin`` role."""
    return await list_tenants(db, status=tenant_status, limit=limit, offset=offset)


@router.get("/{tenant_id}", response_model=TenantModel)
async def api_get_tenant(
    tenant_id: UUID,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantModel:
    """Get a tenant by ID. Requires ``super_admin`` role."""
    tenant = await get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    return tenant


@router.patch("/{tenant_id}", response_model=TenantModel)
async def api_update_tenant(
    tenant_id: UUID,
    request: TenantUpdateRequest,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> TenantModel:
    """Update a tenant. Requires ``super_admin`` role."""
    tenant = await update_tenant(db, tenant_id, request)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    return tenant


@router.delete("/{tenant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def api_delete_tenant(
    tenant_id: UUID,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete a tenant. Requires ``super_admin`` role."""
    deleted = await delete_tenant(db, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
