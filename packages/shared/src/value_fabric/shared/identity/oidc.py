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
            if part in current:
                current = current.get(part)
            else:
                lowered = part.lower()
                current = next(
                    (value for key, value in current.items() if str(key).lower() == lowered),
                    None,
                )
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
        return expected_value.lower() in [str(v).lower() for v in actual_value]

    return str(actual_value).lower() == expected_value.lower()


def map_role_from_claims(
    claims: dict,
    claim_mapping: Optional[Dict[str, str]] = None,
    default_role: str = "user",
) -> str:
    """Map OIDC claims to the highest-privilege VF role.

    claim_mapping keys may use dot notation for nested claims.
    Keys can be either:
      - ``claim_path`` → role (matches any truthy value)
      - ``claim_path=expected_value`` → role (exact/array/regex match)
    Values are the target VF Role strings.
    """
    matched_roles: List[str] = []
    claim_mapping = claim_mapping or {}

    if not claim_mapping:
        role_claim = claims.get("role")
        if isinstance(role_claim, str) and role_claim in _ROLE_PRIVILEGE:
            return role_claim

        groups = claims.get("groups")
        group_values = [groups] if isinstance(groups, str) else list(groups or [])
        normalized_groups = {str(group).strip().lower() for group in group_values}
        if "admin" in normalized_groups or "tenant_admin" in normalized_groups:
            return Role.TENANT_ADMIN.value

        return default_role

    for key, role in claim_mapping.items():
        if "=" in key:
            claim_path, expected_value = key.split("=", 1)
        else:
            claim_path = key
            expected_value = role

        actual_value = _get_nested_claim(claims, claim_path)
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
        self._http_client = self._http

    async def discover(self, issuer_url: str) -> dict:
        """Fetch OpenID Provider metadata from well-known endpoint."""
        well_known = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
        try:
            response = await self._http_client.get(well_known)
        except httpx.HTTPStatusError as exc:
            if getattr(exc.response, "status_code", 0) < 500:
                raise
            response = await self._http_client.get(well_known)
        except Exception:
            response = await self._http_client.get(well_known)
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
            response = await self._http_client.get(jwks_uri)
            response.raise_for_status()
            jwks_data = response.json()
            _JWKS_CACHE[cache_key] = {"jwks": jwks_data, "fetched_at": now}

        # Use PyJWKClient to select the right key
        PyJWKClient(uri="", cache_keys=False)
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
        # SECURITY: Two-step OIDC token verification per RFC 7517/7519
        # Step 1: Unverified decode to extract key ID (kid) for key lookup
        # Step 2: Verified decode with fetched signing key validates signature and claims
        # nosec B105 - unverified decode is immediately followed by verified decode
        unverified = jwt.decode(
            id_token,
            options={"verify_signature": False, "verify_exp": False},
        )
        kid = unverified.get("kid")
        signing_key = await self.get_signing_key(issuer_url, kid=kid)

        # Step 2: Verified decode with proper signature and claim validation
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
        nonce: Optional[str] = None,
        scopes: Optional[List[str]] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[str] = None,
    ) -> str:
        """Construct the OIDC authorization endpoint URL."""
        auth_endpoint = metadata["authorization_endpoint"]
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": " ".join(scopes or ["openid", "profile", "email"]),
        }
        if nonce:
            params["nonce"] = nonce
        if code_challenge:
            params["code_challenge"] = code_challenge
        if code_challenge_method:
            params["code_challenge_method"] = code_challenge_method
        sep = "&" if "?" in auth_endpoint else "?"
        return auth_endpoint + sep + urlencode(params)

    async def exchange_code(
        self,
        token_endpoint: str,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        code_verifier: Optional[str] = None,
    ) -> dict:
        """Exchange an authorization code for tokens."""
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        response = await self._http_client.post(
            token_endpoint,
            data=data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        return response.json()

    async def get_userinfo(self, userinfo_endpoint: str, access_token: str) -> dict:
        """Fetch user information from the UserInfo endpoint.

        Args:
            userinfo_endpoint: The UserInfo endpoint URL
            access_token: Valid access token

        Returns:
            User claims dictionary
        """
        response = await self._http_client.get(
            userinfo_endpoint,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        return response.json()
