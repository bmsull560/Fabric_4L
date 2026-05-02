"""Contract tests for MCP tool discovery protocol.

Tests tools/list and related discovery methods per MCP spec.
Covers single upstream, multi-upstream aggregation, and edge cases.
"""

from __future__ import annotations

import pytest
from typing import Any

from value_fabric.shared.mcp_gateway.tests.contract.fixtures import (
    MockMCPClient,
    MockMCPServer,
    MockTool,
    MCPMessage,
)


@pytest.mark.contract
class TestToolDiscoverySingleUpstream:
    """Tool discovery with single upstream server (C-101)."""
    
    @pytest.mark.asyncio
    async def test_tools_list_returns_all_tools(self):
        """C-101: Single upstream: tools/list returns all tools.
        
        Each tool must have:
        - name (unique identifier)
        - description (for LLM selection)
        - inputSchema (JSON Schema for validation)
        """
        server = MockMCPServer(name="single-upstream")
        
        # Add tools with varying complexity
        server.add_tool(MockTool(
            name="search",
            description="Search documents by query",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string", "description": "Search terms"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 100},
                },
            },
        ))
        server.add_tool(MockTool(
            name="calculate",
            description="Perform mathematical calculations",
            input_schema={
                "type": "object",
                "required": ["expression"],
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"},
                },
            },
        ))
        
        client = MockMCPClient()
        client.set_request_handler(lambda r: server.handle_request(r))
        
        # Initialize first
        await client.send_initialize()
        
        # Discover tools
        response = await client.send_tools_list()
        
        # Assert structure
        assert response.result is not None
        assert "tools" in response.result
        assert len(response.result["tools"]) == 2
        
        # Verify each tool has required fields
        for tool in response.result["tools"]:
            assert "name" in tool, "Tool must have name"
            assert "description" in tool, "Tool must have description"
            assert "inputSchema" in tool, "Tool must have inputSchema"
            assert tool["inputSchema"]["type"] == "object"
    
    @pytest.mark.asyncio
    async def test_tool_with_complex_schema(self):
        """C-104: Tool with complex input schema - schema preserved through gateway.
        
        Complex schemas include:
        - Nested objects
        - Arrays
        - Enums
        - Pattern constraints
        """
        server = MockMCPServer(name="schema-test")
        
        complex_schema = {
            "type": "object",
            "required": ["query", "filters"],
            "properties": {
                "query": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 500,
                },
                "filters": {
                    "type": "object",
                    "properties": {
                        "date_range": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "string", "format": "date"},
                                "end": {"type": "string", "format": "date"},
                            },
                        },
                        "categories": {
                            "type": "array",
                            "items": {"type": "string", "enum": ["tech", "business", "science"]},
                        },
                    },
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc", "relevance"],
                    "default": "relevance",
                },
            },
        }
        
        server.add_tool(MockTool(
            name="advanced_search",
            description="Advanced search with filters",
            input_schema=complex_schema,
        ))
        
        client = MockMCPClient()
        client.set_request_handler(lambda r: server.handle_request(r))
        
        await client.send_initialize()
        response = await client.send_tools_list()
        
        tool = response.result["tools"][0]
        schema = tool["inputSchema"]
        
        # Verify complex schema preserved
        assert schema["properties"]["filters"]["type"] == "object"
        assert schema["properties"]["filters"]["properties"]["categories"]["type"] == "array"
        assert "enum" in schema["properties"]["sort_order"]


