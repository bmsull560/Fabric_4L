"""Synchronous governance middleware stub for local validation.

This stub provides the minimal interfaces required by database.py
when the full async middleware is not available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, FrozenSet, List, Optional
from uuid import UUID

from fastapi import Header, HTTPException, Request, status

from .permissions import Permission, Role
from value_fabric.shared.models.typed_dict import TypedDictModel
from .context import (
    AUTH_SOURCE_JWT,
    AUTH_SOURCE_API_KEY,
    AUTH_SOURCE_SERVICE_ACCOUNT,
    AUTH_SOURCE_UNKNOWN,
    ISOLATION_TIER_SHARED,
)


@dataclass
class SyncRequestContext:
    """Synchronous request context stub."""

    tenant_id: UUID
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    api_key_id: Optional[str] = None
    permissions: FrozenSet[Permission] = field(default_factory=frozenset)
    source: str = "unknown"
    raw: Dict[str, Any] = field(default_factory=dict)


def get_request_context_sync(
    request: Request,
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SyncRequestContext:
    """Stub dependency that extracts tenant from X-Organization-ID header."""
    if x_organization_id:
        try:
            tenant_id = UUID(x_organization_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid X-Organization-ID header",
            )
    else:
        # P0 FIX: Never fall back to a hardcoded tenant — require authentication
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )

    return SyncRequestContext(tenant_id=tenant_id, source="header")


def require_request_context_sync(
    request: Request,
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SyncRequestContext:
    """Stub dependency that requires tenant from X-Organization-ID header."""
    if not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="X-Organization-ID header required",
        )
    try:
        tenant_id = UUID(x_organization_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Organization-ID header",
        )

    return SyncRequestContext(tenant_id=tenant_id, source="header")

# Merged from root identity/middleware_sync.py
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
