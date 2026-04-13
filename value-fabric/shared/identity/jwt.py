"""JWT encode / decode helpers — canonical for all Value Fabric services.

Based on the pattern in ``layer5-ground-truth/src/api/auth.py`` but extracted
into the shared library so every layer uses identical verification logic.

Key design choices:
- HS256 (HMAC-SHA256) — symmetric, fast, industry standard.
- ``JWT_SECRET`` env var is the single signing secret; rotate via env update +
  rolling restart (no dual-key support needed in Phase 1).
- Verification is always on; there is no ``verify_signature: False`` escape hatch.
- ``exp`` claim is always checked.
- Returns ``None`` on soft failures; raises ``HTTPException(401)`` on expired
  tokens (so callers can differentiate expired vs. malformed).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional
from uuid import UUID

import jwt
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Settings (read from env; no Pydantic-Settings dependency here so the shared
# library stays lightweight and importable by all layers)
# ---------------------------------------------------------------------------

_DEFAULT_ALGORITHM = "HS256"
_DEFAULT_TENANT_CLAIM = "tenant_id"
_DEFAULT_USER_CLAIM = "sub"
_DEFAULT_ROLES_CLAIM = "roles"


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "changeme-in-production")
    if secret == "changeme-in-production":
        logger.warning(
            "JWT_SECRET is using the default development value — "
            "set a strong secret in production."
        )
    return secret


def _get_jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", _DEFAULT_ALGORITHM)


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------


@dataclass
class TokenClaims:
    """Validated claims extracted from a JWT.

    ``tenant_id`` is always a UUID; ``user_id`` and ``roles`` are optional so
    that service-to-service tokens (which carry a tenant but no human user) are
    supported transparently.
    """

    tenant_id: UUID
    user_id: Optional[str] = None
    roles: List[str] = field(default_factory=list)
    api_key_id: Optional[str] = None
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


def decode_jwt(token: str) -> Optional[TokenClaims]:
    """Verify and decode a JWT.

    Returns:
        ``TokenClaims`` on success, ``None`` if the token is malformed or
        the signature is invalid.

    Raises:
        ``HTTPException(401)`` if the token has expired (so callers can
        propagate an informative error to the client).
    """
    secret = _get_jwt_secret()
    algorithm = _get_jwt_algorithm()
    tenant_claim = os.getenv("JWT_TENANT_CLAIM", _DEFAULT_TENANT_CLAIM)
    user_claim = os.getenv("JWT_USER_CLAIM", _DEFAULT_USER_CLAIM)
    roles_claim = os.getenv("JWT_ROLES_CLAIM", _DEFAULT_ROLES_CLAIM)

    try:
        payload: dict = jwt.decode(
            token,
            secret,
            algorithms=[algorithm],
            options={"verify_exp": True},
        )
    except jwt.ExpiredSignatureError:
        logger.debug("JWT has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as exc:
        logger.debug("JWT validation failed: %s", exc)
        return None

    raw_tenant = payload.get(tenant_claim)
    if not raw_tenant:
        logger.debug("JWT missing '%s' claim", tenant_claim)
        return None

    try:
        tenant_id = UUID(str(raw_tenant))
    except (ValueError, AttributeError):
        logger.debug("JWT '%s' claim is not a valid UUID: %r", tenant_claim, raw_tenant)
        return None

    roles = payload.get(roles_claim, [])
    if isinstance(roles, str):
        roles = [roles]

    return TokenClaims(
        tenant_id=tenant_id,
        user_id=payload.get(user_claim),
        roles=roles,
        api_key_id=payload.get("api_key_id"),
        raw=payload,
    )


def encode_jwt(
    tenant_id: UUID,
    *,
    user_id: Optional[str] = None,
    roles: Optional[List[str]] = None,
    api_key_id: Optional[str] = None,
    extra_claims: Optional[dict] = None,
    expires_in_seconds: int = 3600,
) -> str:
    """Create a signed JWT for the given identity.

    Used by the Tenant Service when issuing tokens during login / key rotation.
    """
    import time

    secret = _get_jwt_secret()
    algorithm = _get_jwt_algorithm()
    tenant_claim = os.getenv("JWT_TENANT_CLAIM", _DEFAULT_TENANT_CLAIM)
    user_claim = os.getenv("JWT_USER_CLAIM", _DEFAULT_USER_CLAIM)
    roles_claim = os.getenv("JWT_ROLES_CLAIM", _DEFAULT_ROLES_CLAIM)

    now = int(time.time())
    payload: dict = {
        tenant_claim: str(tenant_id),
        "iat": now,
        "exp": now + expires_in_seconds,
    }
    if user_id is not None:
        payload[user_claim] = user_id
    if roles is not None:
        payload[roles_claim] = roles
    if api_key_id is not None:
        payload["api_key_id"] = api_key_id
    if extra_claims:
        payload.update(extra_claims)

    return jwt.encode(payload, secret, algorithm=algorithm)