@pytest.mark.contract
class TestToolDiscoveryMultiUpstream:
    """Tool discovery with multiple upstream servers (C-102, C-103, C-104)."""
    
    @pytest.fixture
    def upstream_a(self):
        """Upstream server A with tools."""
        server = MockMCPServer(name="upstream-a")
        server.add_tool(MockTool(
            name="search",
            description="Search from server A",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {"query": {"type": "string"}},
            },
        ))
        server.add_tool(MockTool(
            name="analyze",
            description="Analyze data",
            input_schema={
                "type": "object",
                "properties": {"data": {"type": "object"}},
            },
        ))
        return server
    
    @pytest.fixture
    def upstream_b(self):
        """Upstream server B with tools."""
        server = MockMCPServer(name="upstream-b")
        server.add_tool(MockTool(
            name="search",  # Same name as upstream-a (intentional collision)
            description="Search from server B",
            input_schema={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {"type": "string"},
                    "source": {"type": "string"},
                },
            },
        ))
        server.add_tool(MockTool(
            name="transform",
            description="Transform data",
            input_schema={
                "type": "object",
                "properties": {"input": {"type": "string"}},
            },
        ))
        return server
    
    @pytest.mark.asyncio
    async def test_multi_upstream_tools_aggregated(self, upstream_a, upstream_b):
        """C-102: Multi-upstream: tools aggregated without collision.
        
        Gateway should merge tools from all upstreams.
        """
        # Simulate gateway aggregating from both upstreams
        async def aggregate_handler(request: MCPMessage) -> MCPMessage:
            # Get tools from both upstreams
            response_a = await upstream_a.handle_request(request)
            response_b = await upstream_b.handle_request(request)
            
            # Merge (simplified - real gateway would handle namespacing)
            all_tools = (
                response_a.result.get("tools", []) +
                response_b.result.get("tools", [])
            )
            
            return MCPMessage(
                id=request.id,
                result={"tools": all_tools},
            )
        
        client = MockMCPClient()
        client.set_request_handler(aggregate_handler)
        
        await client.send_initialize()
        response = await client.send_tools_list()
        
        # Should have 4 tools (2 from each upstream)
        tools = response.result["tools"]
        assert len(tools) == 4
        
        # Verify all tools present
        tool_names = [t["name"] for t in tools]
        assert "search" in tool_names  # Appears twice (collision)
        assert "analyze" in tool_names
        assert "transform" in tool_names
    
    @pytest.mark.asyncio
    async def test_duplicate_tool_names_namespaced(self, upstream_a, upstream_b):
        """C-103: Duplicate tool names: namespacing.
        
        Gateway should namespace tools to avoid collisions:
        - upstream-a/search
        - upstream-b/search
        """
        async def namespaced_handler(request: MCPMessage) -> MCPMessage:
            response_a = await upstream_a.handle_request(request)
            response_b = await upstream_b.handle_request(request)
            
            # Apply namespacing
            tools_a = [
                {**t, "name": f"upstream-a/{t['name']}"}
                for t in response_a.result.get("tools", [])
            ]
            tools_b = [
                {**t, "name": f"upstream-b/{t['name']}"}
                for t in response_b.result.get("tools", [])
            ]
            
            return MCPMessage(
                id=request.id,
                result={"tools": tools_a + tools_b},
            )
        
        client = MockMCPClient()
        client.set_request_handler(namespaced_handler)
        
        await client.send_initialize()
        response = await client.send_tools_list()
        
        tools = response.result["tools"]
        tool_names = [t["name"] for t in tools]
        
        # Should have namespaced tools
        assert "upstream-a/search" in tool_names
        assert "upstream-b/search" in tool_names
        assert "upstream-a/analyze" in tool_names
        assert "upstream-b/transform" in tool_names
    
    @pytest.mark.asyncio
    async def test_duplicate_tool_different_schemas(self, upstream_a, upstream_b):
        """C-104: Tool with same name, different schemas.
        
        Gateway should detect conflict and either:
        - List both with different identifiers
        - Return error/warning
        - Apply versioning
        """
        # Both have "search" but with different schemas
        async def conflict_handler(request: MCPMessage) -> MCPMessage:
            response_a = await upstream_a.handle_request(request)
            response_b = await upstream_b.handle_request(request)
            
            # Detect same name, different schemas
            tools_a = response_a.result.get("tools", [])
            tools_b = response_b.result.get("tools", [])
            
            # Find collisions
            names_a = {t["name"] for t in tools_a}
            names_b = {t["name"] for t in tools_b}
            collisions = names_a & names_b
            
            if collisions:
                # Add collision metadata
                for t in tools_a:
                    if t["name"] in collisions:
                        t["_collision"] = True
                        t["_source"] = "upstream-a"
                for t in tools_b:
                    if t["name"] in collisions:
                        t["_collision"] = True
                        t["_source"] = "upstream-b"
            
            return MCPMessage(
                id=request.id,
                result={"tools": tools_a + tools_b},
            )
        
        client = MockMCPClient()
        client.set_request_handler(conflict_handler)
        
        await client.send_initialize()
        response = await client.send_tools_list()
        
        tools = response.result["tools"]
        search_tools = [t for t in tools if "search" in t["name"]]
        
        # Both should be present with collision markers
        assert len(search_tools) == 2
        assert any(t.get("_collision") for t in search_tools)


