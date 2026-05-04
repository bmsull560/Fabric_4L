"""Canonical context propagation contract for Fabric 4L."""

from __future__ import annotations

import contextvars
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

_current_context: contextvars.ContextVar["RequestContext | None"] = contextvars.ContextVar(
    "request_context",
    default=None,
)


class ContextContractError(RuntimeError):
    """Raised when canonical request context propagation is violated."""


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

    def is_isolation_tier_valid(self) -> bool:
        return self.isolation_tier in self._valid_isolation_tiers

    def is_auth_source_valid(self) -> bool:
        return self.auth_source in self._valid_auth_sources

    def validate(self) -> list[str]:
        errors = []
        if not self.is_isolation_tier_valid():
            errors.append(f"Invalid isolation_tier: {self.isolation_tier}")
        if not self.is_auth_source_valid():
            errors.append(f"Invalid auth_source: {self.auth_source}")
        if self.service_account_id and not self.service_account_scopes:
            errors.append("Service account must have scopes")
        return errors

    @staticmethod
    def _uuid_to_str(value: UUID | None) -> str | None:
        return str(value) if value else None

    def to_dict(self) -> dict[str, Any]:
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


def get_current_context() -> RequestContext | None:
    return _current_context.get()


def get_request_context() -> RequestContext | None:
    return get_current_context()


def set_current_context(context: RequestContext | None) -> None:
    _current_context.set(context)


def set_request_context(context: RequestContext | None) -> None:
    set_current_context(context)


def clear_current_context() -> None:
    _current_context.set(None)


def require_context() -> RequestContext:
    context = get_current_context()
    if context is None:
        raise ContextContractError(
            "No RequestContext is set - ensure GovernanceMiddleware is installed "
            "and that it calls set_request_context() after authentication."
        )
    return context
