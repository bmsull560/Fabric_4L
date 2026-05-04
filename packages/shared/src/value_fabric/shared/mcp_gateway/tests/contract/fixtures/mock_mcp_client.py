"""Mock MCP client for contract testing.

This module provides an in-process MCP client that speaks the Model Context Protocol
for testing gateway protocol compliance without network I/O.
"""

from __future__ import annotations

import json
import asyncio
from typing import Any, Callable, Optional
from dataclasses import dataclass, field
from enum import Enum


class MCPErrorCode(Enum):
    """Standard MCP JSON-RPC error codes."""
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    SERVER_ERROR = -32000
    
    # MCP-specific errors
    NOT_INITIALIZED = -32001
    ALREADY_INITIALIZED = -32002
    SESSION_EXPIRED = -440


@dataclass
class MCPMessage:
    """MCP JSON-RPC message structure.
    
    Per MCP 2024-11-05 spec, all messages follow JSON-RPC 2.0 format.
    """
    jsonrpc: str = "2.0"
    id: str | int | None = None
    method: str | None = None
    params: dict | None = None
    result: Any = None
    error: dict | None = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        data = {"jsonrpc": self.jsonrpc}
        if self.id is not None:
            data["id"] = self.id
        if self.method is not None:
            data["method"] = self.method
        if self.params is not None:
            data["params"] = self.params
        if self.result is not None:
            data["result"] = self.result
        if self.error is not None:
            data["error"] = self.error
        return data
    
    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), separators=(",", ":"))
    
    @classmethod
    def from_dict(cls, data: dict) -> "MCPMessage":
        """Deserialize from dictionary."""
        return cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            id=data.get("id"),
            method=data.get("method"),
            params=data.get("params"),
            result=data.get("result"),
            error=data.get("error"),
        )
    
    @classmethod
    def from_json(cls, json_str: str) -> "MCPMessage":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))
    
    def is_request(self) -> bool:
        """True if this is a request (has method)."""
        return self.method is not None
    
    def is_response(self) -> bool:
        """True if this is a response (has result or error)."""
        return self.result is not None or self.error is not None
    
    def is_notification(self) -> bool:
        """True if this is a notification (request with no id)."""
        return self.method is not None and self.id is None
    
    def is_error(self) -> bool:
        """True if this is an error response."""
        return self.error is not None


