"""RFC 8693 Token Exchange implementation for tool delegation.

Implements OAuth 2.0 Token Exchange (RFC 8693) to enable tools to delegate
their permissions to other tools, creating an audit trail of tool-to-tool calls.

Reference:
    - RFC 8693: https://tools.ietf.org/html/rfc8693
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import httpx

from .types import DelegatedToken, GatewayError

logger = logging.getLogger(__name__)


class TokenExchangeError(GatewayError):
    """Raised when token exchange fails."""
    pass


class TokenExchanger:
    """RFC 8693 Token Exchange handler for tool delegation.
    
    Enables a tool (or the agent runtime) to obtain a security token
    that represents the identity of the subject, but with a different
    set of permissions scoped to a specific tool invocation.
    
    This creates an audit trail where:
    1. User token is exchanged for tool-scoped token
    2. Tool uses delegated token (not original user token)
    3. Audit logs show both subject (user) and actor (tool)
    
    Example:
        >>> exchanger = TokenExchanger("https://auth.example.com/token")
        >>> delegated = await exchanger.exchange_token(
        ...     subject_token=user_token,
        ...     subject_token_type="urn:ietf:params:oauth:token-type:access_token",
        ...     tool_name="search_tool",
        ...     tenant_id=tenant_uuid,
        ...     requested_token_type="urn:ietf:params:oauth:token-type:access_token"
        ... )
        >>> # Use delegated.access_token for tool invocation
    """
    
    def __init__(
        self,
        token_endpoint: str,
        client_id: str | None = None,
        client_secret: str | None = None
    ):
        """Initialize token exchanger.
        
        Args:
            token_endpoint: OAuth token endpoint URL
            client_id: Optional client ID for authentication
            client_secret: Optional client secret
        """
        self.token_endpoint = token_endpoint
        self.client_id = client_id
        self.client_secret = client_secret
        self._http_client = httpx.AsyncClient(timeout=30.0)
    
    async def exchange_token(
        self,
        subject_token: str,
        subject_token_type: str,
        tool_name: str,
        tenant_id: UUID,
        user_id: str | None = None,
        requested_token_type: str = "urn:ietf:params:oauth:token-type:access_token",
        scope: str | None = None,
        resource: str | None = None,
        audience: str | None = None,
        additional_claims: dict[str, Any] | None = None,
    ) -> DelegatedToken:
        """Exchange a subject token for a tool-scoped token.
        
        Args:
            subject_token: The original user's access token
            subject_token_type: Token type (e.g., access_token)
            tool_name: Name of the tool to be invoked (scopes access)
            tenant_id: Tenant ID for tenant attribution
            user_id: User ID for audit trail
            requested_token_type: Type of token to request
            scope: Requested scope (limited to tool's required scopes)
            resource: URI of the target resource
            audience: Intended audience for the token
            additional_claims: Extra claims to include in token
            
        Returns:
            DelegatedToken with scoped access token
            
        Raises:
            TokenExchangeError: If exchange fails
            
        Example:
            >>> delegated = await exchanger.exchange_token(
            ...     subject_token=user_access_token,
            ...     subject_token_type="urn:ietf:params:oauth:token-type:access_token",
            ...     tool_name="database_query",
            ...     tenant_id=tenant_uuid,
            ...     scope="tools:query:readonly"
            ... )
        """
        # RFC 8693 token exchange parameters
        data: dict[str, Any] = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token": subject_token,
            "subject_token_type": subject_token_type,
            "requested_token_type": requested_token_type,
        }
        
        # Add optional parameters
        if scope:
            data["scope"] = scope
        if resource:
            data["resource"] = resource
        if audience:
            data["audience"] = audience
        
        # Build actor token (representing the tool/runtime)
        actor_token_data = {
            "tool_name": tool_name,
            "tenant_id": str(tenant_id),
            "delegation_type": "tool_invocation",
            "subject_user_id": user_id,
        }
        
        if additional_claims:
            actor_token_data.update(additional_claims)
        
        # Actor token identifies the delegating party (the tool/runtime)
        # In a full implementation, this would be a JWT signed by the platform
        data["actor_token"] = self._create_actor_token(actor_token_data)
        data["actor_token_type"] = "urn:ietf:params:oauth:token-type:jwt"
        
        # Add client authentication if configured
        if self.client_id:
            data["client_id"] = self.client_id
        if self.client_secret:
            data["client_secret"] = self.client_secret
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        
        try:
            response = await self._http_client.post(
                self.token_endpoint,
                data=data,
                headers=headers
            )
            response.raise_for_status()
            token_data = response.json()
            
            # Parse expires_in to calculate expiration time
            expires_in = token_data.get("expires_in", 3600)
            expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            
            logger.info(
                f"Token exchange successful for tool '{tool_name}'",
                extra={
                    "tool_name": tool_name,
                    "tenant_id": str(tenant_id),
                    "subject_token_id": token_data.get("sub"),
                }
            )
            
            return DelegatedToken(
                access_token=token_data["access_token"],
                token_type=token_data.get("token_type", "Bearer"),
                expires_at=expires_at,
                scope=token_data.get("scope", scope or ""),
                subject_token_id=str(uuid4())[:8],  # Truncated for tracking
                tool_name=tool_name,
            )
            
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_body = e.response.json()
                error_detail = f" - {error_body.get('error_description', error_body.get('error', ''))}"
            except Exception:
                pass
            logger.error(f"Token exchange failed: {e}{error_detail}")
            raise TokenExchangeError(
                f"Failed to exchange token for tool '{tool_name}': {e}{error_detail}"
            ) from e
        except Exception as e:
            logger.error(f"Token exchange failed: {e}")
            raise TokenExchangeError(
                f"Failed to exchange token for tool '{tool_name}': {e}"
            ) from e
    
    def _create_actor_token(self, claims: dict[str, Any]) -> str:
        """Create a simple actor token for the delegation.
        
        In production, this should be a proper JWT signed with the platform's
        private key. For now, we create a placeholder that includes the claims.
        
        Args:
            claims: Claims to include in the actor token
            
        Returns:
            Actor token string (JWT in production)
        """
        # Placeholder: In production, sign a JWT with platform key
        # import jwt
        # return jwt.encode(claims, private_key, algorithm="RS256")
        
        # For now, return a base64-encoded JSON (not for production!)
        import base64
        import json
        payload = json.dumps(claims).encode()
        return base64.urlsafe_b64encode(payload).decode().rstrip("=")
    
    async def close(self) -> None:
        """Close HTTP client connections."""
        await self._http_client.aclose()
