"""Type definitions for MCP Gateway.

Defines data models for tool requests, responses, manifests, and tokens.
All types are Pydantic models for validation and serialization.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID


class GatewayError(Exception):
    """Base exception for MCP Gateway errors."""
    pass


class AuthenticationError(GatewayError):
    """Raised when tool authentication fails."""
    pass


class ManifestValidationError(GatewayError):
    """Raised when tool manifest signature is invalid."""
    pass


class ToolAccessDeniedError(GatewayError):
    """Raised when tenant is not authorized to use a tool."""
    pass


@dataclass
class ToolRequest:
    """Request to invoke a tool.
    
    Attributes:
        tool_name: Unique identifier for the tool
        parameters: Tool-specific parameters
        tenant_id: UUID of the tenant making the request
        user_id: Optional user ID for audit trail
        request_id: Unique request ID for tracing
        parent_span_id: Optional parent span for distributed tracing
    """
    tool_name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    tenant_id: UUID | None = None
    user_id: str | None = None
    request_id: str | None = None
    parent_span_id: str | None = None


@dataclass
class ToolResponse:
    """Response from tool invocation.
    
    Attributes:
        tool_name: Tool that was invoked
        result: Tool output data
        error: Error message if invocation failed
        execution_time_ms: Duration of tool execution
        request_id: Request ID for correlation
        audit_event_id: ID of emitted audit event
    """
    tool_name: str
    result: dict[str, Any] | None = None
    error: str | None = None
    execution_time_ms: float = 0.0
    request_id: str | None = None
    audit_event_id: str | None = None
    
    @property
    def success(self) -> bool:
        """True if tool invocation succeeded."""
        return self.error is None


@dataclass
class ToolManifest:
    """Tool manifest defining tool capabilities and security properties.
    
    Manifests are signed with JWS to ensure integrity and provenance.
    ETDI (External Tool Description with Integrity) format.
    
    Attributes:
        tool_name: Unique tool identifier
        version: Semantic version of the tool
        description: Human-readable description
        endpoint: URL where tool is hosted
        capabilities: List of capability strings
        required_scopes: OAuth scopes required to use this tool
        signature: JWS signature of the manifest
        tenant_scoped: Whether tool supports per-tenant isolation
    """
    tool_name: str
    version: str
    description: str
    endpoint: str
    capabilities: list[str] = field(default_factory=list)
    required_scopes: list[str] = field(default_factory=list)
    signature: str | None = None
    tenant_scoped: bool = True
    
    def verify_signature(self, public_key: str) -> bool:
        """Verify the JWS signature of this manifest.
        
        Args:
            public_key: PEM-encoded public key for verification
            
        Returns:
            True if signature is valid
        """
        # Implementation in ManifestVerifier
        from .manifest import ManifestVerifier
        return ManifestVerifier.verify_manifest(self, public_key)


@dataclass
class DelegatedToken:
    """Token issued via RFC 8693 Token Exchange for tool delegation.
    
    Short-lived token scoped to a specific tool invocation,
    enabling tools to call other tools with limited permissions.
    
    Attributes:
        access_token: The delegated access token
        token_type: Token type (usually "Bearer")
        expires_at: Expiration timestamp
        scope: Granted scopes (limited to tool requirements)
        subject_token_id: ID of original user token
        tool_name: Tool this token is scoped for
    """
    access_token: str
    token_type: str = "Bearer"
    expires_at: datetime | None = None
    scope: str = ""
    subject_token_id: str | None = None
    tool_name: str | None = None
    
    @property
    def is_expired(self) -> bool:
        """Check if token has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class PKCEChallenge:
    """PKCE (Proof Key for Code Exchange) challenge data.
    
    Used in OAuth 2.1 PKCE flow to prevent authorization code interception.
    
    Attributes:
        code_verifier: Cryptographically random verifier
        code_challenge: SHA256 hash of verifier (sent to auth server)
        code_challenge_method: Method used (always "S256")
    """
    code_verifier: str
    code_challenge: str
    code_challenge_method: str = "S256"


class TokenEndpointAuthMethod(str, Enum):
    """Client authentication methods for token endpoint."""
    NONE = "none"  # PKCE flow (no client secret)
    CLIENT_SECRET_BASIC = "client_secret_basic"
    CLIENT_SECRET_POST = "client_secret_post"


@dataclass
class OAuthClientConfig:
    """Configuration for OAuth 2.1 client.
    
    Attributes:
        client_id: Registered client identifier
        client_secret: Client secret (optional for PKCE)
        authorization_endpoint: OAuth authorization URL
        token_endpoint: OAuth token URL
        redirect_uri: Callback URL for authorization code
        scopes: Requested OAuth scopes
    """
    client_id: str
    authorization_endpoint: str
    token_endpoint: str
    redirect_uri: str
    client_secret: str | None = None
    scopes: list[str] = field(default_factory=list)
