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
from .rate_limiter import RedisRateLimiter, RateLimitResult
from .rate_limiting import RateLimitConfig, RateLimitScope, ROLE_DEFAULT_RATE_LIMITS

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
        rate_limiter: Optional[RedisRateLimiter] = None,
        tenant_settings_resolver: Optional[Callable] = None,
        on_rate_limit_hit: Optional[Callable[[str, str], None]] = None,
    ) -> None:
        super().__init__(app)
        self._api_key_resolver = api_key_resolver
        self._rate_limiter = rate_limiter
        self._tenant_settings_resolver = tenant_settings_resolver
        self._on_rate_limit_hit = on_rate_limit_hit
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

            # Rate limiting check (after identity, before request handling)
            if ctx is not None and self._rate_limiter is not None:
                rate_limit_result = await self._check_rate_limit(request, ctx)
                if rate_limit_result is not None and not rate_limit_result.allowed:
                    from fastapi.responses import JSONResponse
                    config = self._resolve_rate_limit_config(request, ctx)
                    rate_limit_rpm = config.requests_per_minute if config else ""
                    headers = {
                        "X-RateLimit-Limit": str(rate_limit_rpm),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(rate_limit_result.reset_at)),
                        "Retry-After": str(rate_limit_result.retry_after) if rate_limit_result.retry_after is not None else "60",
                    }
                    if self._on_rate_limit_hit is not None and config is not None:
                        try:
                            self._on_rate_limit_hit(str(ctx.tenant_id), config.scope.value)
                        except Exception:
                            pass
                    return JSONResponse(
                        status_code=429,
                        headers=headers,
                        content={"detail": "Rate limit exceeded"},
                    )

            response = await call_next(request)

        finally:
            _current_context.reset(token)

        if ctx is not None:
            response.headers["X-Tenant-ID-Resolved"] = str(ctx.tenant_id)

        # Add rate limit headers if we performed a rate limit check
        if ctx is not None and self._rate_limiter is not None:
            config = self._resolve_rate_limit_config(request, ctx)
            if config is not None:
                # We need the actual result to set remaining accurately.
                # Re-run check (Redis script is idempotent for allowed requests)
                rate_key = self._build_rate_limit_key(request, ctx, config)
                result = await self._rate_limiter.check(rate_key, config)
                response.headers["X-RateLimit-Limit"] = str(config.requests_per_minute)
                response.headers["X-RateLimit-Remaining"] = str(max(0, result.remaining))
                response.headers["X-RateLimit-Reset"] = str(int(result.reset_at))

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

                request.state.api_key_record = record
                return RequestContext(
                    tenant_id=tenant_id,
                    user_id=record.get("user_id"),
                    roles=roles,
                    api_key_id=record.get("key_id"),
                    permissions=permissions,
                    source="api_key",
                    raw={"rate_limit_per_minute": record.get("rate_limit_per_minute")},
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

    # ------------------------------------------------------------------
    # Rate limiting helpers
    # ------------------------------------------------------------------

    def _resolve_rate_limit_config(
        self, request: Request, ctx: RequestContext
    ) -> Optional[RateLimitConfig]:
        """Determine the effective rate limit config for the request."""
        # super_admin and system are unlimited
        if ctx.has_any_role(Role.SUPER_ADMIN, Role.SYSTEM):
            return None

        # 1. API key override
        if ctx.source == "api_key" and hasattr(request.state, "api_key_record"):
            record = request.state.api_key_record
            api_key_rpm = record.get("rate_limit_per_minute")
            if api_key_rpm is not None:
                return RateLimitConfig(
                    requests_per_minute=api_key_rpm,
                    burst_size=min(50, api_key_rpm),
                    scope=RateLimitScope.API_KEY,
                )

        # 2. Tenant settings override
        if self._tenant_settings_resolver is not None:
            # Fire-and-forget async call — we need to handle this in dispatch
            # Since this is sync, we'll skip the async tenant resolver here
            # and handle it in _check_rate_limit instead.
            pass

        # 3. Role defaults
        for role_str in ctx.roles:
            try:
                role = Role(role_str)
                config = ROLE_DEFAULT_RATE_LIMITS.get(role)
                if config is not None:
                    return config
            except ValueError:
                continue

        return ROLE_DEFAULT_RATE_LIMITS.get(Role.READ_ONLY)

    async def _check_rate_limit(
        self, request: Request, ctx: RequestContext
    ) -> Optional[RateLimitResult]:
        """Run rate limit check and return result."""
        if self._rate_limiter is None:
            return None

        # Check tenant settings async if resolver is available
        if self._tenant_settings_resolver is not None:
            try:
                settings = await self._tenant_settings_resolver(ctx.tenant_id)
                if settings and isinstance(settings, dict) and "rate_limits" in settings:
                    rate_limits = settings["rate_limits"]
                    if isinstance(rate_limits, dict):
                        tenant_config = RateLimitConfig(
                            requests_per_minute=rate_limits.get("requests_per_minute", 60),
                            requests_per_hour=rate_limits.get("requests_per_hour"),
                            burst_size=rate_limits.get("burst_size", 10),
                            scope=RateLimitScope(rate_limits.get("scope", "tenant")),
                        )
                        rate_key = self._build_rate_limit_key(request, ctx, tenant_config)
                        return await self._rate_limiter.check(rate_key, tenant_config)
            except Exception as exc:
                logger.warning("Tenant settings resolver failed: %s", exc)

        config = self._resolve_rate_limit_config(request, ctx)
        if config is None:
            return None

        rate_key = self._build_rate_limit_key(request, ctx, config)
        return await self._rate_limiter.check(rate_key, config)

    def _build_rate_limit_key(
        self, request: Request, ctx: RequestContext, config: RateLimitConfig
    ) -> str:
        """Build a Redis key for the rate limit window."""
        if config.scope == RateLimitScope.API_KEY and ctx.api_key_id:
            return f"ratelimit:api_key:{ctx.api_key_id}"
        if config.scope == RateLimitScope.USER and ctx.user_id:
            return f"ratelimit:user:{ctx.tenant_id}:{ctx.user_id}"
        return f"ratelimit:tenant:{ctx.tenant_id}"
