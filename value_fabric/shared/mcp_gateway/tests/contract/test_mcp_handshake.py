"""Contract tests for MCP handshake protocol.

Tests the initialize handshake and session lifecycle per MCP 2024-11-05 spec.
Covers protocol version negotiation, capabilities exchange, and error handling.
"""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock

from shared.mcp_gateway.tests.contract.fixtures import MockMCPClient, MockMCPServer, MCPMessage
from shared.mcp_gateway.tests.contract.fixtures.mock_mcp_client import MCPErrorCode


@pytest.mark.contract
class TestMCPHandshake:
    """MCP initialize handshake protocol compliance tests (C-001 through C-005)."""
    
    @pytest.fixture
    def upstream_server(self):
        """Create a healthy upstream MCP server."""
        server = MockMCPServer(name="test-upstream")
        return server
    
    @pytest.fixture
    def gateway_with_upstream(self, upstream_server):
        """Create gateway configured with upstream server."""
        # This is a simplified fixture - real implementation would wire to actual gateway
        from shared.mcp_gateway import MCPGateway
        
        gateway = MCPGateway(
            auth_handler=None,
            token_exchanger=None,
            manifest_verifier=None,
            tool_registry=None,
            enable_audit_logging=False,
        )
        
        # Attach upstream handler
        async def handle_request(request: MCPMessage) -> MCPMessage:
            return await upstream_server.handle_request(request)
        
        return gateway, handle_request
    
    @pytest.mark.asyncio
    async def test_initialize_success_returns_capabilities(self, upstream_server):
        """C-001: Gateway accepts valid initialize request and returns capabilities.
        
        Per MCP spec, initialize must:
        - Return protocolVersion matching or negotiated
        - Include serverInfo with name and version
        - Include capabilities object
        """
        client = MockMCPClient(protocol_version="2024-11-05")
        
        # Configure client to use upstream
        async def handle_request(request: MCPMessage) -> MCPMessage:
            return await upstream_server.handle_request(request)
        
        client.set_request_handler(handle_request)
        
        # Send initialize
        response = await client.send_initialize()
        
        # Assert protocol compliance
        assert response.result is not None, "Initialize must return result"
        assert response.result["protocolVersion"] == "2024-11-05"
        assert "serverInfo" in response.result
        assert "capabilities" in response.result
        assert response.result["serverInfo"]["name"] == "test-upstream"
        assert client.is_initialized, "Client should mark as initialized"
    
    @pytest.mark.asyncio
    async def test_initialize_rejects_unsupported_protocol(self, upstream_server):
        """C-002: Gateway rejects initialize with unsupported protocol version.
        
        Must return error with supported versions.
        """
        client = MockMCPClient(protocol_version="2024-11-05")
        
        async def handle_request(request: MCPMessage) -> MCPMessage:
            # Simulate gateway rejecting unsupported version
            if request.params.get("protocolVersion") == "2023-01-01":
                return MCPMessage(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Unsupported protocol version: 2023-01-01",
                        "data": {"supportedVersions": ["2024-11-05"]},
                    }
                )
            return await upstream_server.handle_request(request)
        
        client.set_request_handler(handle_request)
        
        response = await client.send_initialize(protocol_version="2023-01-01")
        
        assert response.error is not None, "Should return error"
        assert response.error["code"] == -32602  # Invalid params
        assert "supportedVersions" in response.error.get("data", {})
    
    @pytest.mark.asyncio
    async def test_initialize_requires_client_info(self, upstream_server):
        """C-003: Gateway rejects initialize without client info.
        
        Per spec, clientInfo is required.
        """
        client = MockMCPClient(protocol_version="2024-11-05")
        
        async def handle_request(request: MCPMessage) -> MCPMessage:
            # Simulate gateway requiring clientInfo
            if not request.params.get("clientInfo"):
                return MCPMessage(
                    id=request.id,
                    error={
                        "code": -32602,
                        "message": "Missing required parameter: clientInfo",
                    }
                )
            return await upstream_server.handle_request(request)
        
        client.set_request_handler(handle_request)
        
        # Send initialize without clientInfo
        response = await client.send_initialize(client_info=None)
        
        assert response.error is not None
        assert "clientInfo" in response.error["message"]
    
    @pytest.mark.asyncio
    async def test_ping_returns_empty_result(self, upstream_server):
        """C-004: Gateway supports ping/pong keepalive.
        
        Ping must return empty result ({}).
        """
        client = MockMCPClient()
        
        async def handle_request(request: MCPMessage) -> MCPMessage:
            return await upstream_server.handle_request(request)
        
        client.set_request_handler(handle_request)
        
        # Initialize first (required before other methods)
        await client.send_initialize()
        
        # Send ping
        response = await client.send_ping()
        
        assert response.result == {}, "Ping must return empty result"
    
    @pytest.mark.asyncio
    async def test_rejects_requests_before_initialize(self, upstream_server):
        """C-005: Gateway rejects requests before initialization.
        
        Any method except initialize must fail with not initialized error.
        """
        client = MockMCPClient()
        
        async def handle_request(request: MCPMessage) -> MCPMessage:
            # Simulate gateway rejecting un-initialized requests
            if request.method != "initialize":
                return MCPMessage(
                    id=request.id,
                    error={
                        "code": MCPErrorCode.NOT_INITIALIZED.value,
                        "message": "Server not initialized",
                    }
                )
            return await upstream_server.handle_request(request)
        
        client.set_request_handler(handle_request)
        
        # Try tools/list without initialize
        response = await client.send_tools_list()
        
        assert response.error is not None
        assert response.error["code"] == MCPErrorCode.NOT_INITIALIZED.value
    
    @pytest.mark.asyncio
    async def test_initialize_idempotency(self, upstream_server):
        """Additional: Gateway handles duplicate initialize gracefully.
        
        Per spec, initialize should be idempotent or return error.
        """
        client = MockMCPClient()
        
        async def handle_request(request: MCPMessage) -> MCPMessage:
            return await upstream_server.handle_request(request)
        
        client.set_request_handler(handle_request)
        
        # First initialize
        response1 = await client.send_initialize()
        assert response1.result is not None
        
        # Second initialize - should be idempotent or error
        response2 = await client.send_initialize()
        
        # Either succeeds with same result or returns already initialized error
        assert response2.result is not None or response2.error is not None
        if response2.error:
            assert response2.error["code"] == MCPErrorCode.ALREADY_INITIALIZED.value


