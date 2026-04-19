"""
Integrations Management API Routes.

Provides CRUD operations for CRM provider configurations (Salesforce, HubSpot).
All credentials are encrypted at rest and never returned in API responses.
"""

import logging
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from shared.audit import AuditAction, AuditOutcome, emit_audit_event
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ...models.account import CRMProvider
from ...services.integration_service import (
    IntegrationNotFoundError,
    IntegrationService,
    IntegrationValidationError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/integrations", tags=["Integrations"])

# -----------------------------------------------------------------------------
# Request / Response Schemas
# -----------------------------------------------------------------------------


class IntegrationConfig(BaseModel):
    """Integration configuration (no credentials - for responses)."""

    provider: str = Field(..., description="CRM provider: salesforce or hubspot")
    enabled: bool = Field(False, description="Whether integration is active")
    instance_url: str | None = Field(None, description="CRM instance URL")
    sync_interval_minutes: int = Field(60, ge=5, le=1440)
    sync_batch_size: int = Field(100, ge=10, le=500)


class IntegrationStatusResponse(IntegrationConfig):
    """Integration with sync status (response only)."""

    id: str = Field(..., description="Integration UUID")
    tenant_id: str = Field(..., description="Tenant identifier")
    last_sync_at: str | None = None
    last_successful_sync_at: str | None = None
    records_synced: int = 0
    records_updated: int = 0
    records_failed: int = 0
    status: str = "idle"
    last_error_message: str | None = None
    created_at: str
    updated_at: str


class IntegrationCreateRequest(BaseModel):
    """Request to create/update an integration."""

    enabled: bool = Field(False, description="Whether to enable the integration")
    api_key: str = Field(..., description="API key/token for the CRM")
    api_secret: str | None = Field(None, description="API secret (if required)")
    instance_url: str | None = Field(None, description="CRM instance URL")
    sync_interval_minutes: int = Field(60)
    sync_batch_size: int = Field(100)

    @field_validator("sync_interval_minutes")
    @classmethod
    def validate_interval(cls, v: int) -> int:
        if not 5 <= v <= 1440:
            raise ValueError("sync_interval_minutes must be between 5 and 1440")
        return v

    @field_validator("sync_batch_size")
    @classmethod
    def validate_batch_size(cls, v: int) -> int:
        if not 10 <= v <= 500:
            raise ValueError("sync_batch_size must be between 10 and 500")
        return v


class IntegrationListResponse(BaseModel):
    """List of integrations response."""

    integrations: list[IntegrationStatusResponse]


class ConnectionTestResponse(BaseModel):
    """Connection test result."""

    success: bool
    message: str
    details: dict[str, Any] | None = None
    error_code: str | None = None


class SyncTriggerResponse(BaseModel):
    """Manual sync trigger response."""

    sync_id: str
    status: str
    provider: str


# -----------------------------------------------------------------------------
# Dependencies
# -----------------------------------------------------------------------------


async def get_tenant_id(x_tenant_id: str = Header(..., alias="X-Tenant-ID")) -> str:
    """Extract tenant ID from request header."""
    if not x_tenant_id or not x_tenant_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Tenant-ID header is required",
        )
    return x_tenant_id


def get_integration_service(db: AsyncSession = Depends(get_db)) -> IntegrationService:
    """Dependency for integration service."""
    return IntegrationService(db)


# -----------------------------------------------------------------------------
# Routes
# -----------------------------------------------------------------------------


