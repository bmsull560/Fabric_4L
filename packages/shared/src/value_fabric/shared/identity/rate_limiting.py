"""Rate limiting configuration models and defaults."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from .permissions import Role


class RateLimitScope(str, Enum):
    """Scope at which rate limits are enforced."""

    TENANT = "tenant"
    USER = "user"
    API_KEY = "api_key"


class RateLimitConfig(BaseModel):
    """Rate limit configuration for a caller."""

    requests_per_minute: int = Field(..., ge=1, description="Requests allowed per minute")
    requests_per_hour: int | None = Field(None, ge=1, description="Optional hourly limit")
    burst_size: int = Field(..., ge=1, description="Burst allowance")
    scope: RateLimitScope = Field(default=RateLimitScope.TENANT, description="Limiting scope")


# Default rate limits per role.  super_admin and system are unlimited.
ROLE_DEFAULT_RATE_LIMITS: dict[Role, RateLimitConfig | None] = {
    Role.READ_ONLY: RateLimitConfig(
        requests_per_minute=30,
        burst_size=5,
        scope=RateLimitScope.TENANT,
    ),
    Role.ANALYST: RateLimitConfig(
        requests_per_minute=60,
        burst_size=10,
        scope=RateLimitScope.TENANT,
    ),
    Role.CONTENT_ADMIN: RateLimitConfig(
        requests_per_minute=120,
        burst_size=20,
        scope=RateLimitScope.TENANT,
    ),
    Role.TENANT_ADMIN: RateLimitConfig(
        requests_per_minute=300,
        burst_size=50,
        scope=RateLimitScope.TENANT,
    ),
    Role.SUPER_ADMIN: None,
    Role.SYSTEM: None,
}