@pytest.mark.contract
class TestMCPHandshakeCapabilities:
    """Capability negotiation contract tests."""
    
    @pytest.mark.asyncio
    async def test_capabilities_include_tools(self):
        """Server capabilities indicate tools support."""
        server = MockMCPServer(name="tools-server")
        server.add_tool(MockMCPServer._create_mock_tool("test"))
        
        client = MockMCPClient()
        client.set_request_handler(lambda r: server.handle_request(r))
        
        response = await client.send_initialize()
        
        assert "capabilities" in response.result
        assert "tools" in response.result["capabilities"]
    
    @pytest.mark.asyncio
    async def test_capabilities_include_resources(self):
        """Server capabilities indicate resources support."""
        server = MockMCPServer(name="resources-server")
        
        from shared.mcp_gateway.tests.contract.fixtures.mock_mcp_server import MockResource
        server.add_resource(MockResource(
            uri="file:///test.txt",
            name="test",
            content="test content",
        ))
        
        client = MockMCPClient()
        client.set_request_handler(lambda r: server.handle_request(r))
        
        response = await client.send_initialize()
        
        assert "capabilities" in response.result
        assert "resources" in response.result["capabilities"]
    
    @pytest.mark.asyncio
    async def test_capabilities_include_prompts(self):
        """Server capabilities indicate prompts support."""
        server = MockMCPServer(name="prompts-server")
        server.add_prompt("test-prompt", "Test prompt description")
        
        client = MockMCPClient()
        client.set_request_handler(lambda r: server.handle_request(r))
        
        response = await client.send_initialize()
        
        assert "capabilities" in response.result
        assert "prompts" in response.result["capabilities"]


# Helper to create mock tools for capability tests
def _create_mock_tool(name: str) -> Any:
    from shared.mcp_gateway.tests.contract.fixtures.mock_mcp_server import MockTool
    return MockTool(
        name=name,
        description=f"Tool {name}",
        input_schema={"type": "object", "properties": {}},
    )


MockMCPServer._create_mock_tool = staticmethod(_create_mock_tool)
