"""Tenant provisioning status and webhook endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.identity.context import RequestContext
from shared.identity.dependencies import get_request_context, require_super_admin

from ....database import get_db
from ...provisioning import (
    ProvisioningState,
    ProvisioningStatus,
    TenantProvisioningService,
    provision_tenant,
)
from ...service import get_tenant

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tenants/{tenant_id}/provisioning", tags=["Provisioning"])


class ProvisioningStatusResponse(BaseModel):
    """Response for provisioning status query."""

    tenant_id: str
    status: str
    current_step: str | None
    completed_steps: list[str]
    error: str | None
    retryable: bool
    started_at: str | None
    completed_at: str | None
    retry_count: int
    max_retries: int


class RetryProvisioningResponse(BaseModel):
    """Response from retry provisioning request."""

    message: str
    tenant_id: str
    status: str


class WebhookProvisioningRequest(BaseModel):
    """Request to trigger provisioning via webhook."""

    tenant_id: UUID
    webhook_token: str


class WebhookProvisioningResponse(BaseModel):
    """Response from webhook provisioning request."""

    message: str
    tenant_id: str
    status: str


@router.get("/status", response_model=ProvisioningStatusResponse)
async def get_provisioning_status(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(get_request_context),
) -> ProvisioningStatusResponse:
    """Get provisioning status for a tenant.

    Returns the current state of tenant provisioning including:
    - Overall status (pending, in_progress, completed, failed, etc.)
    - Current step being executed
    - List of completed steps
    - Error information if failed
    - Retry information
    """
    # Verify tenant exists
    tenant = await get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Check permissions - only tenant admin or super admin can view
    if str(context.tenant_id) != str(tenant_id) and not context.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Create provisioning service to get state
    service = TenantProvisioningService(db)

    # Try to get current state by attempting to provision
    # This will return completed state if already done
    state = await service.provision_tenant(tenant_id)

    return ProvisioningStatusResponse(
        tenant_id=str(tenant_id),
        status=state.status.value,
        current_step=state.current_step.name if state.current_step else None,
        completed_steps=[s.name for s in state.completed_steps],
        error=state.error,
        retryable=state.retryable,
        started_at=state.started_at.isoformat() if state.started_at else None,
        completed_at=state.completed_at.isoformat() if state.completed_at else None,
        retry_count=state.retry_count,
        max_retries=state.max_retries,
    )


@router.post("/retry", response_model=RetryProvisioningResponse)
async def retry_provisioning(
    tenant_id: UUID,
    db: AsyncSession = Depends(get_db),
    context: RequestContext = Depends(require_super_admin),
) -> RetryProvisioningResponse:
    """Retry failed provisioning for a tenant (super admin only).

    This endpoint allows super admins to manually retry provisioning
    for tenants that failed and are marked as retryable.
    """
    # Verify tenant exists
    tenant = await get_tenant(db, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Retry provisioning with force flag
    service = TenantProvisioningService(db)
    state = await service.provision_tenant(tenant_id, force_retry=True)

    if state.status == ProvisioningStatus.COMPLETED:
        return RetryProvisioningResponse(
            message="Provisioning completed successfully",
            tenant_id=str(tenant_id),
            status=state.status.value,
        )
    elif state.status == ProvisioningStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Provisioning retry failed",
                "error": state.error,
                "retryable": state.retryable,
            },
        )
    else:
        return RetryProvisioningResponse(
            message="Provisioning in progress",
            tenant_id=str(tenant_id),
            status=state.status.value,
        )


@router.post(
    "/webhook",
    response_model=WebhookProvisioningResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def webhook_provisioning(
    request: WebhookProvisioningRequest,
    db: AsyncSession = Depends(get_db),
) -> WebhookProvisioningResponse:
    """Trigger provisioning via webhook (external systems).

    This endpoint allows external systems to trigger tenant provisioning
    via a webhook call. Requires a valid webhook token for authentication.

    The webhook token should be configured in environment variables:
    PROVISIONING_WEBHOOK_TOKEN
    """
    import os

    # Verify webhook token
    expected_token = os.getenv("PROVISIONING_WEBHOOK_TOKEN", "")
    if not expected_token:
        logger.error("PROVISIONING_WEBHOOK_TOKEN not configured")
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Webhook provisioning not configured",
        )

    if request.webhook_token != expected_token:
        logger.warning("Invalid webhook token received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook token",
        )

    # Verify tenant exists
    tenant = await get_tenant(db, request.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Trigger provisioning asynchronously
    # In production, this should be queued to a background task (Celery)
    # For now, we return immediately and provisioning happens in background
    state = await provision_tenant(db, request.tenant_id)

    if state.status == ProvisioningStatus.COMPLETED:
        return WebhookProvisioningResponse(
            message="Provisioning completed",
            tenant_id=str(request.tenant_id),
            status=state.status.value,
        )
    elif state.status == ProvisioningStatus.FAILED:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "Provisioning failed",
                "error": state.error,
                "retryable": state.retryable,
            },
        )
    else:
        return WebhookProvisioningResponse(
            message="Provisioning initiated",
            tenant_id=str(request.tenant_id),
            status=state.status.value,
        )