@router.get("", response_model=IntegrationListResponse)
async def list_integrations(
    tenant_id: str = Depends(get_tenant_id),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationListResponse:
    """List all configured integrations for the tenant.

    Returns integrations without credentials (encrypted at rest).
    """
    integrations = await service.list_integrations(tenant_id)

    return IntegrationListResponse(
        integrations=[
            IntegrationStatusResponse(**integration.to_dict())
            for integration in integrations
        ]
    )


@router.get("/{provider}", response_model=IntegrationStatusResponse)
async def get_integration(
    provider: CRMProvider,
    tenant_id: str = Depends(get_tenant_id),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationStatusResponse:
    """Get a specific integration configuration.

    Args:
        provider: CRM provider (salesforce or hubspot)
    """
    integration = await service.get_integration(tenant_id, provider)

    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {provider.value} integration configured",
        )

    return IntegrationStatusResponse(**integration.to_dict())


@router.post("/{provider}", response_model=IntegrationStatusResponse)
async def create_or_update_integration(
    provider: CRMProvider,
    request: IntegrationCreateRequest,
    tenant_id: str = Depends(get_tenant_id),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    service: IntegrationService = Depends(get_integration_service),
) -> IntegrationStatusResponse:
    """Create or update an integration configuration.

    Args:
        provider: CRM provider (salesforce or hubspot)
        request: Integration configuration with credentials

    Notes:
        - Credentials are encrypted at rest using AES-256
        - Credentials are never returned in API responses
        - Audit logged for all changes
    """
    # Build credentials dict
    credentials: dict[str, str] = {"api_key": request.api_key}
    if request.api_secret:
        credentials["api_secret"] = request.api_secret
    if request.instance_url:
        credentials["instance_url"] = request.instance_url

    try:
        integration, is_created = await service.create_or_update_integration(
            tenant_id=tenant_id,
            provider=provider,
            enabled=request.enabled,
            credentials=credentials,
            instance_url=request.instance_url,
            sync_interval_minutes=request.sync_interval_minutes,
            sync_batch_size=request.sync_batch_size,
            user_id=x_user_id,
        )

        # Emit audit event (best-effort, log failure but don't fail request)
        try:
            await emit_audit_event(
                action=AuditAction.CREATE if is_created else AuditAction.UPDATE,
                resource_type="integration",
                resource_id=str(integration.id),
                tenant_id=tenant_id,
                user_id=x_user_id,
                outcome=AuditOutcome.SUCCESS,
                details={"provider": provider.value, "enabled": request.enabled, "is_created": is_created},
            )
        except Exception as audit_error:
            logger.error(
                "Audit event failed for integration %s: %s",
                integration.id,
                audit_error,
                exc_info=True,
            )

        return IntegrationStatusResponse(**integration.to_dict())

    except IntegrationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_integration(
    provider: CRMProvider,
    tenant_id: str = Depends(get_tenant_id),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    service: IntegrationService = Depends(get_integration_service),
) -> None:
    """Delete an integration configuration.

    Args:
        provider: CRM provider (salesforce or hubspot)
    """
    deleted = await service.delete_integration(tenant_id, provider, user_id=x_user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No {provider.value} integration found",
        )

    # Emit audit event (best-effort, log failure but don't fail request)
    try:
        await emit_audit_event(
            action=AuditAction.DELETE,
            resource_type="integration",
            resource_id=f"{tenant_id}:{provider.value}",
            tenant_id=tenant_id,
            user_id=x_user_id,
            outcome=AuditOutcome.SUCCESS,
            details={"provider": provider.value},
        )
    except Exception as audit_error:
        logger.error(
            "Audit event failed for deleted integration %s:%s: %s",
            tenant_id,
            provider.value,
            audit_error,
            exc_info=True,
        )


@router.post("/{provider}/test", response_model=ConnectionTestResponse)
async def test_integration_connection(
    provider: CRMProvider,
    tenant_id: str = Depends(get_tenant_id),
    service: IntegrationService = Depends(get_integration_service),
) -> ConnectionTestResponse:
    """Test the connection to a CRM provider.

    Uses stored credentials to verify connectivity.
    """
    result = await service.test_connection(tenant_id, provider)
    return ConnectionTestResponse(**result)


@router.post("/{provider}/sync", response_model=SyncTriggerResponse)
async def trigger_sync(
    provider: CRMProvider,
    tenant_id: str = Depends(get_tenant_id),
    x_user_id: str | None = Header(None, alias="X-User-ID"),
    service: IntegrationService = Depends(get_integration_service),
) -> SyncTriggerResponse:
    """Trigger a manual sync for an integration.

    Args:
        provider: CRM provider (salesforce or hubspot)
    """
    try:
        result = await service.trigger_sync(tenant_id, provider, user_id=x_user_id)

        # Emit audit event (best-effort, log failure but don't fail request)
        try:
            await emit_audit_event(
                action=AuditAction.CREATE,
                resource_type="sync_job",
                resource_id=result["sync_id"],
                tenant_id=tenant_id,
                user_id=x_user_id,
                outcome=AuditOutcome.SUCCESS,
                details={"provider": provider.value, "sync_id": result["sync_id"]},
            )
        except Exception as audit_error:
            logger.error(
                "Audit event failed for sync job %s: %s",
                result["sync_id"],
                audit_error,
                exc_info=True,
            )

        return SyncTriggerResponse(**result)

    except IntegrationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except IntegrationValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
