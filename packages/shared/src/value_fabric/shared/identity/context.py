"""Thread-safe request context for tenant/user identity.

A single ``RequestContext`` is populated by ``GovernanceMiddleware`` at the
start of every request and stored in a ``ContextVar`` so any code that runs
within the same async task can retrieve it without threading it through
function signatures.

This replaces:
- ``layer4-agents/src/tenant/context.py`` (``TenantContext``)
- The ad-hoc ``request.state.authenticated_api_key`` pattern in L3.
"""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional
from uuid import UUID

from .permissions import Permission, Role
from value_fabric.shared.models.typed_dict import TypedDictModel

# Auth source constants
AUTH_SOURCE_JWT = "jwt_claim"
AUTH_SOURCE_API_KEY = "api_key"
AUTH_SOURCE_SERVICE_ACCOUNT = "service_account"
AUTH_SOURCE_UNKNOWN = "unknown"

# Tenant isolation tier constants
ISOLATION_TIER_SHARED = "shared"
ISOLATION_TIER_SCHEMA = "schema"
ISOLATION_TIER_DATABASE = "database"
VALID_ISOLATION_TIERS = {ISOLATION_TIER_SHARED, ISOLATION_TIER_SCHEMA, ISOLATION_TIER_DATABASE}


class RequestContext_to_log_dictResult(TypedDictModel):
    api_key_id: Any
    roles: Any
    source: Any
    tenant_id: Any
    user_id: Any


@dataclass
class RequestContext:
    """Identity context carried by a single request.

    Attributes:
        tenant_id:   Validated tenant UUID.
        user_id:     Human user identifier (``None`` for system/API-key-only calls).
        roles:       List of role strings from JWT or API-key record.
        api_key_id:  Identifier of the API key used, if any.
        permissions: Effective permission set (derived from role + key grants).
        source:      How the identity was resolved (``jwt`` | ``api_key`` | ``header``).
        raw:         Original JWT payload or empty dict — for debugging only.
    """

    tenant_id: UUID
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    api_key_id: Optional[str] = None
    permissions: FrozenSet[Permission] = field(default_factory=frozenset)
    source: str = "unknown"
    raw: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Role / permission helpers
    # ------------------------------------------------------------------

    def has_role(self, role: Role | str) -> bool:
        """Return True if this context carries the given role."""
        role_val = role.value if isinstance(role, Role) else role
        return role_val in self.roles

    def has_any_role(self, *roles: Role | str) -> bool:
        return any(self.has_role(r) for r in roles)

    def has_permission(self, permission: Permission) -> bool:
        """Return True if the effective permission set includes *permission*."""
        return permission in self.permissions

    def has_any_permission(self, *permissions: Permission) -> bool:
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, *permissions: Permission) -> bool:
        return all(self.has_permission(p) for p in permissions)

    def to_log_dict(self) -> Dict[str, Any]:
        """Serialise for structured logging (no sensitive data)."""
        return RequestContext_to_log_dictResult.model_validate({
            "tenant_id": str(self.tenant_id),
            "user_id": self.user_id,
            "roles": self.roles,
            "api_key_id": self.api_key_id,
            "source": self.source,
        })


# ---------------------------------------------------------------------------
# ContextVar storage
# ---------------------------------------------------------------------------

_current_context: ContextVar[Optional[RequestContext]] = ContextVar(
    "vf_request_context",
    default=None,
)


def get_request_context() -> Optional[RequestContext]:
    """Return the current request context, or ``None`` if not set."""
    return _current_context.get()


def set_request_context(ctx: Optional[RequestContext]) -> Token:
    """Set the request context and return the reset token."""
    return _current_context.set(ctx)


def require_context() -> RequestContext:
    """Return the current context or raise ``RuntimeError``.

    Use this in code paths that *must* run within an authenticated request.
    """
    ctx = _current_context.get()
    if ctx is None:
        raise RuntimeError(
            "No RequestContext is set — ensure GovernanceMiddleware is installed "
            "and the endpoint is not bypassing authentication."
        )
    return ctx


class RequestContextManager:
    """Sync context manager for setting the request context.

    Useful in tests and background tasks where there is no HTTP middleware.

    Example::

        with RequestContextManager(ctx):
            result = some_tenant_scoped_operation()
    """

    def __init__(self, ctx: RequestContext) -> None:
        self._ctx = ctx
        self._token: Optional[Token] = None

    def __enter__(self) -> "RequestContextManager":
        self._token = set_request_context(self._ctx)
        return self

    def __exit__(self, *args: Any) -> None:
        if self._token is not None:
            _current_context.reset(self._token)