class MockMCPClient:
    """In-process MCP client for contract testing.
    
    This client implements the MCP protocol for testing gateway compliance
    without requiring network I/O. It can be connected to a gateway via
    an in-memory transport or used to validate gateway responses.
    
    Example:
        >>> client = MockMCPClient()
        >>> response = await client.send_initialize()
        >>> assert response.result["protocolVersion"] == "2024-11-05"
        >>> 
        >>> tools_response = await client.send_tools_list()
        >>> assert "tools" in tools_response.result
    """
    
    def __init__(self, protocol_version: str = "2024-11-05"):
        """Initialize the mock client.
        
        Args:
            protocol_version: MCP protocol version to use
        """
        self.protocol_version = protocol_version
        self._message_id = 0
        self._initialized = False
        self._request_handler: Optional[Callable[[MCPMessage], asyncio.Future[MCPMessage]]] = None
        self._capabilities: dict = {}
        self._server_info: dict = {}
        
    def set_request_handler(self, handler: Callable[[MCPMessage], asyncio.Future[MCPMessage]]):
        """Set the handler for sending requests (e.g., to gateway).
        
        Args:
            handler: Async function that takes MCPMessage request and returns response
        """
        self._request_handler = handler
    
    async def _send(self, message: MCPMessage) -> MCPMessage:
        """Send a message and return the response.
        
        Uses the configured request handler or raises if not set.
        """
        if self._request_handler is None:
            raise RuntimeError("No request handler configured. Call set_request_handler() first.")
        return await self._request_handler(message)
    
    def _next_id(self) -> int:
        """Generate next message ID."""
        self._message_id += 1
        return self._message_id
    
    def _create_request(self, method: str, params: dict | None = None) -> MCPMessage:
        """Create a request message."""
        return MCPMessage(
            id=self._next_id(),
            method=method,
            params=params or {},
        )
    
    # =========================================================================
    # MCP Protocol Methods
    # =========================================================================
    
    async def send_initialize(
        self,
        protocol_version: str | None = None,
        capabilities: dict | None = None,
        client_info: dict | None = None,
    ) -> MCPMessage:
        """Send initialize request per MCP spec.
        
        Args:
            protocol_version: Protocol version (defaults to client version)
            capabilities: Client capabilities
            client_info: Client identification
            
        Returns:
            Initialize response with server capabilities
        """
        request = self._create_request("initialize", {
            "protocolVersion": protocol_version or self.protocol_version,
            "capabilities": capabilities or {},
            "clientInfo": client_info or {"name": "mock-mcp-client", "version": "1.0.0"},
        })
        
        response = await self._send(request)
        
        if response.result:
            self._initialized = True
            self._capabilities = response.result.get("capabilities", {})
            self._server_info = response.result.get("serverInfo", {})
        
        return response
    
    async def send_initialized(self) -> MCPMessage:
        """Send initialized notification.
        
        This is a notification (no response expected) sent after
        successful initialize to confirm client is ready.
        """
        notification = MCPMessage(
            method="notifications/initialized",
            params={},
        )
        return await self._send(notification)
    
    async def send_ping(self) -> MCPMessage:
        """Send ping to check server liveness.
        
        Returns:
            Empty result response
        """
        request = self._create_request("ping")
        return await self._send(request)
    
    async def send_tools_list(self, cursor: str | None = None) -> MCPMessage:
        """Request list of available tools.
        
        Args:
            cursor: Pagination cursor (optional)
            
        Returns:
            Tools list response
        """
        params = {}
        if cursor:
            params["cursor"] = cursor
            
        request = self._create_request("tools/list", params)
        return await self._send(request)
    
    async def send_tools_call(
        self,
        name: str,
        arguments: dict,
        meta: dict | None = None,
    ) -> MCPMessage:
        """Call a tool.
        
        Args:
            name: Tool name to invoke
            arguments: Tool-specific parameters
            meta: Optional metadata (progressToken, etc.)
            
        Returns:
            Tool result or error
        """
        params = {
            "name": name,
            "arguments": arguments,
        }
        if meta:
            params["_meta"] = meta
            
        request = self._create_request("tools/call", params)
        return await self._send(request)
    
    async def send_resources_list(self, cursor: str | None = None) -> MCPMessage:
        """Request list of available resources.
        
        Args:
            cursor: Pagination cursor (optional)
            
        Returns:
            Resources list response
        """
        params = {}
        if cursor:
            params["cursor"] = cursor
            
        request = self._create_request("resources/list", params)
        return await self._send(request)
    
    async def send_resources_read(self, uri: str) -> MCPMessage:
        """Read a resource by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content response
        """
        request = self._create_request("resources/read", {"uri": uri})
        return await self._send(request)
    
    async def send_prompts_list(self, cursor: str | None = None) -> MCPMessage:
        """Request list of available prompts.
        
        Args:
            cursor: Pagination cursor (optional)
            
        Returns:
            Prompts list response
        """
        params = {}
        if cursor:
            params["cursor"] = cursor
            
        request = self._create_request("prompts/list", params)
        return await self._send(request)
    
    async def send_prompts_get(
        self,
        name: str,
        arguments: dict | None = None,
    ) -> MCPMessage:
        """Get a prompt template.
        
        Args:
            name: Prompt name
            arguments: Prompt arguments (optional)
            
        Returns:
            Prompt template response
        """
        params = {"name": name}
        if arguments:
            params["arguments"] = arguments
            
        request = self._create_request("prompts/get", params)
        return await self._send(request)
    
    async def send_completion_complete(
        self,
        ref: dict,
        argument: dict,
    ) -> MCPMessage:
        """Request completion suggestions.
        
        Args:
            ref: Reference to what is being completed (type, name)
            argument: Argument being completed (name, value)
            
        Returns:
            Completion suggestions
        """
        request = self._create_request("completion/complete", {
            "ref": ref,
            "argument": argument,
        })
        return await self._send(request)
    
    async def send_logging_setlevel(self, level: str) -> MCPMessage:
        """Set server logging level.
        
        Args:
            level: Log level (debug, info, warning, error)
            
        Returns:
            Confirmation
        """
        request = self._create_request("logging/setLevel", {"level": level})
        return await self._send(request)
    
    # =========================================================================
    # State Accessors
    # =========================================================================
    
    @property
    def is_initialized(self) -> bool:
        """True if initialize handshake completed successfully."""
        return self._initialized
    
    @property
    def server_capabilities(self) -> dict:
        """Server capabilities from initialize response."""
        return self._capabilities.copy()
    
    @property
    def server_info(self) -> dict:
        """Server identification info."""
        return self._server_info.copy()
    
    def supports_tool(self, tool_name: str) -> bool:
        """Check if server supports a specific tool.
        
        Requires prior tools/list call.
        """
        tools = self._capabilities.get("tools", [])
        return any(t.get("name") == tool_name for t in tools)
    
    # =========================================================================
    # Error Factory Methods
    # =========================================================================
    
    @staticmethod
    def create_error_response(
        id: str | int | None,
        code: int,
        message: str,
        data: Any = None,
    ) -> MCPMessage:
        """Create an error response message."""
        error = {
            "code": code,
            "message": message,
        }
        if data is not None:
            error["data"] = data
            
        return MCPMessage(
            id=id,
            error=error,
        )
    
    @staticmethod
    def create_parse_error(id: str | int | None, message: str = "Parse error") -> MCPMessage:
        """Create a parse error response."""
        return MockMCPClient.create_error_response(id, MCPErrorCode.PARSE_ERROR.value, message)
    
    @staticmethod
    def create_invalid_request(
        id: str | int | None,
        message: str = "Invalid Request",
    ) -> MCPMessage:
        """Create an invalid request error response."""
        return MockMCPClient.create_error_response(id, MCPErrorCode.INVALID_REQUEST.value, message)
    
    @staticmethod
    def create_method_not_found(
        id: str | int | None,
        method: str,
    ) -> MCPMessage:
        """Create a method not found error response."""
        return MockMCPClient.create_error_response(
            id,
            MCPErrorCode.METHOD_NOT_FOUND.value,
            f"Method not found: {method}",
        )
    
    @staticmethod
    def create_invalid_params(
        id: str | int | None,
        message: str = "Invalid params",
    ) -> MCPMessage:
        """Create an invalid params error response."""
        return MockMCPClient.create_error_response(id, MCPErrorCode.INVALID_PARAMS.value, message)
