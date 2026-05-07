from __future__ import annotations

import json
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import jwt
from fastapi import HTTPException, status

from .models import TokenClaims
from .permissions import normalize_role_claims
from value_fabric.shared.models.typed_dict import TypedDictModel


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
_DEFAULT_INTERNAL_ISSUER = "value-fabric-internal"
_DEFAULT_INTERNAL_AUDIENCE = "value-fabric-services"

_DEVELOPMENT_ENVIRONMENTS = {"local", "dev", "development", "test", "testing", "ci"}
_ENV_KEYS = ("ENVIRONMENT", "ENV", "APP_ENV", "VF_ENV", "VALUE_FABRIC_ENV", "PYTHON_ENV")
_LEGACY_TEST_TENANT_ID_RE = re.compile(r"^tenant-[a-z0-9]+(?:-[a-z0-9]+)*$")


def _detect_environment() -> str:
    for key in _ENV_KEYS:
        value = os.getenv(key)
        if value and value.strip():
            return value.strip().lower()
    return "development"


def _is_non_dev_environment() -> bool:
    return _detect_environment() not in _DEVELOPMENT_ENVIRONMENTS


def _allow_legacy_test_tenant_ids() -> bool:
    explicit_test_flag = (
        os.getenv("ALLOW_LEGACY_TEST_TENANT_IDS", "").strip().lower() == "true"
        or os.getenv("TESTING", "").strip().lower() == "true"
    )
    pytest_runtime = bool(
        os.getenv("PYTEST_CURRENT_TEST", "").strip()
        or os.getenv("PYTEST_VERSION", "").strip()
    )
    return explicit_test_flag and (not _is_non_dev_environment() or pytest_runtime)


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
        logger.warning("JWT_SECRET is unset in %s; using local development fallback.", env)
        return _DEFAULT_JWT_SECRET

    if secret == _DEFAULT_JWT_SECRET:
        if is_non_dev:
            raise RuntimeError(
                "JWT_SECRET must not use the default value in non-development "
                f"environments. Detected environment: {env}."
            )
        logger.warning("JWT_SECRET is using the default development value in %s.", env)

    return secret


def _get_jwt_algorithm() -> str:
    return os.getenv("JWT_ALGORITHM", _DEFAULT_ALGORITHM).strip().upper()


def _get_revoked_kids() -> set[str]:
    return {kid.strip() for kid in os.getenv("JWT_REVOKED_KIDS", "").split(",") if kid.strip()}


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


def _resolve_external_key(header: Dict[str, Any], issuer: str) -> Optional[Any]:
    kid = header.get("kid")
    if not kid:
        return None
    if kid in _get_revoked_kids():
        return None
    jwks_raw = os.getenv("OIDC_JWKS_JSON", "").strip()
    if not jwks_raw:
        return None
    try:
        jwks = json.loads(jwks_raw)
    except json.JSONDecodeError:
        logger.warning("OIDC_JWKS_JSON is invalid JSON")
        return None
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.get_default_algorithms()[key.get("alg", "RS256")].from_jwk(json.dumps(key))
    logger.debug("No JWKS key found for kid=%s issuer=%s", kid, issuer)
    return None


def decode_jwt(token: str) -> Optional[TokenClaims]:
    keyset = _build_keyset()
    algorithm = keyset["algorithm"]
    tenant_claim = os.getenv("JWT_TENANT_CLAIM", _DEFAULT_TENANT_CLAIM)
    user_claim = os.getenv("JWT_USER_CLAIM", _DEFAULT_USER_CLAIM)
    roles_claim = os.getenv("JWT_ROLES_CLAIM", _DEFAULT_ROLES_CLAIM)
    internal_issuer = os.getenv("JWT_ISSUER", _DEFAULT_INTERNAL_ISSUER)
    internal_audience = os.getenv("JWT_AUDIENCE", _DEFAULT_INTERNAL_AUDIENCE)
    oidc_issuer = os.getenv("OIDC_ISSUER", "").strip()
    oidc_audience = os.getenv("OIDC_AUDIENCE", "").strip()

    try:
        header = jwt.get_unverified_header(token)
        unverified = jwt.decode(token, options={"verify_signature": False, "verify_exp": False})
        issuer = unverified.get("iss")
        audience = oidc_audience if oidc_issuer and issuer == oidc_issuer else internal_audience
        expected_issuer = oidc_issuer if oidc_issuer and issuer == oidc_issuer else internal_issuer

        if issuer != expected_issuer:
            logger.debug("Unexpected JWT issuer: %s", issuer)
            return None

        kid = header.get("kid")
        if kid and kid in _get_revoked_kids():
            logger.debug("JWT kid revoked: %s", kid)
            return None

        if expected_issuer == oidc_issuer:
            verify_key = _resolve_external_key(header, issuer)
            if verify_key is None:
                return None
            payload = jwt.decode(token, verify_key, algorithms=[header.get("alg", "RS256")], audience=audience, issuer=expected_issuer)
        else:
            verify_keys = keyset["verify"]
            if kid and kid in verify_keys:
                candidates = [verify_keys[kid]]
            elif kid and kid not in verify_keys:
                return None
            else:
                candidates = list(verify_keys.values())
            payload = None
            for key in candidates:
                try:
                    payload = jwt.decode(token, key, algorithms=[algorithm], audience=audience, issuer=expected_issuer)
                    break
                except jwt.ExpiredSignatureError:
                    raise
                except jwt.InvalidTokenError:
                    continue
            if payload is None:
                return None
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired.", headers={"WWW-Authenticate": "Bearer"})
    except jwt.InvalidTokenError:
        return None

    raw_tenant = payload.get(tenant_claim)
    if not raw_tenant:
        return None
    try:
        tenant_id: UUID | str = UUID(str(raw_tenant))
    except (ValueError, AttributeError):
        if _allow_legacy_test_tenant_ids() and _LEGACY_TEST_TENANT_ID_RE.fullmatch(str(raw_tenant)):
            tenant_id = str(raw_tenant)
        else:
            return None

    roles = payload.get(roles_claim, [])
    if not roles and payload.get("role"):
        roles = [payload.get("role")]
    if isinstance(roles, str):
        roles = [roles]
    roles = normalize_role_claims(roles)
    exp = payload.get("exp")
    iat = payload.get("iat")
    jti = payload.get("jti")
    standard_claims = {tenant_claim, user_claim, roles_claim, "role", "exp", "iat", "jti", "api_key_id"}
    extra: Dict[str, Any] = {k: v for k, v in payload.items() if k not in standard_claims}

    return TokenClaims(sub=payload.get(user_claim, ""), tenant_id=str(tenant_id) if tenant_id else None, roles=roles if isinstance(roles, list) else [roles] if roles else [], exp=exp if isinstance(exp, int) else None, iat=iat if isinstance(iat, int) else None, jti=jti if isinstance(jti, str) else None, extra_claims=extra)


def encode_jwt(
    tenant_id: UUID,
    *,
    user_id: Optional[str] = None,
    roles: Optional[List[str]] = None,
    api_key_id: Optional[str] = None,
    extra_claims: Optional[dict] = None,
    expires_in_seconds: int = 3600,
) -> str:
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
        "iss": os.getenv("JWT_ISSUER", _DEFAULT_INTERNAL_ISSUER),
        "aud": os.getenv("JWT_AUDIENCE", _DEFAULT_INTERNAL_AUDIENCE),
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
