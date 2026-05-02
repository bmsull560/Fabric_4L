"""Tenant management API routes (super_admin only).

POST   /v1/tenants                          — create tenant
GET    /v1/tenants                          — list tenants
GET    /v1/tenants/{tenant_id}              — get tenant
PATCH  /v1/tenants/{tenant_id}              — update tenant
DELETE /v1/tenants/{tenant_id}              — soft-delete tenant
POST   /v1/tenants/{tenant_id}/suspend      — suspend tenant
POST   /v1/tenants/{tenant_id}/activate     — activate tenant
POST   /v1/tenants/{tenant_id}/status       — change status with reason
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from shared.identity.dependencies import require_super_admin
from shared.identity.models import (
    TenantCreateRequest,
    TenantModel,
    TenantUpdateRequest,
)
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_db_from_context
from ...service import (
    create_tenant,
    delete_tenant,
    get_tenant,
    list_tenants,
    update_tenant,
    update_tenant_status,
)


class StatusChangeRequest(BaseModel):
    """Request body for tenant status change endpoints."""
    reason: str | None = Field(None, description="Human-readable reason for the status change")
    changed_by: str | None = Field(None, description="User ID or service name initiating the change")


router = APIRouter(prefix="/tenants", tags=["Tenants"])


@router.post("", response_model=TenantModel, status_code=status.HTTP_201_CREATED)
async def api_create_tenant(
    request: TenantCreateRequest,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_from_context),
) -> TenantModel:
    """Create a new tenant. Requires ``super_admin`` role."""
    return await create_tenant(db, request)


@router.get("", response_model=list[TenantModel])
async def api_list_tenants(
    tenant_status: str | None = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_from_context),
) -> list[TenantModel]:
    """List all tenants. Requires ``super_admin`` role."""
    return await list_tenants(db, status=tenant_status, limit=limit, offset=offset)


@router.get("/{tenant_id}", response_model=TenantModel)
async def api_get_tenant(
    tenant_id: UUID,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_from_context),
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
    db: AsyncSession = Depends(get_db_from_context),
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
    db: AsyncSession = Depends(get_db_from_context),
) -> None:
    """Soft-delete a tenant. Requires ``super_admin`` role."""
    deleted = await delete_tenant(db, tenant_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")


# ---------------------------------------------------------------------------
# Lifecycle endpoints (Phase 1, Task 1.7)
# ---------------------------------------------------------------------------


@router.post("/{tenant_id}/suspend", response_model=TenantModel)
async def api_suspend_tenant(
    tenant_id: UUID,
    body: StatusChangeRequest | None = None,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_from_context),
) -> TenantModel:
    """Suspend a tenant (active -> suspended). Requires ``super_admin`` role."""
    reason = body.reason if body else None
    changed_by = body.changed_by if body else None
    try:
        updated = await update_tenant_status(
            db, tenant_id, "suspended", reason=reason, changed_by=changed_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    tenant = await get_tenant(db, tenant_id)
    return tenant


@router.post("/{tenant_id}/activate", response_model=TenantModel)
async def api_activate_tenant(
    tenant_id: UUID,
    body: StatusChangeRequest | None = None,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_from_context),
) -> TenantModel:
    """Activate a tenant (pending/suspended -> active). Requires ``super_admin`` role."""
    reason = body.reason if body else None
    changed_by = body.changed_by if body else None
    try:
        updated = await update_tenant_status(
            db, tenant_id, "active", reason=reason, changed_by=changed_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    tenant = await get_tenant(db, tenant_id)
    return tenant


@router.post("/{tenant_id}/status", response_model=TenantModel)
async def api_change_tenant_status(
    tenant_id: UUID,
    target_status: str = Query(..., description="Target status: active, suspended, deleted"),
    body: StatusChangeRequest | None = None,
    _ctx=Depends(require_super_admin),
    db: AsyncSession = Depends(get_db_from_context),
) -> TenantModel:
    """Change tenant status with reason and audit trail. Requires ``super_admin`` role."""
    reason = body.reason if body else None
    changed_by = body.changed_by if body else None
    try:
        updated = await update_tenant_status(
            db, tenant_id, target_status, reason=reason, changed_by=changed_by,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    if not updated:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    tenant = await get_tenant(db, tenant_id)
    return tenant
