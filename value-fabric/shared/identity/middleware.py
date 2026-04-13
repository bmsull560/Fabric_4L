"""GovernanceMiddleware — single authentication / tenant-resolution middleware.

Replaces:
- ``layer3-knowledge/src/auth/middleware.py`` (``AuthenticationMiddleware``)
- ``layer4-agents/src/tenant/middleware.py``  (``TenantMiddleware``)

Resolution order (first match wins):
  1. ``Authorization: Bearer <JWT>`` — verified with HMAC-SHA256; extracts
     tenant_id, user_id, roles from claims.
  2. ``X-API-Key`` header — HMAC-SHA256 verified against stored hash; the DB
     record provides tenant_id, user_id, role, permissions.
  3. ``X-Tenant-ID`` header (UUID) — accepted *only* for internal
     service-to-service calls; grants the ``system`` role.
  4. Query param ``tenant_id`` — only when ``ALLOW_TENANT_QUERY_PARAM=true``
     (dev/test fallback).

On success, a ``RequestContext`` is stored in the ``ContextVar`` so all
downstream code can call ``get_request_context()`` or ``require_context()``.

On failure / missing credentials, the middleware passes the request through
**without** a context — individual endpoints use FastAPI Depends to enforce
authentication where required (some endpoints, e.g. ``/health``, are public).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Callable, Optional
from uuid import UUID

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from .context import RequestContext, set_request_context, _current_context
from .jwt import decode_jwt
from .permissions import ROLE_PERMISSIONS, Permission, Role

logger = logging.getLogger(__name__)

# Paths that bypass all authentication checks
_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/detailed",
        "/metrics",
        "/docs",
        "/openapi.json",
        "/redoc",
        "/",
    }
)


def _is_public_path(path: str) -> bool:
    """Return True if the path should bypass authentication."""
    return path in _PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc")


def _build_context_from_role(
    tenant_id: UUID,
    *,
    user_id: Optional[str],
    roles: list[str],
    api_key_id: Optional[str] = None,
    source: str,
    raw: dict,
) -> RequestContext:
    """Build a RequestContext, computing effective permissions from roles."""
    permissions: set[Permission] = set()
    for role_str in roles:
        try:
            role = Role(role_str)
            permissions |= ROLE_PERMISSIONS[role].permissions
        except (ValueError, KeyError):
            logger.debug("Unknown role '%s' in token — skipping", role_str)

    return RequestContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=roles,
        api_key_id=api_key_id,
        permissions=frozenset(permissions),
        source=source,
        raw=raw,
    )


class GovernanceMiddleware(BaseHTTPMiddleware):
    """Unified auth + tenant-resolution middleware for all Value Fabric layers.

    Args:
        app:               ASGI application.
        api_key_resolver:  Optional async callable ``(raw_key: str) -> Optional[dict]``
                           that looks up an API key record from the database.
                           Signature: ``async def resolve(key: str) -> dict | None``
                           Expected dict keys: ``tenant_id`` (str UUID), ``user_id``
                           (str|None), ``role`` (str), ``permissions`` (list[str]|None),
                           ``key_id`` (str), ``enabled`` (bool).
                           Pass ``None`` to disable API-key authentication
                           (JWT-only mode).
    """

    def __init__(
        self,
        app: Any,
        api_key_resolver: Optional[Callable] = None,
    ) -> None:
        super().__init__(app)
        self._api_key_resolver = api_key_resolver
        self._allow_query_param = (
            os.getenv("ALLOW_TENANT_QUERY_PARAM", "false").lower() == "true"
        )

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        token: Any = _current_context.set(None)  # always reset at start
        ctx: Optional[RequestContext] = None

        try:
            if not _is_public_path(request.url.path):
                ctx = await self._resolve_identity(request)

            if ctx is not None:
                _current_context.reset(token)
                token = set_request_context(ctx)
                request.state.governance_context = ctx
            else:
                request.state.governance_context = None

            response = await call_next(request)

        finally:
            _current_context.reset(token)

        if ctx is not None:
            response.headers["X-Tenant-ID-Resolved"] = str(ctx.tenant_id)

        return response

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------

    async def _resolve_identity(self, request: Request) -> Optional[RequestContext]:
        """Try each resolution strategy in priority order."""

        # 1. Bearer JWT
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token_str = auth_header[7:]
            try:
                claims = decode_jwt(token_str)
            except Exception:
                # ExpiredSignatureError already raised as HTTPException;
                # other errors fall through to next strategy.
                return None
            if claims is not None:
                return _build_context_from_role(
                    claims.tenant_id,
                    user_id=claims.user_id,
                    roles=claims.roles,
                    api_key_id=claims.api_key_id,
                    source="jwt",
                    raw=claims.raw,
                )

        # 2. X-API-Key header
        raw_api_key = request.headers.get("X-API-Key")
        if raw_api_key and self._api_key_resolver is not None:
            record = await self._api_key_resolver(raw_api_key)
            if record and record.get("enabled", True):
                try:
                    tenant_id = UUID(str(record["tenant_id"]))
                except (ValueError, KeyError):
                    logger.warning("API key record has invalid tenant_id: %r", record.get("tenant_id"))
                    return None

                role_str: str = record.get("role", Role.READ_ONLY.value)
                roles = [role_str]

                # Allow explicit per-key permission overrides stored in DB
                custom_perms: list[str] = record.get("permissions") or []
                if custom_perms:
                    extra: set[Permission] = set()
                    for p in custom_perms:
                        try:
                            extra.add(Permission(p))
                        except ValueError:
                            pass
                    role = Role(role_str)
                    permissions = frozenset(ROLE_PERMISSIONS[role].permissions | extra)
                else:
                    try:
                        permissions = ROLE_PERMISSIONS[Role(role_str)].permissions
                    except (ValueError, KeyError):
                        permissions = frozenset()

                return RequestContext(
                    tenant_id=tenant_id,
                    user_id=record.get("user_id"),
                    roles=roles,
                    api_key_id=record.get("key_id"),
                    permissions=permissions,
                    source="api_key",
                )

        # 3. X-Tenant-ID (service-to-service)
        x_tenant = request.headers.get("X-Tenant-ID")
        if x_tenant:
            try:
                tenant_id = UUID(x_tenant)
            except ValueError:
                logger.debug("Invalid X-Tenant-ID header: %r", x_tenant)
                return None
            return _build_context_from_role(
                tenant_id,
                user_id="service",
                roles=[Role.SYSTEM.value],
                source="header",
                raw={},
            )

        # 4. Query param fallback (dev/test only)
        if self._allow_query_param:
            qp_tenant = request.query_params.get("tenant_id")
            if qp_tenant:
                try:
                    tenant_id = UUID(qp_tenant)
                    return _build_context_from_role(
                        tenant_id,
                        user_id=None,
                        roles=[Role.READ_ONLY.value],
                        source="query_param",
                        raw={},
                    )
                except ValueError:
                    pass

        return None
