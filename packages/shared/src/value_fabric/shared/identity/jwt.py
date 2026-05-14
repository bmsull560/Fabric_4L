from __future__ import annotations

import json
import logging
import os
import re
import threading
import time
from typing import Any, Dict, List, Optional
from uuid import UUID

import httpx
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
_DEFAULT_ORG_CLAIM = "org_id"
_DEFAULT_WORKSPACE_CLAIM = "workspace_id"
_DEFAULT_INTERNAL_ISSUER = "value-fabric-internal"
_DEFAULT_INTERNAL_AUDIENCE = "value-fabric-services"

# Keycloak integration defaults
_DEFAULT_KEYCLOAK_REALM = "fabric"
_DEFAULT_KEYCLOAK_JWKS_PATH = "/protocol/openid-connect/certs"

_DEVELOPMENT_ENVIRONMENTS = {"local", "dev", "development", "test", "testing", "ci"}
_ENV_KEYS = ("ENVIRONMENT", "ENV", "APP_ENV", "VF_ENV", "VALUE_FABRIC_ENV", "PYTHON_ENV")
_LEGACY_TEST_TENANT_ID_RE = re.compile(r"^tenant-[a-z0-9]+(?:-[a-z0-9]+)*$")
_TEST_RUNTIME_SENTINEL_KEYS = ("PYTEST_CURRENT_TEST", "PYTEST_VERSION", "VALUE_FABRIC_TEST_RUNTIME")
_PRODUCTION_LIKE_MARKER_KEYS = (
    "KUBERNETES_SERVICE_HOST",
    "K_SERVICE",
    "ECS_CONTAINER_METADATA_URI",
    "ECS_CONTAINER_METADATA_URI_V4",
    "AWS_EXECUTION_ENV",
    "DYNO",
)
_PRODUCTION_LIKE_ENVIRONMENTS = {"prod", "production", "staging", "stage", "preprod", "pre-production"}
_REQUIRED_REGISTERED_CLAIMS = ("exp", "iss", "aud")
_ALLOWED_EXTERNAL_ALGORITHMS = {"RS256", "ES256"}


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
    explicit_test_runtime = any(os.getenv(key, "").strip() for key in _TEST_RUNTIME_SENTINEL_KEYS)
    production_like_markers_present = any(
        os.getenv(key, "").strip() for key in _PRODUCTION_LIKE_MARKER_KEYS
    ) or _detect_environment() in _PRODUCTION_LIKE_ENVIRONMENTS
    allowed = explicit_test_flag and explicit_test_runtime and not production_like_markers_present
    if allowed:
        logger.warning(
            "legacy_tenant_id_mode_enabled",
            extra={
                "event": "legacy_tenant_id_mode_enabled",
                "component": "identity.jwt",
                "environment": _detect_environment(),
                "test_runtime_keys": [
                    key for key in _TEST_RUNTIME_SENTINEL_KEYS if os.getenv(key, "").strip()
                ],
            },
        )
    return allowed


def _get_jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()

    if not secret:
        raise RuntimeError(
            "JWT_SECRET is required and is currently unset. "
            "Set JWT_SECRET in your environment (for local development, copy "
            ".env.example to .env/.env.dev and provide a strong secret)."
        )

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


_JWKS_URL_CACHE: Dict[str, Any] = {}
_JWKS_URL_CACHE_EXPIRY: Dict[str, float] = {}
_JWKS_URL_CACHE_TTL_SECONDS = 300  # 5 minutes
_JWKS_URL_CACHE_LOCK = threading.Lock()


