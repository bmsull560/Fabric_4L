"""Sync-compatible governance middleware for SQLAlchemy sync layers (Layers 1, 2).

This provides the same governance contract as the async middleware but works
with synchronous SQLAlchemy and WSGI-style request processing.
"""

from __future__ import annotations

import hmac
import logging
import os
import threading
from typing import Any, Callable
from uuid import UUID, uuid4
from shared.identity.context import (
    AUTH_SOURCE_SERVICE_ACCOUNT,
    AUTH_SOURCE_JWT,
    AUTH_SOURCE_API_KEY,
    AUTH_SOURCE_UNKNOWN,
    ISOLATION_TIER_SHARED,
)
from shared.models.typed_dict import TypedDictModel

DEFAULT_API_KEY_ROLE = "read_only"

class SyncRequestContext_to_dictResult(TypedDictModel):
    api_key_id: Any
    auth_source: Any
    isolation_tier: Any
    org_id: Any
    permissions: Any
    request_id: Any
    roles: Any
    service_account_id: Any
    service_account_scopes: Any
    tenant_id: Any
    tenant_role: Any
    user_id: Any

# Thread-local storage for sync context
_thread_local = threading.local()

logger = logging.getLogger(__name__)


class SyncRequestContext:
    """Sync-compatible request context (mirrors async RequestContext).

    This is a simplified sync version that stores the same data as the
    async RequestContext but without dataclass dependencies that may vary.
    """

    def __init__(
        self,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        api_key_id: UUID | None = None,
        roles: list[str] | None = None,
        permissions: list[str] | None = None,
        request_id: str | None = None,
        org_id: UUID | None = None,
        tenant_role: str | None = None,
        isolation_tier: str = ISOLATION_TIER_SHARED,
        auth_source: str = AUTH_SOURCE_UNKNOWN,
        service_account_id: UUID | None = None,
        service_account_scopes: list[str] | None = None,
    ):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.api_key_id = api_key_id
        self.roles = roles or []
        self.permissions = permissions or []
        self.request_id = request_id or str(uuid4())
        self.org_id = org_id
        self.tenant_role = tenant_role
        self.isolation_tier = isolation_tier
        self.auth_source = auth_source
        self.service_account_id = service_account_id
        self.service_account_scopes = service_account_scopes or []

    def has_permission(self, permission: str) -> bool:
        """Check if context has specific permission."""
        return permission in self.permissions

    def is_super_admin(self) -> bool:
        """Check if user is super admin."""
        return "super_admin" in self.roles

    def is_tenant_admin(self) -> bool:
        """Check if user is tenant admin."""
        return "tenant_admin" in self.roles or "super_admin" in self.roles

    def is_service_account(self) -> bool:
        """Check if context represents a service account."""
        return self.service_account_id is not None

    def is_auth_source_valid(self) -> bool:
        """Check if the auth_source is a valid/recognized source."""
        return self.auth_source in {
            AUTH_SOURCE_JWT,
            AUTH_SOURCE_API_KEY,
            AUTH_SOURCE_SERVICE_ACCOUNT,
        }

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary."""
        return SyncRequestContext_to_dictResult.model_validate({
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
        })


class GovernanceMiddlewareSync:
    """Sync SQLAlchemy-compatible governance middleware.

    This middleware provides the same tenant resolution and governance
    features as the async version but for synchronous layers (1, 2).

    Usage (Flask/FastAPI with sync SQLAlchemy):
        from shared.identity.middleware_sync import GovernanceMiddlewareSync

        app = Flask(__name__)
        middleware = GovernanceMiddlewareSync(app, api_key_resolver=lookup_key)

    Or as WSGI middleware:
        app = GovernanceMiddlewareSync(app, api_key_resolver=lookup_key)
    """

    # Paths that bypass all authentication checks
    _PUBLIC_PATHS: frozenset[str] = frozenset({
        "/health",
        "/health/detailed",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/",
    })

    def __init__(
        self,
        app: Any,
        api_key_resolver: Callable[[str], dict | None] | None = None,
        jwt_secret: str | None = None,
    ) -> None:
        """Initialize sync governance middleware.

        Args:
            app: WSGI application or Flask/FastAPI app
            api_key_resolver: Sync callable to resolve API keys
            jwt_secret: Secret for JWT verification
        """
        self.app = app
        self._api_key_resolver = api_key_resolver
        self._jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "")
        # P0-4 FIX: Query param auth removed — never trust client-supplied identity
        # self._allow_query_param removed entirely
        self._service_auth_secret = os.getenv("SERVICE_AUTH_SECRET", "")

    def __call__(self, environ: dict, start_response: Callable) -> Any:
        """WSGI entry point."""
        from urllib.parse import parse_qs

        request_path = environ.get("PATH_INFO", "")

        # Check if public path
        if self._is_public_path(request_path):
            return self.app(environ, start_response)

        # Resolve identity
        auth_header = environ.get("HTTP_AUTHORIZATION")
        api_key_header = environ.get("HTTP_X_API_KEY")
        x_tenant_header = environ.get("HTTP_X_TENANT_ID")

        # F-1 FIX: Extract service auth header for X-Tenant-ID validation
        x_service_auth = environ.get("HTTP_X_SERVICE_AUTH", "")

        ctx = self._resolve_identity_sync(
            auth_header=auth_header,
            api_key_header=api_key_header,
            x_tenant_header=x_tenant_header,
            x_service_auth=x_service_auth,
            request_path=request_path,
            request_method=environ.get("REQUEST_METHOD"),
        )

        # Store in thread-local for downstream access
        _thread_local.request_context = ctx
        _thread_local.request_id = ctx.request_id if ctx else str(uuid4())

        try:
            return self.app(environ, start_response)
        finally:
            # Clean up thread-local
            _thread_local.request_context = None
            _thread_local.request_id = None

    def _is_public_path(self, path: str) -> bool:
        """Return True if path should bypass authentication."""
        return path in self._PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc")

    def _resolve_identity_sync(
        self,
        *,
        auth_header: str | None = None,
        api_key_header: str | None = None,
        x_tenant_header: str | None = None,
        x_service_auth: str = "",
        request_path: str | None = None,
        request_method: str | None = None,
    ) -> SyncRequestContext | None:
        """Sync version of identity resolution."""
        from .jwt import decode_jwt

        # 1. Bearer JWT
        if auth_header and auth_header.startswith("Bearer "):
            token_str = auth_header[7:]
            if not token_str.startswith("vf_"):  # Not an API key
                try:
                    payload = decode_jwt(token_str, self._jwt_secret)
                    if payload:
                        return self._build_context_from_jwt_sync(payload)
                except Exception as e:
                    logger.debug("JWT resolution failed: %s", e)
                    return None

        # 2. X-API-Key header
        if api_key_header and self._api_key_resolver:
            try:
                record = self._api_key_resolver(api_key_header)
                if record and record.get("enabled", True):
                    return self._build_context_from_api_key_sync(record)
            except Exception as e:
                logger.debug("API key resolution failed: %s", e)

        # 3. X-Tenant-ID (service-to-service) — F-1 FIX: require shared secret
        if x_tenant_header:
            if not self._service_auth_secret:
                logger.warning("X-Tenant-ID rejected: SERVICE_AUTH_SECRET not configured")
                return None
            if not hmac.compare_digest(x_service_auth, self._service_auth_secret):
                logger.warning("X-Tenant-ID rejected: invalid X-Service-Auth")
                return None
            try:
                tenant_id = UUID(x_tenant_header)
                return SyncRequestContext(
                    tenant_id=tenant_id,
                    user_id=None,
                    roles=["system"],
                    auth_source=AUTH_SOURCE_SERVICE_ACCOUNT,
                )
            except ValueError:
                logger.debug("Invalid X-Tenant-ID: %s", x_tenant_header)

        # P0-4 FIX: Query param auth removed entirely — never trust client-supplied identity

        return None

    def _build_context_from_jwt_sync(self, payload: dict[str, Any]) -> SyncRequestContext:
        """Build SyncRequestContext from JWT payload."""
        tenant_id = _parse_uuid(payload.get("tenant_id"))
        user_id = _parse_uuid(payload.get("sub"))
        org_id = _parse_uuid(payload.get("org_id"))

        service_account_id = _parse_uuid(payload.get("service_account_id"))
        service_account_scopes = payload.get("scopes", [])
        auth_source = AUTH_SOURCE_SERVICE_ACCOUNT if service_account_id else payload.get("auth_source", AUTH_SOURCE_JWT)

        roles = payload.get("roles", [])
        permissions = self._derive_permissions_sync(roles)

        return SyncRequestContext(
            tenant_id=tenant_id,
            user_id=user_id,
            org_id=org_id,
            tenant_role=payload.get("tenant_role"),
            isolation_tier=payload.get("isolation_tier", ISOLATION_TIER_SHARED),
            roles=roles,
            permissions=permissions,
            auth_source=auth_source,
            service_account_id=service_account_id,
            service_account_scopes=service_account_scopes,
        )

    def _build_context_from_api_key_sync(self, record: dict[str, Any]) -> SyncRequestContext:
        """Build SyncRequestContext from API key record."""
        tenant_id = _parse_uuid(record.get("tenant_id"))
        user_id = _parse_uuid(record.get("user_id"))

        role = record.get("role", DEFAULT_API_KEY_ROLE)
        roles = [role]

        permissions = self._derive_permissions_sync(roles)
        custom_perms = record.get("permissions", [])
        if custom_perms:
            permissions = list(set(permissions + custom_perms))

        return SyncRequestContext(
            tenant_id=tenant_id,
            user_id=user_id,
            api_key_id=_parse_uuid(record.get("key_id")),
            roles=roles,
            permissions=permissions,
            auth_source=AUTH_SOURCE_API_KEY,
        )

    def _derive_permissions_sync(self, roles: list[str]) -> list[str]:
        """Derive permissions from roles."""
        try:
            from .permissions import get_permissions_for_role

            perms = []
            for role in roles:
                perms.extend(get_permissions_for_role(role))
            return list(set(perms))
        except ImportError:
            logger.debug("Permissions module not available, returning empty permissions")
            return []


def _parse_uuid(value: Any) -> UUID | None:
    """Safely parse a value into a UUID, returning None on failure."""
    if not value:
        return None
    try:
        return UUID(str(value))
    except ValueError:
        return None


def get_request_context_sync() -> SyncRequestContext | None:
    """Get current request context from thread-local storage.

    Use this in sync code paths to access the resolved tenant context.

    Example:
        from shared.identity.middleware_sync import get_request_context_sync

        def my_handler():
            ctx = get_request_context_sync()
            if ctx:
                print(f"Tenant: {ctx.tenant_id}")
    """
    return getattr(_thread_local, "request_context", None)


def get_tenant_id_sync() -> UUID | None:
    """Get current tenant ID from thread-local storage."""
    ctx = get_request_context_sync()
    return ctx.tenant_id if ctx else None


def require_request_context_sync() -> SyncRequestContext:
    """Require a request context or raise RuntimeError.

    Raises:
        RuntimeError: If no request context is set
    """
    ctx = get_request_context_sync()
    if ctx is None:
        raise RuntimeError(
            "No request context available. Ensure GovernanceMiddlewareSync is installed."
        )
    return ctx
