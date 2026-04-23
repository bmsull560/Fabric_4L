"""MCP Gateway - Secure Tool Authentication and Delegation.

Provides OAuth 2.1 + PKCE authentication for MCP tools, RFC 8693 Token Exchange
for tool-to-tool delegation, and signed tool manifest verification.

This package implements the security layer for the Model Context Protocol (MCP)
gateway, ensuring tools authenticate with proper tenant context and audit trails.

Example:
    >>> from shared.mcp_gateway import MCPGateway
    >>> gateway = MCPGateway()
    >>> result = await gateway.invoke_tool(
    ...     tool_name="search",
    ...     request={"query": "example"},
    ...     tenant_id=tenant_uuid
    ... )
"""

from .gateway import MCPGateway
from .auth import OAuthHandler, PKCEVerifier
from .token_exchange import TokenExchanger
from .manifest import ManifestVerifier
from .registry import ToolRegistry
from .mcp_types import (
    ToolRequest,
    ToolResponse,
    ToolManifest,
    DelegatedToken,
    GatewayError,
    AuthenticationError,
    ManifestValidationError,
)

__all__ = [
    "MCPGateway",
    "OAuthHandler",
    "PKCEVerifier",
    "TokenExchanger",
    "ManifestVerifier",
    "ToolRegistry",
    "ToolRequest",
    "ToolResponse",
    "ToolManifest",
    "DelegatedToken",
    "GatewayError",
    "AuthenticationError",
    "ManifestValidationError",
]
