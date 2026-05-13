from __future__ import annotations

import logging
import os
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, FrozenSet, Iterable, List, Optional
from uuid import UUID, uuid4

from fastapi import Header, HTTPException, Request, status

from .context import (
    AUTH_SOURCE_API_KEY,
    AUTH_SOURCE_JWT,
    AUTH_SOURCE_SERVICE_ACCOUNT,
    AUTH_SOURCE_UNKNOWN,
    ISOLATION_TIER_SHARED,
    VALID_AUTH_SOURCES,
    VALID_ISOLATION_TIERS,
    RequestContext,
)
from .permissions import Permission, Role, ROLE_PERMISSIONS

logger = logging.getLogger(__name__)
_thread_local = threading.local()
DEFAULT_API_KEY_ROLE = Role.READ_ONLY.value


@dataclass
class SyncRequestContext:
    """Synchronous request context used by sync SQLAlchemy dependencies."""

    tenant_id: Optional[UUID | str] = None
    user_id: Optional[Any] = None
    roles: List[str] = field(default_factory=list)
    api_key_id: Optional[str] = None
    permissions: FrozenSet[Permission | str] | Iterable[Permission | str] = field(default_factory=frozenset)
    source: str = AUTH_SOURCE_UNKNOWN
    raw: Dict[str, Any] = field(default_factory=dict)
    auth_source: Optional[str] = None
    request_id: Optional[str] = None
    org_id: Optional[Any] = None
    tenant_role: Optional[str] = None
    isolation_tier: str = ISOLATION_TIER_SHARED
    service_account_id: Optional[str] = None
    service_account_scopes: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.roles = [str(role) for role in (self.roles or [])]
        self.permissions = frozenset(self.permissions or [])
        self.service_account_scopes = [str(scope) for scope in (self.service_account_scopes or [])]
        if self.auth_source is None:
            self.auth_source = self.source
        if self.source == AUTH_SOURCE_UNKNOWN and self.auth_source:
            self.source = self.auth_source

    def is_auth_source_valid(self) -> bool:
        return self.auth_source in VALID_AUTH_SOURCES


def _parse_uuid(value: Any) -> UUID | None:
    if value is None or value == "":
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


def _permissions_for_roles(roles: Iterable[str]) -> FrozenSet[Permission]:
    permissions: set[Permission] = set()
    for role_str in roles:
        try:
            permissions |= ROLE_PERMISSIONS[Role(str(role_str))].permissions
        except (ValueError, KeyError):
            logger.debug("Unknown role '%s' in sync context", role_str)
    return frozenset(permissions)


def _from_request_context(ctx: RequestContext) -> SyncRequestContext:
    return SyncRequestContext(
        tenant_id=ctx.tenant_id,
        user_id=ctx.user_id,
        roles=list(ctx.roles),
        api_key_id=ctx.api_key_id,
        permissions=frozenset(ctx.permissions),
        source=ctx.source,
        raw=dict(ctx.raw or {}),
        auth_source=ctx.auth_source,
        request_id=ctx.request_id,
        org_id=ctx.org_id,
        tenant_role=ctx.tenant_role,
        isolation_tier=ctx.isolation_tier,
        service_account_id=ctx.service_account_id,
        service_account_scopes=list(ctx.service_account_scopes),
    )


def _reject_spoofed_organization_header(x_organization_id: Optional[str], tenant_id: Optional[UUID | str]) -> None:
    if not x_organization_id or tenant_id is None:
        return
    try:
        org_uuid = UUID(str(x_organization_id))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Organization-ID header") from exc
    if str(org_uuid) != str(tenant_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization header does not match authenticated tenant")


def _reject_spoofed_tenant_header(x_tenant_id: Optional[str], tenant_id: Optional[UUID | str]) -> None:
    if not x_tenant_id or tenant_id is None:
        return
    try:
        header_uuid = UUID(str(x_tenant_id))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-Tenant-ID header",
        ) from exc
    if str(header_uuid) != str(tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="X-Tenant-ID does not match authenticated tenant",
        )


