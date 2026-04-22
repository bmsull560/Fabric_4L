"""Pydantic models for identity entities."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TenantStatus(str, Enum):
    """Tenant lifecycle status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    PENDING = "pending"
    DELETED = "deleted"


class IsolationTier(str, Enum):
    """Tenant data isolation tier (Task 4.1).

    - SHARED: Shared schema with RLS (current)
    - SCHEMA: Dedicated schema per tenant (future)
    - DATABASE: Dedicated database per tenant (future)
    """

    SHARED = "shared"
    SCHEMA = "schema"
    DATABASE = "database"


class UserStatus(str, Enum):
    """User lifecycle status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    SUSPENDED = "suspended"


class Role(str, Enum):
    """User roles in the system."""

    SUPER_ADMIN = "super_admin"
    TENANT_ADMIN = "tenant_admin"
    USER = "user"
    READONLY = "readonly"


class TenantCreateRequest(BaseModel):
    """Request to create a new tenant."""

    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    metadata: dict[str, Any] | None = None


class TenantUpdateRequest(BaseModel):
    """Request to update a tenant."""

    name: str | None = Field(None, min_length=1, max_length=255)
    status: TenantStatus | None = None
    metadata: dict[str, Any] | None = None


class TenantSettings(BaseModel):
    """Tenant settings schema with isolation tier support."""

    isolation_tier: IsolationTier = Field(
        default=IsolationTier.SHARED,
        description="Data isolation tier: shared (RLS), schema (dedicated), or database (dedicated)",
    )
    rate_limits: dict[str, Any] | None = None
    feature_flags: dict[str, Any] | None = None


class TenantModel(BaseModel):
    """Tenant representation."""

    id: UUID
    name: str
    slug: str
    status: TenantStatus
    isolation_tier: IsolationTier = Field(
        default=IsolationTier.SHARED,
        description="Current data isolation tier for this tenant",
    )
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None
    settings: TenantSettings = Field(default_factory=TenantSettings)

    class Config:
        from_attributes = True


class UserInviteRequest(BaseModel):
    """Request to invite a user."""

    email: str
    role: Role = Role.USER
    metadata: dict[str, Any] | None = None


class UserUpdateRequest(BaseModel):
    """Request to update a user."""

    email: str | None = None
    role: Role | None = None
    status: UserStatus | None = None
    metadata: dict[str, Any] | None = None


class UserModel(BaseModel):
    """User representation."""

    id: UUID
    email: str
    tenant_id: UUID
    role: Role
    status: UserStatus
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] | None = None

    class Config:
        from_attributes = True


class APIKeyCreateRequest(BaseModel):
    """Request to create an API key."""

    name: str = Field(..., min_length=1, max_length=255)
    permissions: list[str] | None = None
    expires_at: datetime | None = None


class APIKeyCreateResponse(BaseModel):
    """Response with the new API key (only shown once)."""

    id: UUID
    name: str
    key: str  # The actual API key - only shown once
    permissions: list[str]
    created_at: datetime
    expires_at: datetime | None = None


class APIKeyModel(BaseModel):
    """API key representation (without the actual key)."""

    id: UUID
    name: str
    tenant_id: UUID
    permissions: list[str]
    created_at: datetime
    expires_at: datetime | None = None
    last_used_at: datetime | None = None

    class Config:
        from_attributes = True
