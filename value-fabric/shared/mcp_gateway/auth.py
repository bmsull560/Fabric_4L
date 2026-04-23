"""OAuth 2.1 + PKCE authentication handler for MCP tools.

Implements the authorization code flow with PKCE extension as required
for secure tool authentication in multi-tenant environments.

Reference:
    - OAuth 2.1: https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1
    - PKCE: https://datatracker.ietf.org/doc/html/rfc7636
"""

from __future__ import annotations

import base64
import hashlib
import logging
import secrets
import urllib.parse
from dataclasses import dataclass
from typing import Any

import httpx

from .types import (
    AuthenticationError,
    OAuthClientConfig,
    PKCEChallenge,
    TokenEndpointAuthMethod,
)

logger = logging.getLogger(__name__)


class PKCEVerifier:
    """Generate and verify PKCE challenges.
    
    PKCE prevents authorization code interception attacks by binding
the authorization request to the token request via a code verifier.
    """
    
    @staticmethod
    def generate_challenge() -> PKCEChallenge:
        """Generate a new PKCE challenge.
        
        Creates a code verifier (random string) and derives the
        code_challenge (SHA256 hash of verifier).
        
        Returns:
            PKCEChallenge with verifier and challenge
            
        Example:
            >>> challenge = PKCEVerifier.generate_challenge()
            >>> print(challenge.code_challenge_method)  # "S256"
        """
        # Code verifier: 43-128 chars, [A-Z] / [a-z] / [0-9] / "-" / "." / "_" / "~"
        code_verifier = base64.urlsafe_b64encode(
            secrets.token_bytes(32)
        ).decode("ascii").rstrip("=")
        
        # Code challenge: BASE64URL(SHA256(code_verifier))
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")
        
        return PKCEChallenge(
            code_verifier=code_verifier,
            code_challenge=code_challenge,
            code_challenge_method="S256"
        )
    
    @staticmethod
    def verify_challenge(verifier: str, challenge: str) -> bool:
        """Verify a code challenge against a verifier.
        
        Args:
            verifier: The code verifier
            challenge: The expected code challenge
            
        Returns:
            True if verifier produces the expected challenge
        """
        expected = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).decode("ascii").rstrip("=")
        return secrets.compare_digest(expected, challenge)


@dataclass
class TokenResponse:
    """OAuth 2.1 token response.
    
    Attributes:
        access_token: The access token
        token_type: Token type (e.g., "Bearer")
        expires_in: Token lifetime in seconds
        refresh_token: Optional refresh token
        scope: Granted scopes
    """
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str | None = None
    scope: str | None = None


class OAuthHandler:
    """Handle OAuth 2.1 + PKCE flows for MCP tool authentication.
    
    This handler manages the complete OAuth flow:
    1. Generate PKCE challenge
    2. Build authorization URL with PKCE
    3. Exchange authorization code for access token
    4. Refresh access tokens
    
    Example:
        >>> handler = OAuthHandler(OAuthClientConfig(
        ...     client_id="mcp_client",
        ...     authorization_endpoint="https://auth.example.com/authorize",
        ...     token_endpoint="https://auth.example.com/token",
        ...     redirect_uri="https://tools.example.com/callback",
        ...     scopes=["tools:read", "tools:execute"]
        ... ))
        >>> url, challenge = handler.get_authorization_url()
        >>> # Redirect user to url, get code from callback
        >>> token = await handler.exchange_code(code, challenge)
    """
    
    def __init__(self, config: OAuthClientConfig):
        """Initialize with OAuth client configuration.
        
        Args:
            config: OAuth client registration details
        """
        self.config = config
        self._pkce_verifier = PKCEVerifier()
        self._http_client = httpx.AsyncClient(timeout=30.0)
    
    def get_authorization_url(
        self,
        state: str | None = None,
        additional_params: dict[str, str] | None = None
    ) -> tuple[str, PKCEChallenge]:
        """Build OAuth authorization URL with PKCE.
        
        Args:
            state: Optional state parameter for CSRF protection
            additional_params: Additional query parameters
            
        Returns:
            Tuple of (authorization_url, pkce_challenge)
            Store the challenge securely - needed for token exchange!
            
        Example:
            >>> url, challenge = handler.get_authorization_url(
            ...     state=str(uuid.uuid4())
            ... )
            >>> # Redirect user to url
            >>> # After callback: exchange_code(code, challenge)
        """
        challenge = self._pkce_verifier.generate_challenge()
        
        params = {
            "response_type": "code",
            "client_id": self.config.client_id,
            "redirect_uri": self.config.redirect_uri,
            "code_challenge": challenge.code_challenge,
            "code_challenge_method": challenge.code_challenge_method,
        }
        
        if self.config.scopes:
            params["scope"] = " ".join(self.config.scopes)
        
        if state:
            params["state"] = state
        
        if additional_params:
            params.update(additional_params)
        
        query = urllib.parse.urlencode(params)
        authorization_url = f"{self.config.authorization_endpoint}?{query}"
        
        logger.debug("Generated authorization URL with PKCE challenge")
        return authorization_url, challenge
    
    async def exchange_code(
        self,
        authorization_code: str,
        challenge: PKCEChallenge
    ) -> TokenResponse:
        """Exchange authorization code for access token.
        
        Args:
            authorization_code: Code received from authorization callback
            challenge: PKCE challenge used in authorization request
            
        Returns:
            TokenResponse with access token
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.config.redirect_uri,
            "code_verifier": challenge.code_verifier,
        }
        
        # OAuth 2.1 requires client_id in token request for public clients
        if not self.config.client_secret:
            data["client_id"] = self.config.client_id
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        try:
            response = await self._http_client.post(
                self.config.token_endpoint,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Successfully exchanged authorization code for access token")
            return TokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope")
            )
            
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = f" - {error_body.get('error_description', error_body.get('error', ''))}"
            except Exception:
                pass
            logger.error(f"Token exchange failed: {e}{error_detail}")
            raise AuthenticationError(
                f"Failed to exchange authorization code: {e}{error_detail}"
            ) from e
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise AuthenticationError(f"Failed to exchange authorization code: {e}") from e
    
    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        """Refresh an expired access token.
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            TokenResponse with new access token
            
        Raises:
            AuthenticationError: If refresh fails
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        
        if not self.config.client_secret:
            data["client_id"] = self.config.client_id
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        try:
            response = await self._http_client.post(
                self.config.token_endpoint,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            token_data = response.json()
            
            logger.info("Successfully refreshed access token")
            return TokenResponse(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_in=token_data.get("expires_in", 3600),
                refresh_token=token_data.get("refresh_token"),
                scope=token_data.get("scope")
            )
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise AuthenticationError(f"Failed to refresh token: {e}") from e
    
    async def close(self) -> None:
        """Close HTTP client connections."""
        await self._http_client.aclose()
