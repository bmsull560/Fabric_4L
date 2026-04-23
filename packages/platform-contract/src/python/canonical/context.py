# Canonical context propagation contract for Fabric 4L.
from dataclasses import dataclass, field
from typing import Any, ClassVar
from uuid import UUID

ISOLATION_TIER_SHARED = "shared"
ISOLATION_TIER_SCHEMA = "schema"
ISOLATION_TIER_DATABASE = "database"
VALID_ISOLATION_TIERS = {ISOLATION_TIER_SHARED, ISOLATION_TIER_SCHEMA, ISOLATION_TIER_DATABASE}

AUTH_SOURCE_JWT = "jwt_claim"
AUTH_SOURCE_API_KEY = "api_key"
AUTH_SOURCE_SERVICE_ACCOUNT = "service_account"
AUTH_SOURCE_UNKNOWN = "unknown"


@dataclass(frozen=True)
class RequestContext:
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    api_key_id: UUID | None = None
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    request_id: str | None = None
    org_id: UUID | None = None
    tenant_role: str | None = None
    isolation_tier: str = ISOLATION_TIER_SHARED
    auth_source: str = AUTH_SOURCE_UNKNOWN
    service_account_id: UUID | None = None
    service_account_scopes: list[str] = field(default_factory=list)
    _valid_isolation_tiers: ClassVar[set[str]] = VALID_ISOLATION_TIERS
    _valid_auth_sources: ClassVar[set[str]] = {AUTH_SOURCE_JWT, AUTH_SOURCE_API_KEY, AUTH_SOURCE_SERVICE_ACCOUNT, AUTH_SOURCE_UNKNOWN}

    def has_permission(self, permission: str) -> bool:
        return permission in (self.permissions or [])

    def is_super_admin(self) -> bool:
        return "super_admin" in (self.roles or [])

    def is_tenant_admin(self) -> bool:
        roles = self.roles or []
        return "tenant_admin" in roles or "super_admin" in roles

    def is_service_account(self) -> bool:
        return self.service_account_id is not None

    def validate(self) -> list[str]:
        errors = []
        if self.isolation_tier not in self._valid_isolation_tiers:
            errors.append(f"Invalid isolation_tier: {self.isolation_tier}")
        if self.auth_source not in self._valid_auth_sources:
            errors.append(f"Invalid auth_source: {self.auth_source}")
        if self.service_account_id and not self.service_account_scopes:
            errors.append("Service account must have scopes")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": str(self.tenant_id) if self.tenant_id else None,
            "user_id": str(self.user_id) if self.user_id else None,
            "api_key_id": str(self.api_key_id) if self.api_key_id else None,
            "roles": self.roles,
            "permissions": self.permissions,
            "request_id": self.request_id,
            "org_id": str(self.org_id) if self.org_id else None,
            "tenant_role": self.tenant_role,
            "isolation_tier": self.isolation_tier,
            "auth_source": self.auth_source,
            "service_account_id": str(self.service_account_id) if self.service_account_id else None,
            "service_account_scopes": self.service_account_scopes,
        }
