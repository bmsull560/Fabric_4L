"""
Authentication and tenant-context dependency for Layer 5 Ground Truth API.

Identity is resolved by the canonical ``GovernanceMiddleware`` (shared across
L1-L6). ``get_current_user`` is a thin adapter that reads the already-validated
``RequestContext`` from ``request.state.governance_context`` and returns a
``TokenClaims`` dataclass for RBAC checks.

Resolution precedence (enforced upstream by ``GovernanceMiddleware``):
  1. ``Authorization: Bearer <JWT>`` — verified with ``JWT_SECRET``.
  2. ``X-API-Key`` — HMAC-verified against the stored hash (disabled on L5).
  3. ``X-Tenant-ID`` + ``X-Service-Auth`` — service-to-service only; the
     ``X-Service-Auth`` header must HMAC-match ``SERVICE_AUTH_SECRET`` (≥32
     chars) or the middleware drops the identity.

Fail-closed contract:
  - In any production-like runtime (``ENVIRONMENT``/``APP_ENV`` in
    ``production|staging``), no ``GovernanceMiddleware`` context means 401.
    No header or query-param fallback is permitted.
  - Dev/test fallbacks (direct JWT decode, ``X-Tenant-ID`` without service
    auth, ``tenant_id`` query param) are gated behind
    ``ALLOW_INSECURE_DEV_AUTH_BYPASS=true`` **and** a non-production
    environment, and are only used when the middleware has not produced a
    context (legacy test paths).
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, Query, Request, status
from value_fabric.shared.identity.fallback_telemetry import (
    enforce_fallback_enabled,
    record_fallback_usage,
)

from ..config import Settings, get_settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class TokenClaims:
    """Parsed and validated JWT claims."""

    tenant_id: UUID
    user_id: str | None = None
    roles: list[str] = field(default_factory=list)
    raw: dict = field(default_factory=dict)

    def has_role(self, role: str) -> bool:
        return role in self.roles

    def require_role(self, role: str) -> None:
        if not self.has_role(role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' is required for this operation.",
            )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _decode_jwt(token: str, settings: Settings) -> dict | None:
    """
    Decode and verify a JWT using the configured secret.

    Returns the payload dict on success, None on any failure.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        logger.debug("JWT validation failed: %s", exc)
        return None


def _extract_org_id_from_payload(payload: dict, settings: Settings) -> UUID | None:
    """Pull the organization UUID from a decoded JWT payload."""
    raw = payload.get(settings.jwt_tenant_claim)
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


def _token_claims_from_context(ctx) -> TokenClaims:
    """Build a ``TokenClaims`` view from the shared ``RequestContext``.

    The GovernanceMiddleware always validates tenant/user/role context before
    the dependency runs; this helper is a pure translation to the dataclass
    consumed by Layer 5 route handlers.
    """
    tenant_raw = ctx.tenant_id
    try:
        tenant_uuid = tenant_raw if isinstance(tenant_raw, UUID) else UUID(str(tenant_raw))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context is invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    user_id = str(ctx.user_id) if ctx.user_id is not None else None
    roles = [str(role) for role in (ctx.roles or [])]
    return TokenClaims(
        tenant_id=tenant_uuid,
        user_id=user_id,
        roles=roles,
        raw=dict(getattr(ctx, "raw", {}) or {}),
    )


