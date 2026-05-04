"""
Admin tools with strict permission enforcement.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from value_fabric.shared.audit import AuditAction, AuditOutcome, emit_audit_event
from value_fabric.shared.identity.context import RequestContext
from value_fabric.shared.models.typed_dict import TypedDictModel

from ..tenants.service import update_tenant_status


class suspend_tenantResult(TypedDictModel):
    success: bool
    tenant_id: Any
    status: str


logger = logging.getLogger(__name__)


def _has_admin_permission(context: RequestContext) -> bool:
    """Accept explicit admin roles or broad admin-style permissions."""
    admin_roles = {"super_admin", "tenant_admin", "admin"}
    if any(role in admin_roles for role in (context.roles or [])):
        return True

    permissions = {
        getattr(permission, "value", str(permission))
        for permission in (context.permissions or frozenset())
    }
    return bool(permissions.intersection({"all", "admin", "admin:tenants", "tenant.admin"}))


async def suspend_tenant(
    tenant_id: UUID,
    context: RequestContext | None = None,
    db: AsyncSession | None = None,
    reason: str | None = None,
) -> dict[str, str | bool]:
    """Suspend tenant (admin only) via the tenant lifecycle service.

    Args:
        tenant_id: Tenant UUID to suspend.
        context: Request context (required for permission check).
        db: Async SQLAlchemy session used to persist the lifecycle transition.
        reason: Optional audit/lifecycle reason for the suspension.

    Raises:
        HTTPException: If permission is missing, persistence is unavailable,
            tenant is missing, or the lifecycle transition is invalid.

    Returns:
        Dict with success flag on success.
    """
    if not context or not _has_admin_permission(context):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required",
        )

    if db is None:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Tenant suspension requires a database session and cannot be completed as a dry-run tool.",
        )

    admin_id = str(context.user_id or "unknown")
    suspension_reason = reason or "Suspended by administrator"

    try:
        updated = await update_tenant_status(
            db,
            tenant_id,
            "suspended",
            reason=suspension_reason,
            changed_by=admin_id,
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tenant {tenant_id} not found",
            )
        await db.commit()
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc

    emit_audit_event(
        AuditAction.TENANT_SUSPENDED,
        tenant_id=tenant_id,
        user_id=admin_id,
        resource_type="Tenant",
        resource_id=str(tenant_id),
        request_id=getattr(context, "request_id", None),
        outcome=AuditOutcome.SUCCESS,
        details={"reason": suspension_reason},
    )

    logger.info("Tenant %s suspended by admin %s", tenant_id, admin_id)
    return suspend_tenantResult.model_validate(
        {"success": True, "tenant_id": str(tenant_id), "status": "suspended"}
    )
