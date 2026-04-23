"""
Admin API for tenant rate limit quota management (Task 5).

Provides endpoints for:
- Viewing tenant quotas and usage
- Setting custom limits
- Resetting rate limits
- Monitoring and alerting
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from shared.identity.context import RequestContext
from shared.identity.dependencies import require_privileged_access
from .tenant_rate_limiter import (
    TenantRateLimiter,
    TenantTier,
    RateLimitConfig,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/admin/rate-limits", tags=["Admin - Rate Limits"])


# ═══════════════════════════════════════════════════════════════════════════
# Request/Response Models
# ═══════════════════════════════════════════════════════════════════════════

class RateLimitConfigRequest(BaseModel):
    """Request to set custom rate limit."""
    
    requests_per_minute: int = Field(..., gt=0, description="Requests per minute")
    requests_per_hour: int = Field(..., gt=0, description="Requests per hour")
    requests_per_day: int = Field(..., gt=0, description="Requests per day")
    burst_allowance: int = Field(0, ge=0, description="Burst allowance")
    
    class Config:
        json_schema_extra = {
            "example": {
                "requests_per_minute": 1000,
                "requests_per_hour": 50000,
                "requests_per_day": 1000000,
                "burst_allowance": 200,
            }
        }


class TenantQuotaResponse(BaseModel):
    """Response with tenant quota status."""
    
    tenant_id: str
    tier: str
    limits: dict
    usage: dict
    custom_limits: bool


class TenantUsageResponse(BaseModel):
    """Response with tenant usage statistics."""
    
    tenant_id: str
    timestamp: str
    windows: dict


# ═══════════════════════════════════════════════════════════════════════════
# Dependency Injection
# ═══════════════════════════════════════════════════════════════════════════

async def get_rate_limiter() -> TenantRateLimiter:
    """Get rate limiter instance (injected by app)."""
    # This should be injected via app.state or dependency override
    raise NotImplementedError("Rate limiter must be injected via dependency override")


# ═══════════════════════════════════════════════════════════════════════════
# Endpoints
# ═══════════════════════════════════════════════════════════════════════════

@router.get(
    "/tenants/{tenant_id}/quota",
    response_model=TenantQuotaResponse,
    summary="Get tenant quota status",
    description="""
    Get current quota status for a tenant including:
    - Rate limits (per minute/hour/day)
    - Current usage across all windows
    - Whether custom limits are applied
    
    **Requires:** super_admin role
    """,
)
async def get_tenant_quota(
    tenant_id: UUID,
    context: RequestContext = Depends(require_privileged_access()),
    rate_limiter: TenantRateLimiter = Depends(get_rate_limiter),
) -> TenantQuotaResponse:
    """Get quota status for tenant.
    
    Args:
        tenant_id: Tenant UUID
        context: Request context (super-admin required)
        rate_limiter: Rate limiter instance
        
    Returns:
        TenantQuotaResponse with quota and usage
    """
    try:
        # Determine tenant tier (would come from database in production)
        tenant_tier = TenantTier.SHARED  # TODO: Query from database
        
        status_data = await rate_limiter.get_tenant_quota_status(
            tenant_id=tenant_id,
            tenant_tier=tenant_tier,
        )
        
        return TenantQuotaResponse(**status_data)
        
    except Exception as e:
        logger.error(f"Failed to get tenant quota: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve quota status: {str(e)}",
        )


@router.get(
    "/tenants/{tenant_id}/usage",
    response_model=TenantUsageResponse,
    summary="Get tenant usage statistics",
    description="""
    Get current usage statistics for a tenant across all rate limit windows.
    
    **Requires:** super_admin role
    """,
)
async def get_tenant_usage(
    tenant_id: UUID,
    endpoint: str | None = None,
    context: RequestContext = Depends(require_privileged_access()),
    rate_limiter: TenantRateLimiter = Depends(get_rate_limiter),
) -> TenantUsageResponse:
    """Get usage statistics for tenant.
    
    Args:
        tenant_id: Tenant UUID
        endpoint: Optional endpoint filter
        context: Request context (super-admin required)
        rate_limiter: Rate limiter instance
        
    Returns:
        TenantUsageResponse with usage data
    """
    try:
        usage_data = await rate_limiter.get_tenant_usage(
            tenant_id=tenant_id,
            endpoint=endpoint,
        )
        
        return TenantUsageResponse(**usage_data)
        
    except Exception as e:
        logger.error(f"Failed to get tenant usage: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve usage statistics: {str(e)}",
        )


@router.put(
    "/tenants/{tenant_id}/limits",
    status_code=status.HTTP_200_OK,
    summary="Set custom rate limits",
    description="""
    Set custom rate limits for a specific tenant.
    Overrides tier-based defaults.
    
    **Requires:** super_admin role + X-Privileged-Reason header
    """,
)
async def set_custom_limits(
    tenant_id: UUID,
    config: RateLimitConfigRequest,
    context: RequestContext = Depends(require_privileged_access()),
    rate_limiter: TenantRateLimiter = Depends(get_rate_limiter),
) -> dict:
    """Set custom rate limits for tenant.
    
    Args:
        tenant_id: Tenant UUID
        config: Custom rate limit configuration
        context: Request context (super-admin required)
        rate_limiter: Rate limiter instance
        
    Returns:
        Success message
    """
    try:
        rate_limit_config = RateLimitConfig(
            requests_per_minute=config.requests_per_minute,
            requests_per_hour=config.requests_per_hour,
            requests_per_day=config.requests_per_day,
            burst_allowance=config.burst_allowance,
        )
        
        await rate_limiter.set_custom_limit(
            tenant_id=tenant_id,
            config=rate_limit_config,
        )
        
        logger.info(
            f"Super-admin {context.user_id} set custom rate limits for tenant {tenant_id}"
        )
        
        return {
            "message": f"Custom rate limits set for tenant {tenant_id}",
            "limits": {
                "requests_per_minute": config.requests_per_minute,
                "requests_per_hour": config.requests_per_hour,
                "requests_per_day": config.requests_per_day,
                "burst_allowance": config.burst_allowance,
            },
        }
        
    except Exception as e:
        logger.error(f"Failed to set custom limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set custom limits: {str(e)}",
        )


@router.post(
    "/tenants/{tenant_id}/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset tenant rate limits",
    description="""
    Reset all rate limit counters for a tenant.
    Use with caution - this clears all usage tracking.
    
    **Requires:** super_admin role + X-Privileged-Reason header
    """,
)
async def reset_tenant_limits(
    tenant_id: UUID,
    context: RequestContext = Depends(require_privileged_access()),
    rate_limiter: TenantRateLimiter = Depends(get_rate_limiter),
) -> dict:
    """Reset rate limits for tenant.
    
    Args:
        tenant_id: Tenant UUID
        context: Request context (super-admin required)
        rate_limiter: Rate limiter instance
        
    Returns:
        Number of keys deleted
    """
    try:
        deleted_count = await rate_limiter.reset_tenant_limits(tenant_id)
        
        logger.warning(
            f"Super-admin {context.user_id} reset rate limits for tenant {tenant_id} "
            f"({deleted_count} keys deleted)"
        )
        
        return {
            "message": f"Rate limits reset for tenant {tenant_id}",
            "keys_deleted": deleted_count,
        }
        
    except Exception as e:
        logger.error(f"Failed to reset tenant limits: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset rate limits: {str(e)}",
        )


@router.get(
    "/tiers",
    summary="List rate limit tiers",
    description="""
    List all available rate limit tiers with their default quotas.
    
    **Requires:** super_admin role
    """,
)
async def list_rate_limit_tiers(
    context: RequestContext = Depends(require_privileged_access()),
) -> dict:
    """List rate limit tiers and their quotas.
    
    Args:
        context: Request context (super-admin required)
        
    Returns:
        Dictionary of tiers and their limits
    """
    from .tenant_rate_limiter import DEFAULT_TENANT_LIMITS
    
    tiers = {}
    for tier, config in DEFAULT_TENANT_LIMITS.items():
        tiers[tier.value] = {
            "requests_per_minute": config.requests_per_minute,
            "requests_per_hour": config.requests_per_hour,
            "requests_per_day": config.requests_per_day,
            "burst_allowance": config.burst_allowance,
        }
    
    return {"tiers": tiers}
