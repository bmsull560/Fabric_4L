"""OIDC client for discovery, JWKS caching, and claim mapping."""

from __future__ import annotations

import logging
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
import jwt
from jwt import PyJWKClient

from .oidc_config import OIDCProviderConfig
from .permissions import Role

logger = logging.getLogger(__name__)

_JWKS_CACHE: Dict[str, Dict[str, Any]] = {}
_JWKS_TTL_SECONDS = 3600

_ROLE_PRIVILEGE: Dict[str, int] = {
    Role.READ_ONLY.value: 1,
    Role.ANALYST.value: 2,
    Role.CONTENT_ADMIN.value: 3,
    Role.TENANT_ADMIN.value: 4,
    Role.SUPER_ADMIN.value: 5,
    Role.SYSTEM.value: 6,
}


def _get_nested_claim(claims: dict, path: str) -> Any:
    """Retrieve a nested claim value using dot notation (e.g., 'groups.value')."""
    parts = path.split(".")
    current: Any = claims
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _match_claim_value(actual_value: Any, expected_value: str) -> bool:
    """Check if actual claim value matches expected pattern.

    Supports:
    - Exact string match
    - Array membership (if actual is a list)
    - Regex match (if expected is wrapped in /.../)
    """
    if actual_value is None:
        return False

    # Regex pattern: /pattern/
    if expected_value.startswith("/") and expected_value.endswith("/") and len(expected_value) > 1:
        pattern = expected_value[1:-1]
        try:
            compiled = re.compile(pattern)
        except re.error:
            return False
        if isinstance(actual_value, list):
            return any(bool(compiled.search(str(v))) for v in actual_value)
        return bool(compiled.search(str(actual_value)))

    if isinstance(actual_value, list):
        return expected_value in [str(v) for v in actual_value]

    return str(actual_value) == expected_value


def map_role_from_claims(claims: dict, claim_mapping: Dict[str, str], default_role: str) -> str:
    """Map OIDC claims to the highest-privilege VF role.

    claim_mapping keys may use dot notation for nested claims.
    Keys can be either:
      - ``claim_path`` → role (matches any truthy value)
      - ``claim_path=expected_value`` → role (exact/array/regex match)
    Values are the target VF Role strings.
    """
    matched_roles: List[str] = []

    for key, role in claim_mapping.items():
        if "=" in key:
            claim_path, expected_value = key.split("=", 1)
        else:
            claim_path = key
            expected_value = None

        actual_value = _get_nested_claim(claims, claim_path)
        if expected_value is None:
            if actual_value:
                matched_roles.append(role)
        else:
            if _match_claim_value(actual_value, expected_value):
                matched_roles.append(role)

    if not matched_roles:
        return default_role

    # Return highest privilege match
    def _privilege(role: str) -> int:
        return _ROLE_PRIVILEGE.get(role, 0)

    return max(matched_roles, key=_privilege)


class OIDCClient:
    """Async OIDC client with in-memory JWKS caching."""

    def __init__(self, http_client: Optional[httpx.AsyncClient] = None) -> None:
        self._http = http_client or httpx.AsyncClient(timeout=30.0, follow_redirects=True)

    async def discover(self, issuer_url: str) -> dict:
        """Fetch OpenID Provider metadata from well-known endpoint."""
        well_known = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
        response = await self._http.get(well_known)
        response.raise_for_status()
        return response.json()

    def _get_jwks_uri(self, issuer_url: str, metadata: Optional[dict] = None) -> str:
        """Return JWKS URI from cached metadata or discovery."""
        if metadata and "jwks_uri" in metadata:
            return metadata["jwks_uri"]
        return issuer_url.rstrip("/") + "/.well-known/jwks"

    async def get_signing_key(self, issuer_url: str, kid: Optional[str] = None) -> Any:
        """Fetch or return cached signing key for the issuer."""
        now = time.time()
        cache_key = issuer_url.rstrip("/")
        cached = _JWKS_CACHE.get(cache_key)

        if cached and (now - cached["fetched_at"]) < _JWKS_TTL_SECONDS:
            jwks_data = cached["jwks"]
        else:
            metadata = await self.discover(cache_key)
            jwks_uri = self._get_jwks_uri(cache_key, metadata)
            response = await self._http.get(jwks_uri)
            response.raise_for_status()
            jwks_data = response.json()
            _JWKS_CACHE[cache_key] = {"jwks": jwks_data, "fetched_at": now}

        # Use PyJWKClient to select the right key
        jwk_client = PyJWKClient(uri="", cache_keys=False)
        # PyJWKClient expects a URI it can fetch; we bypass by feeding the keys directly
        # but the public API is limited. Instead, parse manually.
        keys = jwks_data.get("keys", [])
        if not keys:
            raise jwt.InvalidTokenError("No JWKS keys found")

        for key in keys:
            if kid is None or key.get("kid") == kid:
                return jwt.api_jwk.PyJWK(key)

        # Fallback: return first key if kid not specified and no match
        return jwt.api_jwk.PyJWK(keys[0])

    async def verify_id_token(
        self,
        id_token: str,
        issuer_url: str,
        client_id: str,
    ) -> dict:
        """Verify an OIDC id_token signature and claims.

        Returns the decoded token claims as a dict.
        Raises jwt.InvalidTokenError or jwt.ExpiredSignatureError on failure.
        """
        unverified = jwt.decode(
            id_token,
            options={"verify_signature": False, "verify_exp": False},
        )
        kid = unverified.get("kid")
        signing_key = await self.get_signing_key(issuer_url, kid=kid)

        payload = jwt.decode(
            id_token,
            key=signing_key.key,
            algorithms=["RS256", "ES256"],
            issuer=issuer_url.rstrip("/"),
            audience=client_id,
            options={"verify_exp": True},
        )
        return payload

    def build_authorize_url(
        self,
        metadata: dict,
        client_id: str,
        redirect_uri: str,
        state: str,
        nonce: str,
        scopes: List[str],
    ) -> str:
        """Construct the OIDC authorization endpoint URL."""
        auth_endpoint = metadata["authorization_endpoint"]
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "nonce": nonce,
            "scope": " ".join(scopes),
        }
        sep = "&" if "?" in auth_endpoint else "?"
        return auth_endpoint + sep + urlencode(params)

    async def exchange_code(
        self,
        token_endpoint: str,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
    ) -> dict:
        """Exchange an authorization code for tokens."""
        response = await self._http.post(
            token_endpoint,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()