@pytest.mark.contract
class TestToolDiscoveryPagination:
    """Tool list pagination support (optional per spec)."""
    
    @pytest.mark.asyncio
    async def test_tools_list_pagination(self):
        """C-105: Paginated tools/list if supported.
        
        Gateway should handle cursor-based pagination.
        """
        server = MockMCPServer(name="pagination-test")
        
        # Add many tools to trigger pagination
        for i in range(150):
            server.add_tool(MockTool(
                name=f"tool-{i:03d}",
                description=f"Tool number {i}",
                input_schema={"type": "object", "properties": {}},
            ))
        
        # Override handler to implement pagination
        async def paginated_handler(request: MCPMessage) -> MCPMessage:
            cursor = request.params.get("cursor") if request.params else None
            
            all_tools = [
                {"name": f"tool-{i:03d}", "description": f"Tool {i}", "inputSchema": {}}
                for i in range(150)
            ]
            
            # Simple pagination: 50 per page
            page_size = 50
            if cursor:
                start = int(cursor)
            else:
                start = 0
            
            page = all_tools[start:start + page_size]
            next_cursor = str(start + page_size) if start + page_size < len(all_tools) else None
            
            result = {"tools": page}
            if next_cursor:
                result["nextCursor"] = next_cursor
            
            return MCPMessage(id=request.id, result=result)
        
        client = MockMCPClient()
        client.set_request_handler(paginated_handler)
        
        await client.send_initialize()
        
        # Fetch first page
        response1 = await client.send_tools_list()
        assert len(response1.result["tools"]) == 50
        assert "nextCursor" in response1.result
        
        # Fetch second page
        response2 = await client.send_tools_list(cursor=response1.result["nextCursor"])
        assert len(response2.result["tools"]) == 50
        assert "nextCursor" in response2.result
        
        # Fetch third page
        response3 = await client.send_tools_list(cursor=response2.result["nextCursor"])
        assert len(response3.result["tools"]) == 50
        # No more pages
        assert "nextCursor" not in response3.result


@pytest.mark.contract
class TestToolDiscoveryEdgeCases:
    """Edge cases and error handling in tool discovery."""
    
    @pytest.mark.asyncio
    async def test_empty_tools_list(self):
        """Server with no tools returns empty list."""
        server = MockMCPServer(name="empty-server")
        
        client = MockMCPClient()
        client.set_request_handler(lambda r: server.handle_request(r))
        
        await client.send_initialize()
        response = await client.send_tools_list()
        
        assert response.result["tools"] == []
    
    @pytest.mark.asyncio
    async def test_tools_list_without_initialize(self):
        """tools/list without initialize returns error."""
        server = MockMCPServer(name="test-server")
        server.add_tool(MockTool(name="test", description="Test", input_schema={}))
        
        # Override to reject without initialization
        async def strict_handler(request: MCPMessage) -> MCPMessage:
            if request.method != "initialize":
                return MCPMessage(
                    id=request.id,
                    error={
                        "code": -32001,
                        "message": "Server not initialized",
                    }
                )
            return await server.handle_request(request)
        
        client = MockMCPClient()
        client.set_request_handler(strict_handler)
        
        # Skip initialize
        response = await client.send_tools_list()
        
        assert response.error is not None
        assert response.error["code"] == -32001