def _fetch_jwks_from_url(url: str, *, _hold_lock: bool = False) -> Optional[Dict[str, Any]]:
    """Fetch JWKS from a URL with thread-safe in-memory caching.

    Args:
        url: The JWKS endpoint URL.
        _hold_lock: Internal flag. When True the caller already holds
            ``_JWKS_URL_CACHE_LOCK``, so this function skips the cache-read
            check and the cache-write lock acquisition to avoid re-entrancy.
            Never pass this from outside ``_resolve_external_key``.
    """
    now = time.time()
    if not _hold_lock:
        with _JWKS_URL_CACHE_LOCK:
            cached = _JWKS_URL_CACHE.get(url)
            expiry = _JWKS_URL_CACHE_EXPIRY.get(url, 0)
            if cached and now < expiry:
                return cached
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(url, headers={"Accept": "application/json"})
            response.raise_for_status()
            jwks = response.json()
            if _hold_lock:
                # Caller holds the lock; write directly without re-acquiring.
                _JWKS_URL_CACHE[url] = jwks
                _JWKS_URL_CACHE_EXPIRY[url] = now + _JWKS_URL_CACHE_TTL_SECONDS
            else:
                with _JWKS_URL_CACHE_LOCK:
                    _JWKS_URL_CACHE[url] = jwks
                    _JWKS_URL_CACHE_EXPIRY[url] = now + _JWKS_URL_CACHE_TTL_SECONDS
            return jwks
    except Exception as exc:
        logger.warning("Failed to fetch JWKS from %s: %s", url, exc)
        return None


def _build_keycloak_jwks_url() -> Optional[str]:
    """Build Keycloak JWKS URL from KEYCLOAK_URL and KEYCLOAK_REALM."""
    keycloak_url = os.getenv("KEYCLOAK_URL", "").strip().rstrip("/")
    realm = os.getenv("KEYCLOAK_REALM", _DEFAULT_KEYCLOAK_REALM).strip()
    if keycloak_url and realm:
        return f"{keycloak_url}/realms/{realm}{_DEFAULT_KEYCLOAK_JWKS_PATH}"
    return None


def _find_key_in_jwks(jwks: Dict[str, Any], kid: str) -> Optional[Any]:
    """Return the PyJWT algorithm key object for the given kid, or None."""
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return jwt.algorithms.get_default_algorithms()[key.get("alg", "RS256")].from_jwk(json.dumps(key))
    return None


def _resolve_external_key(header: Dict[str, Any], issuer: str) -> Optional[Any]:
    kid = header.get("kid")
    if not kid:
        return None
    if kid in _get_revoked_kids():
        return None

    jwks: Optional[Dict[str, Any]] = None

    # Try static JWKS JSON first (no network, no cache invalidation needed)
    jwks_raw = os.getenv("OIDC_JWKS_JSON", "").strip()
    if jwks_raw:
        try:
            jwks = json.loads(jwks_raw)
        except json.JSONDecodeError:
            logger.warning("OIDC_JWKS_JSON is invalid JSON")

    if jwks is not None:
        result = _find_key_in_jwks(jwks, kid)
        if result is not None:
            return result
        # Static JWKS doesn't contain the kid — cannot refresh, fail closed.
        logger.debug("No JWKS key found for kid=%s in static OIDC_JWKS_JSON", kid)
        return None

    # Determine the URL source for dynamic fetching (explicit URL or Keycloak auto-build)
    jwks_url = os.getenv("OIDC_JWKS_URL", "").strip() or _build_keycloak_jwks_url()
    if not jwks_url:
        logger.debug("No JWKS URL configured; cannot resolve kid=%s", kid)
        return None

    # First attempt: use cached JWKS (lock is acquired inside _fetch_jwks_from_url)
    jwks = _fetch_jwks_from_url(jwks_url)
    if jwks is not None:
        result = _find_key_in_jwks(jwks, kid)
        if result is not None:
            return result

    # kid not found in cached JWKS — force a single cache-busting re-fetch.
    # Hold the lock for the entire evict+re-fetch sequence so that concurrent
    # requests carrying the same new kid don't all stampede the IdP at once.
    # The first thread to acquire the lock evicts and re-fetches; subsequent
    # threads find the fresh entry already in the cache.
    logger.debug("kid=%s not in cached JWKS; forcing re-fetch from %s", kid, jwks_url)
    with _JWKS_URL_CACHE_LOCK:
        # Re-check under the lock: another thread may have already refreshed.
        cached = _JWKS_URL_CACHE.get(jwks_url)
        expiry = _JWKS_URL_CACHE_EXPIRY.get(jwks_url, 0)
        if cached and time.time() < expiry:
            result = _find_key_in_jwks(cached, kid)
            if result is not None:
                return result
        # Still not present — evict and fetch. Pass _hold_lock=True so the
        # fetch skips re-acquiring the lock we already hold.
        _JWKS_URL_CACHE.pop(jwks_url, None)
        _JWKS_URL_CACHE_EXPIRY.pop(jwks_url, None)
        jwks = _fetch_jwks_from_url(jwks_url, _hold_lock=True)

    if jwks is not None:
        result = _find_key_in_jwks(jwks, kid)
        if result is not None:
            return result

    logger.debug("No JWKS key found for kid=%s issuer=%s after cache refresh", kid, issuer)
    return None


