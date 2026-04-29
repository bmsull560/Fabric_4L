"""Request context for identity and tenant information."""

from __future__ import annotations

import contextvars
from dataclasses import dataclass, field
from typing import Any, ClassVar
from uuid import UUID

# Context variable for async-safe context storage
_current_context: contextvars.ContextVar[RequestContext | None] = contextvars.ContextVar(
    "request_context", default=None
)

# P1: Tenant isolation tier constants
ISOLATION_TIER_SHARED = "shared"
ISOLATION_TIER_SCHEMA = "schema"
ISOLATION_TIER_DATABASE = "database"
VALID_ISOLATION_TIERS = {ISOLATION_TIER_SHARED, ISOLATION_TIER_SCHEMA, ISOLATION_TIER_DATABASE}

# Auth source constants
AUTH_SOURCE_JWT = "jwt_claim"
AUTH_SOURCE_API_KEY = "api_key"
AUTH_SOURCE_SERVICE_ACCOUNT = "service_account"
AUTH_SOURCE_UNKNOWN = "unknown"


@dataclass
class RequestContext:
    """Context for the current request including tenant and user info.

    Multi-tenancy fields:
    - tenant_id: Primary tenant identifier for RLS enforcement
    - org_id: Optional organization hierarchy (enterprise feature)
    - tenant_role: User's role within the tenant context
    - isolation_tier: Tenant's data isolation level (shared/schema/database)
    - auth_source: How the tenant context was resolved (jwt_claim|api_key|service_account)

    Service account fields (for programmatic access):
    - service_account_id: Service account identifier
    - service_account_scopes: Granted scopes for service account
    """

    # Core identity
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    api_key_id: UUID | None = None
    roles: list[str] | None = None
    permissions: list[str] | None = None
    request_id: str | None = None

    # Extended tenant context (Task 1.1)
    org_id: UUID | None = None
    tenant_role: str | None = None
    isolation_tier: str = ISOLATION_TIER_SHARED
    auth_source: str = AUTH_SOURCE_UNKNOWN

    # Service account support (Task 1.3)
    service_account_id: UUID | None = None
    service_account_scopes: list[str] = field(default_factory=list)
    
    # Task 2: Multi-Tenancy Hardening - Super-admin bypass tracking
    accessed_tenant_ids: set[str] = field(default_factory=set)
    privileged_session_start: float | None = None  # Unix timestamp

    # P1: Class-level validation
    _valid_isolation_tiers: ClassVar[set[str]] = VALID_ISOLATION_TIERS
    _valid_auth_sources: ClassVar[set[str]] = {
        AUTH_SOURCE_JWT, AUTH_SOURCE_API_KEY, AUTH_SOURCE_SERVICE_ACCOUNT, AUTH_SOURCE_UNKNOWN
    }

    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission."""
        if not self.permissions:
            return False
        return permission in self.permissions

    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        if not self.roles:
            return False
        return "super_admin" in self.roles

    def is_tenant_admin(self) -> bool:
        """Check if user is tenant admin."""
        if not self.roles:
            return False
        return "tenant_admin" in self.roles or "super_admin" in self.roles

    def is_service_account(self) -> bool:
        """Check if context represents a service account."""
        return self.service_account_id is not None

    def is_isolation_tier_valid(self) -> bool:
        """Check if isolation_tier is a valid value."""
        return self.isolation_tier in self._valid_isolation_tiers

    def is_auth_source_valid(self) -> bool:
        """Check if auth_source is a valid value."""
        return self.auth_source in self._valid_auth_sources

    def validate(self) -> list[str]:
        """Validate context state and return list of validation errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.is_isolation_tier_valid():
            errors.append(f"Invalid isolation_tier: {self.isolation_tier}")
        
        if not self.is_auth_source_valid():
            errors.append(f"Invalid auth_source: {self.auth_source}")
        
        # Validate service account consistency
        if self.service_account_id and not self.service_account_scopes:
            errors.append("Service account must have scopes")
        
        return errors

    @staticmethod
    def _uuid_to_str(uuid_val: UUID | None) -> str | None:
        """P2: Helper to serialize UUID to string."""
        return str(uuid_val) if uuid_val else None

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "tenant_id": self._uuid_to_str(self.tenant_id),
            "user_id": self._uuid_to_str(self.user_id),
            "api_key_id": self._uuid_to_str(self.api_key_id),
            "roles": self.roles,
            "permissions": self.permissions,
            "request_id": self.request_id,
            "org_id": self._uuid_to_str(self.org_id),
            "tenant_role": self.tenant_role,
            "isolation_tier": self.isolation_tier,
            "auth_source": self.auth_source,
            "service_account_id": self._uuid_to_str(self.service_account_id),
            "service_account_scopes": self.service_account_scopes,
        }


# ═══════════════════════════════════════════════════════════════════════════
# Context Management Functions
# ═══════════════════════════════════════════════════════════════════════════


def get_current_context() -> RequestContext | None:
    """Get the current request context from async context storage.
    
    Returns:
        Current RequestContext or None if not set
    """
    return _current_context.get()


# Alias for compatibility with value-fabric/shared/identity API
get_request_context = get_current_context


def set_current_context(context: RequestContext | None) -> None:
    """Set the current request context in async context storage.
    
    Args:
        context: RequestContext to set
    """
    _current_context.set(context)


# Alias for compatibility with value-fabric/shared/identity API
set_request_context = set_current_context


def clear_current_context() -> None:
    """Clear the current request context from async context storage."""
    _current_context.set(None)


def require_context() -> RequestContext:
    """Get the current request context, raising if not set.
    
    Returns:
        Current RequestContext
        
    Raises:
        RuntimeError: If no context is set
    """
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError(
            "No RequestContext is set — ensure GovernanceMiddleware is installed "
            "and that it calls set_request_context() after authentication."
        )
    return ctx
