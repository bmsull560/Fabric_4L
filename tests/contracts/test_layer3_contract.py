"""
Contract Tests for Layer 3 Knowledge Graph API

Validates that the implementation matches the OpenAPI specification.
These tests verify endpoints exist and return expected status codes.
"""

import pytest
from httpx import AsyncClient


# ============================================================================
# Entity Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_entity_traverse_endpoint_exists(client: AsyncClient):
    """Verify POST /v1/entity/traverse is implemented and returns valid response."""
    response = await client.post(
        "/v1/entity/traverse",
        json={
            "entity_id": "test-entity-123",
            "direction": "downward",
            "max_depth": 3
        }
    )
    # Should not be 404 (not found) - we accept 200, 400, or 422 as valid
    assert response.status_code != 404, "Entity traverse endpoint should exist"
    assert response.status_code in [200, 400, 422], \
        f"Expected 200, 400, or 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_entity_context_endpoint_exists(client: AsyncClient):
    """Verify GET /v1/entity/{entity_id}/context is implemented."""
    response = await client.get(
        "/v1/entity/test-entity-123/context",
        params={"hops": 2, "limit": 50}
    )
    # Should not be 404 - endpoint should exist
    assert response.status_code != 404, "Entity context endpoint should exist"
    # We accept 200, 400, 404 (entity not found), or 422
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected 200, 400, 404, or 422, got {response.status_code}"


# ============================================================================
# Search Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_hybrid_search_endpoint_exists(client: AsyncClient):
    """Verify POST /v1/search/hybrid is implemented."""
    response = await client.post(
        "/v1/search/hybrid",
        json={"query": "test query", "limit": 10}
    )
    assert response.status_code != 404, "Hybrid search endpoint should exist"
    assert response.status_code in [200, 400, 422], \
        f"Expected 200, 400, or 422, got {response.status_code}"


# ============================================================================
# Value Tree Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_value_tree_get_endpoint_exists(client: AsyncClient):
    """Verify GET /v1/value-trees/{entity_id} is implemented."""
    response = await client.get("/v1/value-trees/test-entity-123")
    assert response.status_code != 404, "Value tree endpoint should exist"
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected 200, 400, 404, or 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_value_tree_paths_endpoint_exists(client: AsyncClient):
    """Verify GET /v1/value-trees/{entity_id}/paths is implemented."""
    response = await client.get("/v1/value-trees/test-entity-123/paths")
    assert response.status_code != 404, "Value tree paths endpoint should exist"
    assert response.status_code in [200, 400, 404, 422], \
        f"Expected 200, 400, 404, or 422, got {response.status_code}"


# ============================================================================
# Formula Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_formulas_list_endpoint_exists(client: AsyncClient):
    """Verify GET /v1/formulas is implemented."""
    response = await client.get("/v1/formulas")
    assert response.status_code != 404, "Formulas list endpoint should exist"
    assert response.status_code in [200, 400, 422], \
        f"Expected 200, 400, or 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_formula_evaluate_endpoint_exists(client: AsyncClient):
    """Verify POST /v1/formulas/evaluate is implemented."""
    response = await client.post(
        "/v1/formulas/evaluate",
        json={"formula": "a + b", "variables": {"a": 1, "b": 2}}
    )
    assert response.status_code != 404, "Formula evaluate endpoint should exist"
    assert response.status_code in [200, 400, 422], \
        f"Expected 200, 400, or 422, got {response.status_code}"


# ============================================================================
# Analytics Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_analytics_communities_endpoint_exists(client: AsyncClient):
    """Verify POST /v1/analytics/communities is implemented."""
    response = await client.post(
        "/v1/analytics/communities",
        json={"entity_types": ["UseCase"]}
    )
    assert response.status_code != 404, "Communities endpoint should exist"
    assert response.status_code in [200, 400, 422], \
        f"Expected 200, 400, or 422, got {response.status_code}"


@pytest.mark.asyncio
async def test_analytics_centrality_endpoint_exists(client: AsyncClient):
    """Verify POST /v1/analytics/centrality is implemented."""
    response = await client.post(
        "/v1/analytics/centrality",
        json={"entity_ids": ["test-1", "test-2"]}
    )
    assert response.status_code != 404, "Centrality endpoint should exist"
    assert response.status_code in [200, 400, 422], \
        f"Expected 200, 400, or 422, got {response.status_code}"


# ============================================================================
# GraphRAG Endpoints
# ============================================================================

@pytest.mark.asyncio
async def test_graphrag_query_endpoint_exists(client: AsyncClient):
    """Verify POST /v1/graphrag is implemented."""
    response = await client.post(
        "/v1/graphrag",
        json={"question": "What is the ROI of CRM integration?"}
    )
    assert response.status_code != 404, "GraphRAG endpoint should exist"
    assert response.status_code in [200, 400, 422], \
        f"Expected 200, 400, or 422, got {response.status_code}"


# ============================================================================
# Health Endpoint
# ============================================================================

@pytest.mark.asyncio
async def test_health_endpoint_exists(client: AsyncClient):
    """Verify GET /health is implemented."""
    response = await client.get("/health")
    assert response.status_code == 200, "Health endpoint should return 200"
