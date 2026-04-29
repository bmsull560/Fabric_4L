from __future__ import annotations

import logging
import os
import time
import json
from typing import Any, Dict, List, Optional
from uuid import UUID

import jwt
from fastapi import HTTPException, status

from .models import TokenClaims
from shared.models.typed_dict import TypedDictModel


class get_jwksResult(TypedDictModel):
    keys: list[Any]

class _build_keysetResult(TypedDictModel):
    active_kid: Any
    algorithm: Any
    signing_key: Any
    verify: Any

logger = logging.getLogger(__name__)

_DEFAULT_ALGORITHM = "HS256"
_DEFAULT_TENANT_CLAIM = "tenant_id"
_DEFAULT_USER_CLAIM = "sub"
_DEFAULT_ROLES_CLAIM = "roles"
_DEFAULT_JWT_SECRET = "changeme-in-production"

_DEVELOPMENT_ENVIRONMENTS = {"local", "dev", "development", "test", "testing", "ci"}
_ENV_KEYS = ("ENVIRONMENT", "ENV", "APP_ENV", "VF_ENV", "VALUE_FABRIC_ENV", "PYTHON_ENV")


def _detect_environment() -> str:
    for key in _ENV_KEYS:
        value = os.getenv(key)
        if value and value.strip():
            return value.strip().lower()
    return "development"


def _is_non_dev_environment() -> bool:
    return _detect_environment() not in _DEVELOPMENT_ENVIRONMENTS


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    env = _detect_environment()
    is_non_dev = _is_non_dev_environment()

    if not secret:
        if is_non_dev:
            raise RuntimeError(
                "JWT_SECRET is required in non-development environments. "
                f"Detected environment: {env}."
            )
        logger.warning(
            "JWT_SECRET is unset in %s; using local development fallback.",
            env,
        )
        return _DEFAULT_JWT_SECRET

    if secret == _DEFAULT_JWT_SECRET:
        if is_non_dev:
            raise RuntimeError(
                "JWT_SECRET must not use the default value in non-development "
                f"environments. Detected environment: {env}."
            )
        logger.warning(
            "JWT_SECRET is using the default development value in %s.",
            env,
        )

    return secret


def _get_jwt_algorithm() -> str:
    """Get the JWT signing algorithm from environment or default."""
    return os.getenv("JWT_ALGORITHM", _DEFAULT_ALGORITHM).strip().upper()


def _build_keyset() -> Dict[str, Any]:
    algorithm = _get_jwt_algorithm()
    active_kid = os.getenv("JWT_ACTIVE_KID", "active").strip() or "active"
    previous_kid = os.getenv("JWT_PREVIOUS_KID", "").strip()

    if algorithm == "HS256":
        active_secret = _get_jwt_secret()
        previous_secret = os.getenv("JWT_PREVIOUS_SECRET", "").strip()
        verify = {active_kid: active_secret}
        if previous_kid and previous_secret:
            verify[previous_kid] = previous_secret
        return _build_keysetResult.model_validate({"algorithm": algorithm, "active_kid": active_kid, "signing_key": active_secret, "verify": verify})

    if algorithm in {"RS256", "ES256"}:
        active_private = os.getenv("JWT_PRIVATE_KEY_PEM", "").strip()
        active_public = os.getenv("JWT_PUBLIC_KEY_PEM", "").strip()
        previous_public = os.getenv("JWT_PREVIOUS_PUBLIC_KEY_PEM", "").strip()
        if not active_private:
            raise RuntimeError(f"JWT_PRIVATE_KEY_PEM is required when JWT_ALGORITHM={algorithm}")
        if not active_public:
            raise RuntimeError(f"JWT_PUBLIC_KEY_PEM is required when JWT_ALGORITHM={algorithm}")
        verify = {active_kid: active_public}
        if previous_kid and previous_public:
            verify[previous_kid] = previous_public
        return _build_keysetResult.model_validate({"algorithm": algorithm, "active_kid": active_kid, "signing_key": active_private, "verify": verify})

    raise RuntimeError(f"Unsupported JWT_ALGORITHM: {algorithm}")


def get_jwks() -> Dict[str, Any]:
    keyset = _build_keyset()
    alg = keyset["algorithm"]
    if alg not in {"RS256", "ES256"}:
        return get_jwksResult.model_validate({"keys": []})
    keys = []
    for kid, public_key in keyset["verify"].items():
        jwk_json = jwt.algorithms.get_default_algorithms()[alg].to_jwk(public_key)
        key_obj = json.loads(jwk_json)
        key_obj["kid"] = kid
        key_obj["alg"] = alg
        key_obj["use"] = "sig"
        keys.append(key_obj)
    return get_jwksResult.model_validate({"keys": keys})


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
    keyset = _build_keyset()
    algorithm = keyset["algorithm"]
    tenant_claim = os.getenv("JWT_TENANT_CLAIM", _DEFAULT_TENANT_CLAIM)
    user_claim = os.getenv("JWT_USER_CLAIM", _DEFAULT_USER_CLAIM)
    roles_claim = os.getenv("JWT_ROLES_CLAIM", _DEFAULT_ROLES_CLAIM)

    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        verify_keys = keyset["verify"]
        if kid and kid in verify_keys:
            candidates = [verify_keys[kid]]
        elif kid and kid not in verify_keys:
            logger.debug("JWT kid not recognized: %s", kid)
            return None
        else:
            candidates = list(verify_keys.values())
        payload = None
        for key in candidates:
            try:
                payload = jwt.decode(token, key, algorithms=[algorithm], options={"verify_exp": True})
                break
            except jwt.ExpiredSignatureError:
                raise
            except jwt.InvalidTokenError:
                continue
        if payload is None:
            return None
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

    # Extract standard claims
    exp = payload.get("exp")
    iat = payload.get("iat")
    jti = payload.get("jti")
    
    # Build extra_claims from remaining fields
    standard_claims = {tenant_claim, user_claim, roles_claim, "exp", "iat", "jti", "api_key_id"}
    extra: Dict[str, Any] = {k: v for k, v in payload.items() if k not in standard_claims}
    
    return TokenClaims(
        sub=payload.get(user_claim, ""),
        tenant_id=str(tenant_id) if tenant_id else None,
        roles=roles if isinstance(roles, list) else [roles] if roles else [],
        exp=exp if isinstance(exp, int) else None,
        iat=iat if isinstance(iat, int) else None,
        jti=jti if isinstance(jti, str) else None,
        extra_claims=extra,
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
    keyset = _build_keyset()
    algorithm = keyset["algorithm"]
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

    headers = {"kid": keyset["active_kid"]}
    return jwt.encode(payload, keyset["signing_key"], algorithm=algorithm, headers=headers)
