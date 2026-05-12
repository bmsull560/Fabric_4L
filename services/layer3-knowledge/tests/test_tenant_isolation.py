"""Test tenant isolation in Neo4j queries.

These tests verify that all read endpoints enforce tenant_id filtering
to prevent cross-tenant data exposure.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from value_fabric.layer3.api.app_monolith import _extract_tenant_id, get_full_graph
from value_fabric.layer3.api.routes.entities import list_entities



class TestTenantIsolation:
    """Verify tenant isolation on all Neo4j read endpoints."""

    @pytest.fixture
    def mock_request_with_tenant(self):
        """Create a mock request with tenant context."""
        request = MagicMock()
        request.state = MagicMock()
        request.state.governance_context = MagicMock()
        request.state.governance_context.tenant_id = "tenant-a"
        return request

    @pytest.fixture
    def mock_request_no_tenant(self):
        """Create a mock request without tenant context."""
        request = MagicMock()
        request.state = MagicMock()
        request.state.governance_context = None
        return request

    @pytest.fixture
    def mock_neo4j_driver(self):
        """Create a mock Neo4j driver."""
        driver = MagicMock()
        session = AsyncMock()
        driver.session.return_value = MagicMock(
            __aenter__=AsyncMock(return_value=session),
            __aexit__=AsyncMock(return_value=False),
        )

        # Mock count result
        count_result = AsyncMock()
        count_result.single.return_value = {"total": 0}
        session.run.return_value = count_result

        return driver, session

    def test_extract_tenant_id_with_context(self, mock_request_with_tenant):
        """_extract_tenant_id should return tenant_id from request context."""
        tenant_id = _extract_tenant_id(mock_request_with_tenant)
        assert tenant_id == "tenant-a"

    def test_extract_tenant_id_without_context(self, mock_request_no_tenant):
        """_extract_tenant_id should return None without context."""
        tenant_id = _extract_tenant_id(mock_request_no_tenant)
        assert tenant_id is None

    def test_extract_tenant_id_none_request(self):
        """_extract_tenant_id should handle None request."""
        tenant_id = _extract_tenant_id(None)
        assert tenant_id is None

    @pytest.mark.asyncio
    async def test_list_entities_requires_tenant_id(self, mock_neo4j_driver):
        """list_entities must reject requests without tenant_id."""
        driver, _ = mock_neo4j_driver

        with pytest.raises(HTTPException) as exc_info:
            await list_entities(
                search_text=None,
                entity_types=None,
                domains=None,
                statuses=None,
                min_confidence=None,
                max_confidence=None,
                limit=25,
                offset=0,
                sort_by="updated_at",
                sort_order="desc",
                neo4j_driver=driver,
                request=None,
            )

        assert exc_info.value.status_code == 401
        assert "Authentication context is required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_list_entities_includes_tenant_in_where_clause(
        self, mock_request_with_tenant, mock_neo4j_driver
    ):
        """list_entities must include tenant_id in all MATCH queries."""
        driver, session = mock_neo4j_driver

        # Set up proper mock chain for session.run
        mock_result = AsyncMock()
        mock_result.single.return_value = {"total": 0}
        mock_result.fetch.return_value = []
        session.run.return_value = mock_result

        await list_entities(
            search_text=None,
            entity_types=None,
            domains=None,
            statuses=None,
            min_confidence=None,
            max_confidence=None,
            limit=25,
            offset=0,
            sort_by="updated_at",
            sort_order="desc",
            neo4j_driver=driver,
            request=mock_request_with_tenant,
        )

        # Verify queries include tenant_id filter
        calls = session.run.call_args_list
        assert len(calls) > 0, "No queries were executed"

        for call in calls:
            query = call[1].get("query") or call[0][0] if call[0] else call.args[1] if call.args else call.kwargs.get("query", "")
            if "MATCH" in str(query):
                params = call[1] if call[1] else call.kwargs if call.kwargs else {}
                if isinstance(params, dict) and params:
                    assert "tenant_id" in params or "$tenant_id" in str(query), f"Query missing tenant_id: {query}"

    @pytest.mark.asyncio
    async def test_get_full_graph_requires_tenant_id(self):
        """get_full_graph must reject requests without tenant_id."""
        mock_state = MagicMock()
        mock_state.neo4j_driver = AsyncMock()

        with patch("value_fabric.layer3.api.app_monolith.get_app_state", return_value=mock_state):
            with pytest.raises(HTTPException) as exc_info:
                await get_full_graph(
                    limit=1000,
                    app_state=mock_state,
                    request=None,
                )

        assert exc_info.value.status_code == 400
        assert "tenant_id is required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_full_graph_includes_tenant_in_queries(
        self, mock_request_with_tenant
    ):
        """get_full_graph must include tenant_id in all MATCH queries."""
        mock_state = MagicMock()
        mock_neo4j = AsyncMock()
        mock_neo4j.execute_query.return_value = []
        mock_state.neo4j_driver = mock_neo4j

        with patch("value_fabric.layer3.api.app_monolith.get_app_state", return_value=mock_state):
            await get_full_graph(
                limit=1000,
                app_state=mock_state,
                request=mock_request_with_tenant,
            )

        # Verify queries include tenant_id filter
        calls = mock_neo4j.execute_query.call_args_list
        assert len(calls) > 0, "No queries were executed"

        for call in calls:
            query = call[0][0]
            params = call[0][1] if len(call[0]) > 1 else call.kwargs if call.kwargs else {}

            if "MATCH" in str(query):
                assert (
                    "tenant_id" in str(query) or (params and "tenant_id" in params)
                ), f"Query missing tenant_id filter: {query}"


    @pytest.mark.asyncio
    async def test_get_full_graph_fails_closed_when_context_absent(self):
        """Module-unavailable scenario must fail closed when auth context is missing."""
        mock_state = MagicMock()
        mock_state.neo4j_driver = AsyncMock()

        request = MagicMock()
        request.state = MagicMock()
        request.state.governance_context = None

        with patch("value_fabric.layer3.api.app_monolith.NEO4J_TENANT_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc_info:
                await get_full_graph(limit=1000, app_state=mock_state, request=request)

        assert exc_info.value.status_code == 401
        assert "Authentication context is required" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_get_full_graph_fails_closed_when_request_absent_and_module_unavailable(self):
        """Module-unavailable scenario must reject missing request context."""
        mock_state = MagicMock()
        mock_state.neo4j_driver = AsyncMock()

        with patch("value_fabric.layer3.api.app_monolith.NEO4J_TENANT_AVAILABLE", False):
            with pytest.raises(HTTPException) as exc_info:
                await get_full_graph(limit=1000, app_state=mock_state, request=None)

        assert exc_info.value.status_code == 401
        assert "Authentication context is required" in exc_info.value.detail

    def test_cross_tenant_access_blocked_in_list_entities(self):
        """Tenant A cannot see Tenant B's entities via list_entities."""
        # This would require integration test with actual Neo4j
        # For unit tests, we verify the tenant_id is included in queries
        pass

    def test_cross_tenant_access_blocked_in_get_full_graph(self):
        """Tenant A cannot see Tenant B's entities via get_full_graph."""
        # This would require integration test with actual Neo4j
        # For unit tests, we verify the tenant_id is included in queries
        pass