def get_request_context_sync(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SyncRequestContext:
    """Return a sync context bridged from canonical governance state."""
    governance_context = getattr(request.state, "governance_context", None)
    if governance_context is not None:
        if hasattr(governance_context, "validate"):
            validation_errors = list(governance_context.validate())
            if validation_errors:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Request identity context failed validation")
        _reject_spoofed_tenant_header(x_tenant_id, governance_context.tenant_id)
        _reject_spoofed_organization_header(x_organization_id, governance_context.tenant_id)
        return _from_request_context(governance_context)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")


def require_request_context_sync(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-ID"),
) -> SyncRequestContext:
    return get_request_context_sync(
        request,
        x_tenant_id=x_tenant_id,
        x_organization_id=x_organization_id,
    )


class GovernanceMiddlewareSync:
    _PUBLIC_PATHS: frozenset[str] = frozenset({"/health", "/health/detailed", "/metrics", "/docs", "/openapi.json", "/redoc", "/"})

    def __init__(self, app: Any, api_key_resolver: Callable[[str], dict | None] | None = None, jwt_secret: str | None = None) -> None:
        self.app = app
        self._api_key_resolver = api_key_resolver
        self._jwt_secret = jwt_secret or os.getenv("JWT_SECRET", "")

    def __call__(self, environ: dict, start_response: Callable) -> Any:
        request_path = environ.get("PATH_INFO", "")
        if self._is_public_path(request_path):
            return self.app(environ, start_response)
        ctx = self._resolve_identity_sync(
            auth_header=environ.get("HTTP_AUTHORIZATION"),
            api_key_header=environ.get("HTTP_X_API_KEY"),
            x_tenant_header=environ.get("HTTP_X_TENANT_ID"),
        )
        _thread_local.request_context = ctx
        _thread_local.request_id = ctx.request_id if ctx else str(uuid4())
        try:
            return self.app(environ, start_response)
        finally:
            _thread_local.request_context = None
            _thread_local.request_id = None

    def _is_public_path(self, path: str) -> bool:
        return path in self._PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc")

    def _resolve_identity_sync(self, *, auth_header: str | None = None, api_key_header: str | None = None, x_tenant_header: str | None = None, **_: Any) -> SyncRequestContext | None:
        from .jwt import decode_jwt
        if auth_header and auth_header.startswith("Bearer "):
            token_str = auth_header[7:]
            if not token_str.startswith("vf_"):
                try:
                    payload = decode_jwt(token_str, self._jwt_secret)
                    if payload:
                        return self._build_context_from_jwt_sync(payload)
                except Exception as exc:
                    logger.debug("JWT resolution failed: %s", exc)
                    return None
        if api_key_header and self._api_key_resolver:
            try:
                record = self._api_key_resolver(api_key_header)
                if record and record.get("enabled", True):
                    return self._build_context_from_api_key_sync(record)
            except Exception as exc:
                logger.debug("API key resolution failed: %s", exc)
        return None

    def _build_context_from_jwt_sync(self, payload: dict[str, Any]) -> SyncRequestContext:
        tenant_id = _parse_uuid(payload.get("tenant_id"))
        user_id = _parse_uuid(payload.get("sub") or payload.get("user_id"))
        roles = [str(role) for role in payload.get("roles", [])]
        auth_source = payload.get("auth_source", AUTH_SOURCE_JWT)
        if payload.get("service_account_id"):
            auth_source = AUTH_SOURCE_SERVICE_ACCOUNT
        return SyncRequestContext(
            tenant_id=tenant_id,
            user_id=user_id,
            roles=roles,
            permissions=_permissions_for_roles(roles),
            auth_source=auth_source,
            source=auth_source,
            request_id=payload.get("request_id"),
            org_id=_parse_uuid(payload.get("org_id")),
            service_account_id=str(payload.get("service_account_id")) if payload.get("service_account_id") else None,
            service_account_scopes=payload.get("scopes", []),
            raw=dict(payload),
        )

    def _build_context_from_api_key_sync(self, record: dict[str, Any]) -> SyncRequestContext:
        roles = [str(record.get("role", DEFAULT_API_KEY_ROLE))]
        permissions = set(_permissions_for_roles(roles))
        for permission in record.get("permissions") or []:
            try:
                permissions.add(Permission(str(permission)))
            except ValueError:
                logger.debug("Ignoring unknown API-key permission '%s'", permission)
        return SyncRequestContext(
            tenant_id=_parse_uuid(record.get("tenant_id")),
            user_id=_parse_uuid(record.get("user_id")),
            api_key_id=str(record.get("key_id")) if record.get("key_id") is not None else None,
            roles=roles,
            permissions=frozenset(permissions),
            auth_source=AUTH_SOURCE_API_KEY,
            source=AUTH_SOURCE_API_KEY,
            request_id=str(record.get("request_id")) if record.get("request_id") is not None else None,
            raw=dict(record),
        )