def decode_jwt(token: str) -> Optional[TokenClaims]:
    tenant_claim = os.getenv("JWT_TENANT_CLAIM", _DEFAULT_TENANT_CLAIM)
    user_claim = os.getenv("JWT_USER_CLAIM", _DEFAULT_USER_CLAIM)
    roles_claim = os.getenv("JWT_ROLES_CLAIM", _DEFAULT_ROLES_CLAIM)
    internal_issuer = os.getenv("JWT_ISSUER", _DEFAULT_INTERNAL_ISSUER)
    internal_audience = os.getenv("JWT_AUDIENCE", _DEFAULT_INTERNAL_AUDIENCE)
    oidc_issuer = os.getenv("OIDC_ISSUER", "").strip()
    oidc_audience = os.getenv("OIDC_AUDIENCE", "").strip()

    try:
        header = jwt.get_unverified_header(token)
        unverified = jwt.decode(
            token,
            options={
                "verify_signature": False,
                "verify_exp": False,
                "verify_aud": False,
                "verify_iss": False,
                "verify_iat": False,
                "verify_nbf": False,
            },
        )
        header_alg = str(header.get("alg", "")).strip().upper()
        if not header_alg:
            return None
        issuer = unverified.get("iss")
        if any(unverified.get(claim) in (None, "") for claim in _REQUIRED_REGISTERED_CLAIMS):
            return None
        audience = oidc_audience if oidc_issuer and issuer == oidc_issuer else internal_audience
        expected_issuer = oidc_issuer if oidc_issuer and issuer == oidc_issuer else internal_issuer

        if expected_issuer is not None and issuer != expected_issuer:
            logger.debug("Unexpected JWT issuer: %s", issuer)
            return None

        kid = header.get("kid")
        if kid and kid in _get_revoked_kids():
            logger.debug("JWT kid revoked: %s", kid)
            return None

        payload: Dict[str, Any]
        if expected_issuer == oidc_issuer:
            if header_alg not in _ALLOWED_EXTERNAL_ALGORITHMS:
                return None
            verify_key = _resolve_external_key(header, issuer)
            if verify_key is None:
                return None
            payload = jwt.decode(
                token,
                verify_key,
                algorithms=[header_alg],
                audience=audience,
                issuer=expected_issuer,
                options={
                    "require": list(_REQUIRED_REGISTERED_CLAIMS),
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                },
            )
        else:
            keyset = _build_keyset()
            algorithm = keyset["algorithm"]
            if header_alg != algorithm:
                return None
            decode_kwargs: Dict[str, Any] = {
                "algorithms": [algorithm],
                "audience": audience,
                "issuer": expected_issuer,
                "options": {
                    "require": list(_REQUIRED_REGISTERED_CLAIMS),
                    "verify_exp": True,
                    "verify_aud": True,
                    "verify_iss": True,
                    "verify_iat": True,
                    "verify_nbf": True,
                },
            }
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
                    payload = jwt.decode(token, key, **decode_kwargs)
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
    org_claim = os.getenv("JWT_ORG_CLAIM", _DEFAULT_ORG_CLAIM)
    workspace_claim = os.getenv("JWT_WORKSPACE_CLAIM", _DEFAULT_WORKSPACE_CLAIM)
    standard_claims = {
        tenant_claim, user_claim, roles_claim, org_claim, workspace_claim,
        "role", "exp", "iat", "jti", "api_key_id", "email", "name", "impersonator_id",
    }
    extra: Dict[str, Any] = {k: v for k, v in payload.items() if k not in standard_claims}

    return TokenClaims(
        sub=payload.get(user_claim, ""),
        tenant_id=str(tenant_id) if tenant_id else None,
        org_id=payload.get(org_claim),
        workspace_id=payload.get(workspace_claim),
        roles=roles if isinstance(roles, list) else [roles] if roles else [],
        email=payload.get("email"),
        name=payload.get("name"),
        impersonator_id=payload.get("impersonator_id"),
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
