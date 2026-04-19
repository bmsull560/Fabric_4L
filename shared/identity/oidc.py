"""OIDC client and utilities."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .oidc_config import OIDCProviderConfig
from .permissions import Role

logger = logging.getLogger(__name__)


class OIDCClient:
    """Client for OIDC authentication flows."""

    def __init__(self, config: OIDCProviderConfig):
        self.config = config
        self._http_client = httpx.AsyncClient()

    async def get_authorization_url(
        self,
        state: str,
        code_challenge: str | None = None,
    ) -> str:
        """Get authorization URL for OIDC flow.

        Args:
            state: State parameter for CSRF protection
            code_challenge: PKCE code challenge

        Returns:
            Authorization URL
        """
        params = {
            "client_id": self.config.client_id,
            "response_type": "code",
            "scope": " ".join(self.config.scopes),
            "redirect_uri": str(self.config.redirect_uri),
            "state": state,
        }
        
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.config.authorization_endpoint}?{query}"

    async def exchange_code(
        self,
        code: str,
        code_verifier: str | None = None,
    ) -> dict[str, Any] | None:
        """Exchange authorization code for tokens.

        Args:
            code: Authorization code from callback
            code_verifier: PKCE code verifier

        Returns:
            Token response or None on failure
        """
        data = {
            "grant_type": "authorization_code",
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "code": code,
            "redirect_uri": str(self.config.redirect_uri),
        }

        if code_verifier:
            data["code_verifier"] = code_verifier

        try:
            response = await self._http_client.post(
                str(self.config.token_endpoint),
                data=data,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            return None

    async def get_userinfo(self, access_token: str) -> dict[str, Any] | None:
        """Get user info from UserInfo endpoint.

        Args:
            access_token: Access token

        Returns:
            User info or None on failure
        """
        if not self.config.userinfo_endpoint:
            return None

        try:
            response = await self._http_client.get(
                str(self.config.userinfo_endpoint),
                headers={"Authorization": f"Bearer {access_token}"},
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"UserInfo request failed: {e}")
            return None

    async def close(self):
        """Close HTTP client."""
        await self._http_client.aclose()


def map_role_from_claims(claims: dict[str, Any]) -> Role:
    """Map OIDC claims to system role.

    Args:
        claims: OIDC claims from ID token or UserInfo

    Returns:
        System role
    """
    # Check for admin claim
    role_claim = claims.get("role", "").lower()
    
    if "admin" in role_claim or "super" in role_claim:
        return Role.SUPER_ADMIN
    
    # Check groups if available
    groups = claims.get("groups", [])
    if isinstance(groups, str):
        groups = [groups]
    
    for group in groups:
        group_lower = group.lower()
        if "admin" in group_lower:
            return Role.TENANT_ADMIN
    
    return Role.USER
