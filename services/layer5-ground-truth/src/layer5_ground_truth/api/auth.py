"""
JWT-based authentication and tenant extraction for Layer 5 Ground Truth API.

Mirrors the pattern used by Layer 4's TenantMiddleware but implemented as
FastAPI dependencies so they compose cleanly with endpoint signatures.

Resolution order for tenant_id:
  1. Bearer JWT  →  claims[jwt_tenant_claim]
  2. X-Tenant-ID header  (service-to-service calls)
  3. tenant_id query param  (dev / test fallback, disabled in production)

The `get_current_user` dependency returns a `TokenClaims` dataclass that
endpoints can use for RBAC checks.
"""

import logging
from dataclasses import dataclass, field
from uuid import UUID

import jwt
from fastapi import Depends, Header, HTTPException, Query, Request, status

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
    Resolve the caller's identity and organization from the request.

    Priority:
      1. Bearer JWT in Authorization header (verified with JWT_SECRET)
      2. X-Tenant-ID header (service-to-service, no user context)
      3. tenant_id query param (only when JWT_FALLBACK_TO_QUERY_PARAM=true)

    Raises HTTP 401 if no valid identity can be resolved.
    """
    # ── 1. Try Bearer JWT ──────────────────────────────────────────────────
    if authorization and authorization.startswith("Bearer "):
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

            return TokenClaims(
                tenant_id=org_id,
                user_id=user_id,
                roles=roles,
                raw=payload,
            )

    # ── 2. Try X-Tenant-ID header (service-to-service) ────────────────────
    if x_tenant_id:
        try:
            org_id = UUID(x_tenant_id)
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

    # ── 3. Query param fallback (dev / test only) ──────────────────────────
    if settings.jwt_fallback_to_query_param and tenant_id:
        try:
            org_id = UUID(tenant_id)
            logger.debug(
                "Using tenant_id query param fallback for tenant %s — "
                "set JWT_FALLBACK_TO_QUERY_PARAM=false in production",
                org_id,
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

    # ── 4. Use default tenant if configured (last resort) ─────────────────
    if settings.default_tenant_id and settings.default_tenant_id != "default":
        try:
            org_id = UUID(settings.default_tenant_id)
            return TokenClaims(tenant_id=org_id)
        except (ValueError, AttributeError):
            pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Could not resolve organization identity. "
            "Provide a valid Bearer JWT, X-Tenant-ID header, or tenant_id query param."
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )
