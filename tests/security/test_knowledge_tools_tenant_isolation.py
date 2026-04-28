"""P0: Knowledge Tools Tenant Isolation Tests

Validates that knowledge graph query tools enforce tenant boundaries.
These tests address the gap where QueryGraphTool executes Cypher queries
without validating tenant context, potentially allowing cross-tenant data access.

Ship/No-Ship Gate: FAIL on this file blocks release.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

# Path setup - only executed at collection time, cleaned up after
_repo_root = Path(__file__).resolve().parents[2]
_layer4_src = _repo_root / "value-fabric" / "layer4-agents" / "src"
_shared_path = str(_repo_root / "value-fabric")
_layer4_path = str(_layer4_src)

# Use pytest fixture for scoped path manipulation instead of module-level mutation
@pytest.fixture(scope="module", autouse=True)
def setup_import_paths():
    """Add required paths for imports, cleanup after module tests complete."""
    paths_added = []
    for path in [_shared_path, _layer4_path]:
        if path not in sys.path:
            sys.path.insert(0, path)
            paths_added.append(path)
    yield
    # Cleanup: remove only paths we added (use discard pattern for safety)
    for path in paths_added:
        try:
            sys.path.remove(path)
        except ValueError:
            pass  # Path already removed by another test or cleanup


# Lazy import fixtures to avoid import errors at collection time
def _get_knowledge_tools():
    """Import knowledge tools with proper error handling.
    
    Bypasses broken __init__.py by importing directly from module file.
    """
    import importlib.util
    
    # Import directly from file to bypass package __init__ issues
    tools_path = _layer4_src / "tools" / "knowledge_tools.py"
    spec = importlib.util.spec_from_file_location("knowledge_tools", tools_path)
    module = importlib.util.module_from_spec(spec)
    
    # Need to set up sys.path for relative imports in the module
    sys.path.insert(0, str(_layer4_src))
    try:
        spec.loader.exec_module(module)
    except ImportError as e:
        pytest.skip(f"Cannot load knowledge_tools module: {e}")
    finally:
        if str(_layer4_src) in sys.path:
            sys.path.remove(str(_layer4_src))
    
    # Import schemas separately
    schemas_path = _layer4_src / "models" / "tool_schemas.py"
    schemas_spec = importlib.util.spec_from_file_location("tool_schemas", schemas_path)
    schemas_module = importlib.util.module_from_spec(schemas_spec)
    sys.path.insert(0, str(_layer4_src))
    try:
        schemas_spec.loader.exec_module(schemas_module)
    except ImportError as e:
        pytest.skip(f"Cannot load tool_schemas module: {e}")
    finally:
        if str(_layer4_src) in sys.path:
            sys.path.remove(str(_layer4_src))
    
    return (
        module.QueryGraphTool, 
        module.SemanticSearchTool, 
        schemas_module.QueryGraphInput, 
        schemas_module.SemanticSearchInput
    )

# Constants matching conftest.py
TENANT_A_ID = UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
TENANT_B_ID = UUID("bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb")


class TestQueryGraphToolTenantEnforcement:
    """P0: Verify query_graph tool enforces tenant isolation."""

    @pytest.fixture
    def mock_neo4j_session(self):
        """Create a mock Neo4j session that captures executed queries."""
        session = AsyncMock()
        
        # Mock result that returns records with tenant_id
        result = AsyncMock()
        result.data = AsyncMock(return_value=[
            {"id": "node-1", "tenant_id": str(TENANT_A_ID), "name": "Entity A"},
            {"id": "node-2", "tenant_id": str(TENANT_A_ID), "name": "Entity B"},
        ])
        result.keys = MagicMock(return_value=["id", "tenant_id", "name"])
        
        session.run = AsyncMock(return_value=result)
        return session

    @pytest.fixture
    def mock_tenant_context(self, monkeypatch):
        """Mock tenant context for testing without real shared.identity."""
        from unittest.mock import MagicMock, patch
        
        # Create a mock TenantContext
        mock_ctx = MagicMock()
        mock_ctx.tenant_id = TENANT_A_ID
        mock_ctx.user_id = "user-123"
        mock_ctx.roles = ["analyst"]
        mock_ctx.source = "jwt"
        
        # Patch get_current_tenant_context to return our mock
        with patch("shared.domain.context.get_request_context") as mock_get_ctx:
            mock_get_ctx.return_value = mock_ctx
            yield mock_ctx

    @pytest.mark.asyncio
    async def test_query_graph_injects_tenant_filter(self, mock_neo4j_session, mock_tenant_context):
        """POSITIVE: Tool injects tenant filter into Cypher query when context available.
        
        When TenantContext is set, the query_graph tool should:
        1. Extract tenant_id from context
        2. Modify query to add tenant filter
        3. Execute modified query
        """
        QueryGraphTool, _, QueryGraphInput, _ = _get_knowledge_tools()
        
        tool = QueryGraphTool(config={"neo4j_uri": "bolt://localhost:7687"})
        
        # Patch the driver to return our mock session
        mock_driver = MagicMock()
        mock_driver.session = MagicMock(return_value=mock_neo4j_session)
        tool._driver = mock_driver
        
        input_data = QueryGraphInput(
            cypher_query="MATCH (n:Account) RETURN n LIMIT 10",
            parameters={}
        )
        
        result = await tool.execute(input_data)
        
        # Verify the session.run was called
        mock_neo4j_session.run.assert_called_once()
        call_args = mock_neo4j_session.run.call_args
        executed_query = call_args[0][0]  # First positional arg is the query
        
        # Verify tenant filtering was injected
        assert str(TENANT_A_ID) in executed_query or "tenant_id" in executed_query or "$tenant_id" in executed_query, (
            f"Query must include tenant filter. Executed query: {executed_query}"
        )

    @pytest.mark.asyncio
    async def test_query_graph_without_tenant_context_fails_closed(self, mock_neo4j_session):
        """NEGATIVE: Tool fails closed when no tenant context is available.
        
        Without RequestContext, the tool must either:
        1. Reject the query entirely
        2. Require explicit tenant_id in input
        3. Return error response
        
        This is a P0 negative test - it proves the tool doesn't execute
        unscoped queries that could return cross-tenant data.
        """
        QueryGraphTool, _, QueryGraphInput, _ = _get_knowledge_tools()
        
        tool = QueryGraphTool(config={"neo4j_uri": "bolt://localhost:7687"})
        
        mock_driver = MagicMock()
        mock_driver.session = MagicMock(return_value=mock_neo4j_session)
        tool._driver = mock_driver
        
        input_data = QueryGraphInput(
            cypher_query="MATCH (n:Account) RETURN n LIMIT 10",
            parameters={}
        )
        
        result = await tool.execute(input_data)
        
        # Tool should fail closed with error when no tenant context
        assert result.error is not None, (
            "Tool must fail closed without tenant context. "
            f"Got {result.row_count} rows with no error."
        )
        assert "tenant" in result.error.lower() or "authentication" in result.error.lower(), (
            f"Error should indicate tenant/auth issue: {result.error}"
        )

    @pytest.mark.asyncio
    async def test_cross_tenant_query_blocked(self, mock_neo4j_session, mock_tenant_context):
        """NEGATIVE: Tenant A cannot query Tenant B data via tenant_id spoofing.
        
        Attempting to override tenant_id in query parameters should be blocked.
        The tool must use the authenticated context tenant_id, not the input.
        """
        QueryGraphTool, _, QueryGraphInput, _ = _get_knowledge_tools()
        
        tool = QueryGraphTool(config={"neo4j_uri": "bolt://localhost:7687"})
        
        mock_driver = MagicMock()
        mock_driver.session = MagicMock(return_value=mock_neo4j_session)
        tool._driver = mock_driver
        
        # Try to spoof tenant_b in parameters
        input_data = QueryGraphInput(
            cypher_query="MATCH (n:Account {tenant_id: $tenant_id}) RETURN n",
            parameters={"tenant_id": str(TENANT_B_ID)}  # Attempted spoof
        )
        
        result = await tool.execute(input_data)
        
        # Verify the actual tenant_id in the executed query
        call_args = mock_neo4j_session.run.call_args
        actual_params = call_args[1].get("parameters", {}) if len(call_args) > 1 else {}
        
        # The tool should override spoofed tenant_id with context tenant_id
        assert actual_params.get("tenant_id") != str(TENANT_B_ID), (
            "Tool must reject tenant_id spoofing in query parameters. "
            "Input attempted Tenant B but Tenant A context should override."
        )


class TestSemanticSearchToolTenantIsolation:
    """P1: Verify semantic_search tool enforces tenant boundaries."""

    @pytest.fixture
    def mock_pinecone_index(self):
        """Create mock Pinecone index that captures query filters."""
        index = MagicMock()
        index.query = MagicMock(return_value={
            "matches": [
                {"id": "vec-1", "score": 0.95, "metadata": {"tenant_id": str(TENANT_A_ID)}},
            ]
        })
        return index

    @pytest.mark.asyncio
    async def test_semantic_search_applies_tenant_filter(self, mock_pinecone_index, monkeypatch):
        """POSITIVE: Semantic search includes tenant_id in metadata filter."""
        from tools.knowledge_tools import SemanticSearchTool
        from models.tool_schemas import SemanticSearchInput
        from shared.identity.context import RequestContext, set_request_context
        from shared.identity.permissions import Permission
        
        # Set tenant context
        ctx = RequestContext(
            tenant_id=TENANT_A_ID,
            user_id="user-123",
            roles=["analyst"],
            api_key_id=None,
            permissions=frozenset({Permission.READ_KNOWLEDGE}),
            source="jwt",
            raw={},
        )
        token = set_request_context(ctx)
        
        try:
            tool = SemanticSearchTool(config={"pinecone_api_key": "test-key"})
            tool._index = mock_pinecone_index
            
            input_data = SemanticSearchInput(
                query="sales forecasting methodology",
                top_k=5
            )
            
            result = await tool.execute(input_data)
            
            # Verify query was called with tenant filter
            mock_pinecone_index.query.assert_called_once()
            call_kwargs = mock_pinecone_index.query.call_args.kwargs
            
            filter_metadata = call_kwargs.get("filter", {})
            assert "tenant_id" in filter_metadata, (
                "Semantic search must include tenant_id in metadata filter"
            )
            assert filter_metadata["tenant_id"] == str(TENANT_A_ID), (
                f"Filter must use context tenant_id, got {filter_metadata.get('tenant_id')}"
            )
        finally:
            from shared.identity.context import _current_context
            _current_context.reset(token)


class TestKnowledgeToolsRateLimiting:
    """P1: Knowledge tools respect rate limiting."""

    @pytest.mark.asyncio
    async def test_query_graph_respects_rate_limit(self, monkeypatch):
        """NEGATIVE: Tool fails gracefully when rate limit exceeded."""
        from tools.knowledge_tools import QueryGraphTool
        from models.tool_schemas import QueryGraphInput
        
        # Mock rate limiter that always blocks
        mock_limiter = MagicMock()
        mock_limiter.check = AsyncMock(return_value=MagicMock(
            allowed=False,
            retry_after=60
        ))
        
        monkeypatch.setattr(
            "shared.identity.rate_limiter.RedisRateLimiter",
            lambda **kwargs: mock_limiter
        )
        
        tool = QueryGraphTool(config={"neo4j_uri": "bolt://localhost:7687"})
        
        input_data = QueryGraphInput(
            cypher_query="MATCH (n) RETURN n LIMIT 1",
            parameters={}
        )
        
        result = await tool.execute(input_data)
        
        # Should return error indicating rate limit
        assert result.error is not None, "Rate limited request must return error"
        assert "rate" in result.error.lower() or "limit" in result.error.lower(), (
            f"Error should indicate rate limiting: {result.error}"
        )


class TestKnowledgeToolsInputValidation:
    """P0: Knowledge tools validate input to prevent injection attacks."""

    @pytest.mark.asyncio
    async def test_query_graph_blocks_write_operations(self):
        """NEGATIVE: Cypher write operations are blocked (read-only enforcement)."""
        from tools.knowledge_tools import QueryGraphTool
        from models.tool_schemas import QueryGraphInput
        
        tool = QueryGraphTool(config={"neo4j_uri": "bolt://localhost:7687"})
        
        malicious_queries = [
            "MATCH (n) DELETE n",  # DELETE
            "MATCH (n) SET n.prop = 'value'",  # SET
            "CREATE (n:Node {id: 1})",  # CREATE
            "MATCH (n) MERGE (m:Node)",  # MERGE
            "MATCH (n) REMOVE n.prop",  # REMOVE
            "DROP INDEX test",  # DROP
        ]
        
        for query in malicious_queries:
            input_data = QueryGraphInput(cypher_query=query, parameters={})
            result = await tool.execute(input_data)
            
            assert result.error is not None, (
                f"Write operation must be blocked: {query}"
            )
            assert result.row_count == 0, (
                f"Write operation must return 0 rows: {query}"
            )

    @pytest.mark.asyncio
    async def test_query_graph_allows_read_operations(self):
        """POSITIVE: Read-only Cypher queries are permitted."""
        from tools.knowledge_tools import QueryGraphTool
        from models.tool_schemas import QueryGraphInput
        
        tool = QueryGraphTool(config={"neo4j_uri": "bolt://localhost:7687"})
        
        read_queries = [
            "MATCH (n:Account) RETURN n LIMIT 10",
            "MATCH (n)-[r]->(m) RETURN n, r, m",
            "MATCH (n) WHERE n.name = 'test' RETURN n",
            "MATCH (n) RETURN n ORDER BY n.created_at DESC",
            "MATCH (n) RETURN count(n) as total",
        ]
        
        # Mock the driver to avoid actual DB calls
        with patch.object(tool, '_get_driver') as mock_get_driver:
            mock_session = AsyncMock()
            mock_result = AsyncMock()
            mock_result.data = AsyncMock(return_value=[])
            mock_session.run = AsyncMock(return_value=mock_result)
            
            mock_driver = MagicMock()
            mock_driver.session = MagicMock(return_value=mock_session)
            mock_get_driver.return_value = mock_driver
            
            for query in read_queries:
                input_data = QueryGraphInput(cypher_query=query, parameters={})
                result = await tool.execute(input_data)
                
                assert result.error is None or "write" not in result.error.lower(), (
                    f"Read query should be allowed: {query}. Error: {result.error}"
                )


class TestKnowledgeToolsAuditLogging:
    """P1: Knowledge tools generate audit logs for security events."""

    @pytest.mark.asyncio
    async def test_query_graph_logs_executed_queries(self, caplog):
        """POSITIVE: Executed queries are logged for audit trail."""
        from tools.knowledge_tools import QueryGraphTool
        from models.tool_schemas import QueryGraphInput
        
        import logging
        
        # Set log level to capture query logs
        with caplog.at_level(logging.INFO):
            tool = QueryGraphTool(config={"neo4j_uri": "bolt://localhost:7687"})
            
            with patch.object(tool, '_get_driver') as mock_get_driver:
                mock_session = AsyncMock()
                mock_result = AsyncMock()
                mock_result.data = AsyncMock(return_value=[])
                mock_session.run = AsyncMock(return_value=mock_result)
                
                mock_driver = MagicMock()
                mock_driver.session = MagicMock(return_value=mock_session)
                mock_get_driver.return_value = mock_driver
                
                input_data = QueryGraphInput(
                    cypher_query="MATCH (n:Account) RETURN n",
                    parameters={}
                )
                
                await tool.execute(input_data)
                
                # Verify query was logged
                log_messages = " ".join([rec.message for rec in caplog.records])
                assert "MATCH" in log_messages or "cypher" in log_messages.lower(), (
                    "Query execution should be logged for audit trail"
                )