def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    tenant_id: str | None = Query(
        default=None,
        description="Tenant UUID — dev/test fallback when JWT is absent",
    ),
    settings: Settings = Depends(get_settings),
) -> TokenClaims:
    """
    Resolve the caller's identity from the GovernanceMiddleware context.

    Primary path (all environments): read ``request.state.governance_context``
    populated by the canonical ``GovernanceMiddleware`` (JWT / API key /
    ``X-Tenant-ID`` + HMAC-verified ``X-Service-Auth``).

    Dev/test fallback (non-production only, requires
    ``ALLOW_INSECURE_DEV_AUTH_BYPASS=true``): when no middleware context is
    present, tolerate a legacy direct JWT / ``X-Tenant-ID`` / query-param path
    to keep existing test fixtures working without weakening production.

    Raises HTTP 401 if no valid identity can be resolved.
    """
    # ── 1. Primary path — GovernanceMiddleware-validated context ──────────
    ctx = getattr(request.state, "governance_context", None) or getattr(
        request.state, "context", None
    )
    if ctx is not None and getattr(ctx, "tenant_id", None):
        return _token_claims_from_context(ctx)

    # In any production-like runtime, a missing middleware context is a
    # fail-closed 401 — no header or query-param fallback is permitted.
    if settings.is_production_like or not settings.allow_insecure_dev_auth_bypass:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # ── 2. Dev/test fallback — direct Bearer JWT verification ─────────────
    if authorization and authorization.startswith("Bearer "):
        enforce_fallback_enabled("layer5.direct_jwt", default=True)
        token = authorization[7:]
        payload = _decode_jwt(token, settings)

        if payload is not None:
            org_id = _extract_org_id_from_payload(payload, settings)
            if org_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=(
                        f"JWT is missing the '{settings.jwt_tenant_claim}' claim "
                        "or it is not a valid UUID."
                    ),
                    headers={"WWW-Authenticate": "Bearer"},
                )

            user_id = payload.get(settings.jwt_user_claim)
            roles = payload.get(settings.jwt_roles_claim, [])
            if isinstance(roles, str):
                roles = [roles]
            record_fallback_usage(
                "layer5.direct_jwt",
                tenant_id=org_id,
                client_id=request.headers.get("X-Client-ID"),
                service="layer5-ground-truth",
                path=str(request.url.path),
            )

            return TokenClaims(
                tenant_id=org_id,
                user_id=user_id,
                roles=roles,
                raw=payload,
            )

    # ── 3. Dev/test fallback — X-Tenant-ID header (no user context) ───────
    # NOTE: This path is reachable only when ALLOW_INSECURE_DEV_AUTH_BYPASS=true
    # AND the environment is NOT production-like. GovernanceMiddleware rejects
    # unverified X-Tenant-ID in production by refusing to build a context, and
    # the fail-closed branch above short-circuits before we get here.
    if x_tenant_id:
        enforce_fallback_enabled("layer5.x_tenant_id_header", default=True)
        try:
            org_id = UUID(x_tenant_id)
            record_fallback_usage(
                "layer5.x_tenant_id_header",
                tenant_id=org_id,
                client_id=request.headers.get("X-Client-ID"),
                service="layer5-ground-truth",
                path=str(request.url.path),
            )
            return TokenClaims(
                tenant_id=org_id,
                user_id="service",
                roles=["service"],
            )
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"X-Tenant-ID header is not a valid UUID: {x_tenant_id!r}",
            )

    # ── 4. Dev/test fallback — tenant_id query param ──────────────────────
    if settings.jwt_fallback_to_query_param and tenant_id:
        enforce_fallback_enabled("layer5.tenant_query_param", default=True)
        try:
            org_id = UUID(tenant_id)
            logger.debug(
                "Using tenant_id query param fallback for tenant %s — "
                "set JWT_FALLBACK_TO_QUERY_PARAM=false in production",
                org_id,
            )
            record_fallback_usage(
                "layer5.tenant_query_param",
                tenant_id=org_id,
                client_id=request.headers.get("X-Client-ID"),
                service="layer5-ground-truth",
                path=str(request.url.path),
            )
            return TokenClaims(
                tenant_id=org_id,
                user_id=None,
                roles=[],
            )
        except (ValueError, AttributeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"tenant_id query param is not a valid UUID: {tenant_id!r}",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Could not resolve organization identity. "
            "Provide a valid Bearer JWT or configure GovernanceMiddleware."
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )
