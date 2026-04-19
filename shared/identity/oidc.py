"""OIDC client and utilities with PKCE support."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from urllib.parse import quote

import httpx
from jose import jwt
from jose.exceptions import JWTError

from .permissions import Role

logger = logging.getLogger(__name__)


class OIDCClient:
    """Client for OIDC authentication flows with discovery and PKCE support."""

    def __init__(self, timeout: float = 30.0, max_retries: int = 3) -> None:
        """Initialize OIDC client with HTTP client.

        Args:
            timeout: Request timeout in seconds (default: 30)
            max_retries: Maximum number of retries for failed requests (default: 3)
        """
        self._timeout = timeout
        self._max_retries = max_retries
        self._http_client = httpx.AsyncClient(timeout=timeout)

    async def discover(self, issuer_url: str) -> dict[str, Any]:
        """Discover OIDC provider metadata from well-known endpoint.

        Args:
            issuer_url: OIDC issuer URL

        Returns:
            Provider metadata dictionary

        Raises:
            httpx.HTTPError: If discovery fails after all retries
        """
        # Normalize issuer URL
        base_url = issuer_url.rstrip("/")
        well_known_url = f"{base_url}/.well-known/openid-configuration"

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.get(well_known_url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx client errors
                if 400 <= e.response.status_code < 500:
                    raise
                last_error = e
            except httpx.RequestError as e:
                last_error = e

            if attempt < self._max_retries - 1:
                # Exponential backoff: 1s, 2s, 4s
                delay = 2 ** attempt
                logger.warning(f"OIDC discovery failed (attempt {attempt + 1}), retrying in {delay}s: {last_error}")
                await asyncio.sleep(delay)

        raise last_error or httpx.RequestError(f"Failed to discover OIDC provider after {self._max_retries} attempts")

    def build_authorize_url(
        self,
        metadata: dict[str, Any],
        client_id: str,
        redirect_uri: str,
        state: str,
        nonce: str | None = None,
        scopes: list[str] | None = None,
        code_challenge: str | None = None,
        code_challenge_method: str = "S256",
    ) -> str:
        """Build authorization URL for OIDC flow.

        Args:
            metadata: OIDC provider metadata from discovery
            client_id: OAuth client ID
            redirect_uri: Redirect URI for callback
            state: State parameter for CSRF protection
            nonce: Nonce for replay attack protection
            scopes: Requested scopes
            code_challenge: PKCE code challenge
            code_challenge_method: PKCE method (default: S256)

        Returns:
            Authorization URL
        """
        auth_endpoint = metadata.get("authorization_endpoint", "")

        params: dict[str, str] = {
            "client_id": client_id,
            "response_type": "code",
            "scope": " ".join(scopes or ["openid", "profile", "email"]),
            "redirect_uri": redirect_uri,
            "state": state,
        }

        if nonce:
            params["nonce"] = nonce

        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = code_challenge_method

        # Properly URL-encode all parameters
        query = "&".join(f"{k}={quote(v, safe='')}" for k, v in params.items())
        return f"{auth_endpoint}?{query}"

    async def exchange_code(
        self,
        token_endpoint: str,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str | None = None,
        code_verifier: str | None = None,
    ) -> dict[str, Any]:
        """Exchange authorization code for tokens.

        Args:
            token_endpoint: OIDC token endpoint URL
            code: Authorization code from callback
            redirect_uri: Redirect URI used in authorize request
            client_id: OAuth client ID
            client_secret: OAuth client secret (optional for public clients)
            code_verifier: PKCE code verifier

        Returns:
            Token response dictionary

        Raises:
            httpx.HTTPError: If token exchange fails
        """
        data: dict[str, str] = {
            "grant_type": "authorization_code",
            "client_id": client_id,
            "code": code,
            "redirect_uri": redirect_uri,
        }

        if client_secret:
            data["client_secret"] = client_secret

        if code_verifier:
            data["code_verifier"] = code_verifier

        last_error: Exception | None = None
        for attempt in range(self._max_retries):
            try:
                response = await self._http_client.post(token_endpoint, data=data)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Don't retry on 4xx client errors (except 429 rate limit)
                if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                    raise
                last_error = e
            except httpx.RequestError as e:
                last_error = e

            if attempt < self._max_retries - 1:
                # Exponential backoff with jitter: 1s, 2s, 4s
                delay = 2 ** attempt
                logger.warning(f"Token exchange failed (attempt {attempt + 1}), retrying in {delay}s: {last_error}")
                await asyncio.sleep(delay)

        raise last_error or httpx.RequestError(f"Failed to exchange code after {self._max_retries} attempts")

    async def get_userinfo(self, userinfo_endpoint: str, access_token: str) -> dict[str, Any] | None:
        """Get user info from UserInfo endpoint.

        Args:
            userinfo_endpoint: UserInfo endpoint URL
            access_token: Access token

        Returns:
            User info or None on failure
        """
        try:
            response = await self._http_client.get(
                userinfo_endpoint,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"UserInfo request failed: {e}")
            return None

    async def verify_id_token(
        self,
        id_token: str,
        issuer_url: str,
        client_id: str,
    ) -> dict[str, Any]:
        """Verify and decode OIDC ID token.

        Args:
            id_token: ID token from token endpoint
            issuer_url: Expected issuer URL
            client_id: Expected audience (client ID)

        Returns:
            Decoded token claims

        Raises:
            ValueError: If token verification fails
        """
        try:
            # Get JWKS for key validation
            metadata = await self.discover(issuer_url)
            jwks_uri = metadata.get("jwks_uri")

            if jwks_uri:
                # Fetch signing keys
                jwks_response = await self._http_client.get(str(jwks_uri))
                jwks_response.raise_for_status()
                jwks = jwks_response.json()

                # Find the key used to sign the token
                unverified_header = jwt.get_unverified_header(id_token)
                kid = unverified_header.get("kid")

                signing_key = None
                for key in jwks.get("keys", []):
                    if key.get("kid") == kid:
                        signing_key = key
                        break

                if not signing_key:
                    raise ValueError(f"No matching signing key found for kid={kid}")

                # Verify with JWKS
                claims = jwt.decode(
                    id_token,
                    signing_key,
                    algorithms=["RS256"],
                    issuer=issuer_url,
                    audience=client_id,
                )
            else:
                raise ValueError("No JWKS URI in provider metadata, cannot verify token")

            return claims

        except JWTError as e:
            raise ValueError(f"Invalid ID token: {e}") from e
        except Exception as e:
            raise ValueError(f"Token verification failed: {e}") from e

    async def close(self) -> None:
        """Close HTTP client."""
        await self._http_client.aclose()


def map_role_from_claims(
    claims: dict[str, Any],
    claim_mapping: dict[str, str] | None = None,
    default_role: str | None = None,
) -> str:
    """Map OIDC claims to system role.

    Args:
        claims: OIDC claims from ID token or UserInfo
        claim_mapping: Optional mapping of claim names to role values
        default_role: Default role if no mapping matches

    Returns:
        Role string value
    """
    # Apply custom claim mapping if provided
    if claim_mapping:
        for claim_key, role_value in claim_mapping.items():
            claim_value = claims.get(claim_key)
            if claim_value:
                if isinstance(claim_value, list):
                    # Check if any value in list matches the expected role value
                    for val in claim_value:
                        if str(val).lower() == role_value.lower():
                            return role_value
                elif str(claim_value).lower() == role_value.lower():
                    return role_value

    # Check for admin claim
    role_claim = claims.get("role", "").lower()

    if "admin" in role_claim or "super" in role_claim:
        return "super_admin"

    # Check groups if available
    groups = claims.get("groups", [])
    if isinstance(groups, str):
        groups = [groups]

    for group in groups:
        group_lower = group.lower()
        if "admin" in group_lower:
            return "tenant_admin"

    # Return default role or user
    return default_role or "user"
