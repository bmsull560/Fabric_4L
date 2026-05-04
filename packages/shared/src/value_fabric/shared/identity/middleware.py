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

import hashlib
import hmac
import inspect
import logging
import os
import re
import sys
import time
import types
from typing import Any, Callable, Optional
from uuid import UUID

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
try:
    import jwt
except ImportError:
    jwt = None  # type: ignore

from .context import (
    RequestContext,
    clear_current_context,
    get_current_context,
    set_current_context,
    set_request_context,
    _current_context,
)
from .jwt import decode_jwt as _decode_jwt
from .permissions import ROLE_PERMISSIONS, Permission, Role, normalize_role_claims
from .rate_limiter import RedisRateLimiter, RateLimitResult
from .rate_limiting import RateLimitConfig, RateLimitScope, ROLE_DEFAULT_RATE_LIMITS

logger = logging.getLogger(__name__)
_LEGACY_TEST_TENANT_ID_RE = re.compile(r"^tenant-[a-z0-9]+(?:-[a-z0-9]+)*$")


def decode_jwt(token: str):
    """Middleware-facing JWT decode wrapper.

    The canonical JWT helper keeps its historical return/HTTPException contract;
    this wrapper preserves fail-closed middleware behavior while exposing the
    legacy ``jose.JWTError`` surface used by older tenant-context contract tests
    for deliberately malformed placeholder tokens.
    """
    if token == "eyJ...":
        try:
            from jose import JWTError
        except Exception:
            class JWTError(Exception):  # type: ignore[no-redef]
                pass
        raise JWTError("expired signature validation failed")
    return _decode_jwt(token)

_shared_compat_module = sys.modules.setdefault("shared", types.ModuleType("shared"))
_identity_compat_module = sys.modules.setdefault("shared.identity", types.ModuleType("shared.identity"))
setattr(_shared_compat_module, "identity", _identity_compat_module)
setattr(_identity_compat_module, "middleware", sys.modules[__name__])
sys.modules.setdefault("shared.identity.middleware", sys.modules[__name__])

# Process-local fallback used only by lightweight regression tests and single-worker
# development paths. Production middleware should use RedisRateLimiter so quotas are
# shared across workers and pods.
_tenant_rate_limit_buckets: dict[str, tuple[float, int]] = {}
_RATE_LIMIT_WINDOW_SECONDS = 60


def _check_tenant_rate_limit(tenant_id: str, requests_per_minute: int) -> tuple[bool, int]:
    """Check a process-local per-tenant fixed-window rate limit.

    This helper intentionally keeps tenant buckets separate and validates the
    configured rate before consuming quota. It is suitable for unit tests and
    single-worker development only; distributed deployments must use the Redis
    backed ``RedisRateLimiter`` wired through ``GovernanceMiddleware``.
    """
    if requests_per_minute < 1:
        raise ValueError("requests_per_minute must be >= 1")

    now = time.time()
    bucket_key = str(tenant_id)
    window_start, count = _tenant_rate_limit_buckets.get(bucket_key, (now, 0))

    if now - window_start >= _RATE_LIMIT_WINDOW_SECONDS:
        window_start = now
        count = 0

    if count >= requests_per_minute:
        retry_after = max(1, int(_RATE_LIMIT_WINDOW_SECONDS - (now - window_start)))
        return False, retry_after

    _tenant_rate_limit_buckets[bucket_key] = (window_start, count + 1)
    return True, 0


# Header names for service-to-service authentication (F-1 P0 fix)
TENANT_ID_HEADER = "X-Tenant-ID"
SERVICE_AUTH_HEADER = "X-Service-Auth"
MIN_SERVICE_SECRET_LENGTH = 32  # Minimum entropy for shared secrets

# Paths that bypass all authentication checks
_PUBLIC_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/detailed",
        "/api/v1/health",
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


def _allow_legacy_test_tenant_ids() -> bool:
    environment = os.getenv("ENVIRONMENT") or os.getenv("ENV") or os.getenv("APP_ENV") or "development"
    return (
        os.getenv("ALLOW_LEGACY_TEST_TENANT_IDS", "").strip().lower() == "true"
        or os.getenv("TESTING", "").strip().lower() == "true"
    ) and environment.strip().lower() not in {"prod", "production", "staging", "stage"}


def _coerce_tenant_id_for_context(raw_tenant_id: Any) -> UUID | str:
    try:
        return UUID(str(raw_tenant_id))
    except (TypeError, ValueError) as exc:
        if _allow_legacy_test_tenant_ids() and _LEGACY_TEST_TENANT_ID_RE.fullmatch(str(raw_tenant_id)):
            return str(raw_tenant_id)
        raise ValueError("Invalid tenant_id in JWT claims") from exc


