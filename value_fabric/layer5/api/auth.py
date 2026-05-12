"""Identity and auth dependencies for Layer 5."""

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
from ..runtime_mode import is_production_like_mode
from .tenant_context import enforce_authenticated_tenant_precedence

logger = logging.getLogger(__name__)


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


def _decode_jwt(token: str, settings: Settings) -> dict | None:
    """Decode and verify a JWT using the configured secret."""
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
    raw = payload.get(settings.jwt_tenant_claim)
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except (ValueError, AttributeError):
        return None


def _request_path(request: Request) -> str:
    url = getattr(request, "url", None)
    return str(getattr(url, "path", "<unknown>"))


def _token_claims_from_context(ctx) -> TokenClaims:
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


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    x_tenant_id: str | None = Header(default=None, alias="X-Tenant-ID"),
    tenant_id: str | None = Query(
        default=None,
        description="Tenant UUID - dev/test fallback when JWT is absent",
    ),
    settings: Settings = Depends(get_settings),
) -> TokenClaims:
    """Resolve caller identity from governance context with strict tenant precedence."""
    ctx = getattr(request.state, "governance_context", None) or getattr(
        request.state, "context", None
    )
    if ctx is not None and getattr(ctx, "tenant_id", None):
        claims = _token_claims_from_context(ctx)
        await enforce_authenticated_tenant_precedence(
            request,
            claims.tenant_id,
            actor=claims.user_id,
        )
        return claims

    allow_fallback_admission = settings.allow_insecure_dev_auth_bypass and not is_production_like_mode(
        settings.environment,
        settings.app_env,
    )
    if not allow_fallback_admission:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

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
            logger.warning(
                "Auth fallback admitted via direct_jwt",
                extra={"event": "auth_fallback", "path": _request_path(request), "mode": settings.effective_environment},
            )
            record_fallback_usage(
                "layer5.direct_jwt",
                tenant_id=org_id,
                client_id=request.headers.get("X-Client-ID"),
                service="layer5-ground-truth",
                path=_request_path(request),
            )
            return TokenClaims(
                tenant_id=org_id,
                user_id=user_id,
                roles=roles,
                raw=payload,
            )

    if x_tenant_id:
        enforce_fallback_enabled("layer5.x_tenant_id_header", default=True)
        try:
            org_id = UUID(x_tenant_id)
            logger.warning(
                "Auth fallback admitted via x_tenant_id_header",
                extra={"event": "auth_fallback", "path": _request_path(request), "mode": settings.effective_environment},
            )
            record_fallback_usage(
                "layer5.x_tenant_id_header",
                tenant_id=org_id,
                client_id=request.headers.get("X-Client-ID"),
                service="layer5-ground-truth",
                path=_request_path(request),
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

    if settings.jwt_fallback_to_query_param and tenant_id:
        enforce_fallback_enabled("layer5.tenant_query_param", default=True)
        try:
            org_id = UUID(tenant_id)
            logger.warning(
                "Auth fallback admitted via tenant_query_param",
                extra={"event": "auth_fallback", "path": _request_path(request), "mode": settings.effective_environment, "tenant_id": str(org_id)},
            )
            record_fallback_usage(
                "layer5.tenant_query_param",
                tenant_id=org_id,
                client_id=request.headers.get("X-Client-ID"),
                service="layer5-ground-truth",
                path=_request_path(request),
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
