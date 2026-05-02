"""Typed validation layer for tenant settings JSONB (Task 84).

Prevents JSON drift by providing Pydantic models for structured access
to tenant configuration data.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class RateLimitSettings(BaseModel):
    """Rate limit configuration per tenant.

    Example JSONB structure:
    {
        "rate_limits": {
            "requests_per_minute": 120,
            "burst": 240,
            "llm_requests_per_minute": 30
        }
    }
    """

    requests_per_minute: int = Field(
        default=120,
        ge=1,
        le=10000,
        description="Default requests per minute limit",
    )
    burst: int = Field(
        default=240,
        ge=1,
        le=50000,
        description="Burst capacity for token bucket",
    )
    llm_requests_per_minute: int = Field(
        default=30,
        ge=1,
        le=1000,
        description="LLM-specific requests per minute limit",
    )

    @field_validator("burst")
    @classmethod
    def burst_must_be_greater_than_rpm(cls, v: int, info) -> int:
        """Ensure burst >= requests_per_minute."""
        data = info.data
        if "requests_per_minute" in data and v < data["requests_per_minute"]:
            raise ValueError("burst must be >= requests_per_minute")
        return v


class TenantSettings(BaseModel):
    """Complete tenant settings schema with validation.

    Provides type-safe access to tenant.settings JSONB column.
    """

    rate_limits: RateLimitSettings = Field(
        default_factory=RateLimitSettings,
        description="Rate limiting configuration",
    )

    # Future settings can be added here with their own typed schemas
    # feature_flags: dict[str, bool] = Field(default_factory=dict)
    # billing: BillingSettings = Field(default_factory=BillingSettings)

    @classmethod
    def from_json(cls, data: dict | None) -> "TenantSettings":
        """Parse tenant settings from JSONB dict.

        Args:
            data: Raw JSONB dict from database (may be None)

        Returns:
            Validated TenantSettings instance
        """
        if data is None:
            return cls()
        return cls.model_validate(data)

    def to_json(self) -> dict:
        """Serialize to JSONB-compatible dict.

        Returns:
            Dict suitable for storing in tenant.settings
        """
        return self.model_dump()


def get_tenant_rate_limits(settings: dict | None) -> RateLimitSettings:
    """Extract and validate rate limits from tenant settings.

    Convenience function for middleware and services.

    Args:
        settings: Raw tenant.settings JSONB dict

    Returns:
        Validated RateLimitSettings with defaults
    """
    tenant_settings = TenantSettings.from_json(settings)
    return tenant_settings.rate_limits