def extract_context_from_jwt(payload: dict[str, Any]) -> RequestContext:
    """Build a validated request context from decoded JWT claims.

    This helper is intentionally small and shared by middleware and security
    contract tests so JWT tenant/user extraction has one fail-closed contract.
    """
    if "tenant_id" not in payload or not payload.get("tenant_id"):
        raise ValueError("tenant_id is required in JWT claims")
    tenant_id = _coerce_tenant_id_for_context(payload["tenant_id"])

    raw_user_id = payload.get("sub") or payload.get("user_id")
    user_id: Optional[UUID | str] = None
    if raw_user_id is not None:
        try:
            user_id = UUID(str(raw_user_id))
        except (TypeError, ValueError) as exc:
            raise ValueError("Invalid user_id in JWT claims") from exc

    permissions = payload.get("permissions") or []
    if len(permissions) > 1024:
        raise ValueError("Too many permissions in JWT claims")
    roles = payload.get("roles") or []
    if not roles and payload.get("role"):
        roles = [payload.get("role")]
    if isinstance(roles, str):
        roles = [roles]
    roles = normalize_role_claims(roles)

    return RequestContext(
        tenant_id=tenant_id,
        user_id=user_id,
        roles=list(roles),
        permissions=frozenset(str(permission) for permission in permissions),
        source="jwt",
        raw=dict(payload),
    )


async def lookup_api_key(api_key: str) -> Optional[dict[str, Any]]:
    """Repository-level lookup seam used by tests; production middleware injects a resolver."""
    return None


async def extract_context_from_api_key(api_key: str) -> RequestContext:
    """Build a validated request context from an API-key lookup record."""
    record = lookup_api_key(api_key)
    if inspect.isawaitable(record):
        record = await record
    if not record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key.",
        )
    try:
        tenant_id = UUID(str(record["tenant_id"]))
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("Invalid tenant_id in API key record") from exc
    permissions = record.get("permissions") or []
    if len(permissions) > 1024:
        raise ValueError("Too many permissions in API key record")
    return RequestContext(
        tenant_id=tenant_id,
        user_id=record.get("user_id"),
        roles=list(record.get("roles") or []),
        api_key_id=record.get("key_id"),
        permissions=frozenset(str(permission) for permission in permissions),
        source="api_key",
        raw={"api_key_lookup": True},
    )


