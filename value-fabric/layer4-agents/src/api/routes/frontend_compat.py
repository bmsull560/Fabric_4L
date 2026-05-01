"""Frontend compatibility aliases for path mismatches.

These routes provide backward-compatible paths that the frontend expects,
mapping to canonical backend handlers.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from shared.identity.context import RequestContext
from shared.identity.dependencies import require_authenticated
from ....database import get_db_from_context
from ...models.tenant import Tenant
from ...service import get_tenant, update_tenant
from ...email_verification import EmailVerificationService
from ...provisioning import TenantProvisioningService, ProvisioningStatus
from ...tiers import get_tier_config

router = APIRouter(tags=["Frontend Compatibility"])


class TenantSettingsResponse(BaseModel):
    """Tenant settings response."""

    id: str
    name: str
    slug: str
    status: str
    tier_id: str
    settings: dict
    created_at: str


class TenantSettingsUpdate(BaseModel):
    """Update tenant settings."""

    settings: dict | None = None


class TenantSettingsUpdateResponse(BaseModel):
    """Tenant settings update response."""

    id: str
    name: str
    settings: dict
    updated_at: str


class RegisterTenantRequest(BaseModel):
    """Request to register a new tenant."""

    name: str
    slug: str
    admin_email: str
    tier_id: str = "free"
    organization_name: str | None = None
    phone: str | None = None


class RegisterTenantResponse(BaseModel):
    """Response from tenant registration."""

    message: str
    tenant_id: str
    verification_required: bool


@router.get("/tenant/settings", response_model=TenantSettingsResponse)
async def get_current_tenant_settings(
    db: AsyncSession = Depends(get_db_from_context),
    ctx: RequestContext = Depends(require_authenticated),
) -> TenantSettingsResponse:
    """Get settings for the current tenant (frontend compatibility alias)."""
    tenant = await get_tenant(db, ctx.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    settings = tenant.settings or {}
    tier_id = settings.get("tier_id", "free")

    return TenantSettingsResponse(
        id=str(tenant.id),
        name=tenant.name,
        slug=tenant.slug,
        status=tenant.status,
        tier_id=tier_id,
        settings=settings,
        created_at=tenant.created_at.isoformat() if tenant.created_at else "",
    )


@router.patch("/tenant/settings", response_model=TenantSettingsUpdateResponse)
async def update_current_tenant_settings(
    update: TenantSettingsUpdate,
    db: AsyncSession = Depends(get_db_from_context),
    ctx: RequestContext = Depends(require_authenticated),
) -> TenantSettingsUpdateResponse:
    """Update settings for the current tenant (frontend compatibility alias)."""
    tenant = await get_tenant(db, ctx.tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    current_settings = tenant.settings or {}
    if update.settings:
        allowed_fields = {"custom_branding", "notification_preferences", "webhook_url"}
        for key, value in update.settings.items():
            if key in allowed_fields:
                current_settings[key] = value
        tenant.settings = current_settings

    updated = await update_tenant(
        db,
        ctx.tenant_id,
        settings_update=current_settings,
    )
    if not updated:
        raise HTTPException(status_code=500, detail="Failed to update tenant settings")

    return TenantSettingsUpdateResponse(
        id=str(updated.id),
        name=updated.name,
        settings=updated.settings or {},
        updated_at=updated.updated_at.isoformat() if updated.updated_at else "",
    )


@router.post("/auth/register", status_code=202, response_model=RegisterTenantResponse)
async def register_tenant_frontend_alias(
    request: RegisterTenantRequest,
    db: AsyncSession = Depends(get_db_from_context),
) -> RegisterTenantResponse:
    """Register a new tenant (frontend compatibility alias for /v1/tenants/register)."""
    from ...service import get_tenant_by_slug, create_tenant
    from shared.identity.models import TenantCreateRequest, TenantStatus

    # Check slug uniqueness
    existing = await get_tenant_by_slug(db, request.slug)
    if existing:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    # Validate tier
    try:
        tier = get_tier_config(request.tier_id)
        if not tier.is_public:
            raise HTTPException(status_code=400, detail="Invalid tier selection")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid tier")

    # Create tenant
    create_request = TenantCreateRequest(
        name=request.name,
        slug=request.slug,
        settings={
            "isolation_tier": "shared",
            "admin_email": request.admin_email,
            "organization_name": request.organization_name,
            "phone": request.phone,
            "tier_id": request.tier_id,
            "registration_pending": True,
        },
    )

    tenant = await create_tenant(db, create_request)

    # Generate verification token
    email_service = EmailVerificationService()
    token = email_service.generate_token(UUID(tenant.id), request.admin_email)

    # Send verification email
    email_sent = await email_service.send_verification_email(
        request.admin_email,
        request.name,
        token,
    )

    if not email_sent:
        import logging

        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to send verification email to {request.admin_email}")

    return RegisterTenantResponse(
        message="Registration received. Check your email to verify.",
        tenant_id=tenant.id,
        verification_required=True,
    )