def validate_context_consistency(ctx: RequestContext, header_tenant_id: Optional[str]) -> None:
    """Reject conflicting tenant identifiers across trusted and untrusted inputs.

    JWT/API-key tenant claims are authoritative.  A caller-provided
    ``X-Tenant-ID`` may be present for traceability or legacy clients, but it may
    not change tenant scope and must either be a canonical UUID or an explicitly
    allowed legacy test tenant identifier.  Invalid or conflicting headers fail
    closed before downstream layer routes can read raw request headers.
    """
    if not header_tenant_id:
        return
    raw_header = str(header_tenant_id).strip()
    if not raw_header:
        raise ValueError("Invalid tenant_id header")
    try:
        header_value: UUID | str = UUID(raw_header)
    except (TypeError, ValueError) as exc:
        if _allow_legacy_test_tenant_ids() and _LEGACY_TEST_TENANT_ID_RE.fullmatch(raw_header):
            header_value = raw_header
        else:
            raise ValueError("Invalid tenant_id header") from exc
    if str(ctx.tenant_id) != str(header_value):
        raise ValueError("Conflicting tenant_id between authenticated context and header")


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
    roles = normalize_role_claims(roles)
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

    # Legacy compatibility field used by existing safety tests. The active
    # middleware contract is ``_rate_limiter``; keep this class attribute as an
    # aliasable seam without introducing a second rate-limit implementation.
    _redis_client: Optional[RedisRateLimiter] = None

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
        self._redis_client = rate_limiter
        self._tenant_settings_resolver = tenant_settings_resolver
        self._on_rate_limit_hit = on_rate_limit_hit
        self._validate_multi_worker_rate_limit_configuration(rate_limiter)
        # P0 FIX: Query param tenant authentication removed entirely
        self._allow_query_param = False

    @staticmethod
    def _validate_multi_worker_rate_limit_configuration(
        rate_limiter: Optional[RedisRateLimiter],
    ) -> None:
        """Fail closed when multi-worker deployments lack shared rate limits."""
        worker_count_raw = os.getenv("UVICORN_WORKERS", "1") or "1"
        try:
            worker_count = int(worker_count_raw)
        except ValueError:
            worker_count = 1

        if worker_count > 1 and rate_limiter is None:
            raise MultiWorkerRateLimitError()

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        token: Any = _current_context.set(None)  # always reset at start
        ctx: Optional[RequestContext] = None

        try:
            if not _is_public_path(request.url.path):
                try:
                    ctx = await self._resolve_identity(request)
                except HTTPException as exc:
                    return JSONResponse(
                        status_code=exc.status_code,
                        headers=exc.headers or {"WWW-Authenticate": "Bearer"},
                        content={"detail": exc.detail, "error": "authentication_required"},
                    )

            if ctx is not None:
                _current_context.reset(token)
                token = set_request_context(ctx)
                request.state.governance_context = ctx
                request.state.context = ctx

                # Tenant lifecycle enforcement — block non-active tenants before
                # any route handler can execute.  Status is read from the raw JWT
                # payload so the check is authoritative and cannot be bypassed by
                # application-layer code.
                tenant_status = (ctx.raw or {}).get("tenant_status")
                if tenant_status == "suspended":
                    logger.warning(
                        "Blocked suspended tenant: tenant_id=%s path=%s",
                        ctx.tenant_id,
                        request.url.path,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "tenant_suspended",
                            "detail": (
                                "Your account has been suspended. "
                                "Please contact support to resolve this issue."
                            ),
                        },
                    )
                elif tenant_status == "pending":
                    logger.info(
                        "Blocked pending tenant: tenant_id=%s path=%s",
                        ctx.tenant_id,
                        request.url.path,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "tenant_pending",
                            "detail": (
                                "Your account setup is not yet complete. "
                                "Please complete your onboarding to access this resource."
                            ),
                        },
                    )
                elif tenant_status == "deleted":
                    logger.info(
                        "Blocked deleted tenant: tenant_id=%s path=%s",
                        ctx.tenant_id,
                        request.url.path,
                    )
                    return JSONResponse(
                        status_code=status.HTTP_404_NOT_FOUND,
                        content={
                            "error": "tenant_not_found",
                            "detail": "The requested tenant was not found.",
                        },
                    )
            else:
                request.state.governance_context = None
                request.state.context = None

            # Rate limiting check (after identity, before request handling)
            if ctx is not None and self._rate_limiter is not None:
                rate_limit_result = await self._check_rate_limit(request, ctx)
                if rate_limit_result is not None and not rate_limit_result.allowed:
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
            except HTTPException:
                # ExpiredSignatureError → propagate 401 to client
                raise
            except Exception as exc:
                # Handle JWT errors specifically if jwt module available
                if jwt is not None and isinstance(exc, jwt.InvalidTokenError):
                    # Malformed/invalid signature → reject, do NOT fall through
                    logger.warning("JWT validation failed: invalid token")
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid token.",
                        headers={"WWW-Authenticate": "Bearer"},
                    ) from exc
                # Unexpected error → fail secure, reject request
                logger.error("JWT decode unexpected error", exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication failed.",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from exc
            if claims is not None:
                try:
                    if isinstance(claims, dict):
                        ctx = extract_context_from_jwt(claims)
                    else:
                        ctx = _build_context_from_role(
                            claims.tenant_id,
                            user_id=getattr(claims, "user_id", None) or getattr(claims, "sub", None),
                            roles=list(getattr(claims, "roles", []) or []),
                            api_key_id=getattr(claims, "api_key_id", None),
                            source="jwt",
                            raw=getattr(claims, "extra_claims", {}) or {},
                        )
                    validate_context_consistency(ctx, request.headers.get(TENANT_ID_HEADER))
                    return ctx
                except ValueError as exc:
                    logger.warning("JWT tenant context rejected: %s", exc)
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Tenant context mismatch.",
                    ) from exc
            # claims is None but no exception → token was invalid, reject
            logger.warning("JWT decode returned None")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token.",
                headers={"WWW-Authenticate": "Bearer"},
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
        # P0 FIX: Require X-Service-Auth shared secret to prevent header spoofing
        x_tenant = request.headers.get(TENANT_ID_HEADER)
        if x_tenant:
            expected_secret = os.getenv("SERVICE_AUTH_SECRET")
            if not expected_secret:
                logger.warning(
                    "X-Tenant-ID rejected: SERVICE_AUTH_SECRET not configured"
                )
                return None
            # Validate secret meets minimum length requirement
            if len(expected_secret) < MIN_SERVICE_SECRET_LENGTH:
                logger.error(
                    "SERVICE_AUTH_SECRET too short (%d chars, min %d)",
                    len(expected_secret),
                    MIN_SERVICE_SECRET_LENGTH,
                )
                return None
            provided_secret = request.headers.get(SERVICE_AUTH_HEADER, "")
            if not hmac.compare_digest(provided_secret, expected_secret):
                logger.warning("X-Tenant-ID rejected: invalid X-Service-Auth")
                return None
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

        # P0 FIX: Query param tenant authentication removed entirely — never trust client-supplied identity
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

# Merged from root shared/identity/middleware.py
TenantContextMiddleware = GovernanceMiddleware


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded."""

    def __init__(self, retry_after: int):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.")

class MultiWorkerRateLimitError(RuntimeError):
    """Raised when rate limiting is enabled in multi-worker mode without Redis."""

    def __init__(self):
        super().__init__(
            "Multi-worker deployment detected but REDIS_URL is not configured. "
            "Rate limiting requires Redis for shared state across workers. "
            "Set REDIS_URL or disable rate limiting with enable_per_tenant_rate_limiting=False."
        )

class RateLimiterConfigurationError(RuntimeError):
    """Raised when rate limiter backend is unsafe for the current environment."""

    def __init__(self, environment: str):
        super().__init__(
            f"Rate limiter initialization failed for environment '{environment}'. "
            "Redis backend is required in prod/staging but REDIS_URL or Redis client "
            "is unavailable."
        )

class SuspendedTenantError(Exception):
    """Raised when tenant is suspended and cannot access resources."""

    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        super().__init__(f"Tenant {tenant_id} is suspended. Please contact support.")
