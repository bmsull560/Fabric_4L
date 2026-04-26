"""
Mocked fixtures for contract tests - enables CI execution without running services.

This module provides respx-based mocked fixtures that simulate Layer 3/4/5 API responses
for contract testing in CI environments where services are not running.

Usage:
    # In CI or when services unavailable:
    pytest tests/contract/ -v --mock-contracts

    # Or with environment variable:
    export CONTRACT_TEST_MODE=mock
    pytest tests/contract/ -v

Requires:
    pip install respx>=0.20.0
"""

import os
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient, Response

# Try to import respx, skip if not available
try:
    import respx
    from respx import mock
    RESPX_AVAILABLE = True
except ImportError:
    RESPX_AVAILABLE = False


def _is_mock_mode() -> bool:
    """Check if contract tests should run in mock mode."""
    return os.getenv("CONTRACT_TEST_MODE", "").lower() == "mock"


@pytest.fixture
def client() -> AsyncClient:
    """Create HTTP client for Layer 3 API contract tests.

    Uses LAYER3_API_URL environment variable, falls back to localhost:8003.
    When CONTRACT_TEST_MODE=mock, returns a mocked client.
    """
    if _is_mock_mode() and RESPX_AVAILABLE:
        # Return client that will be intercepted by respx mock router
        return AsyncClient(base_url="http://localhost:8003", timeout=10.0)

    # Default: real client (requires running service)
    base_url = os.getenv("LAYER3_API_URL", "http://localhost:8003").rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", "10.0"))
    return AsyncClient(base_url=base_url, timeout=timeout)


@pytest.fixture
def layer4_client() -> AsyncClient:
    """Create HTTP client for Layer 4 Agents API tests."""
    if _is_mock_mode() and RESPX_AVAILABLE:
        return AsyncClient(base_url="http://localhost:8004", timeout=10.0)

    base_url = os.getenv("LAYER4_API_URL", "http://localhost:8004").rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", "10.0"))
    return AsyncClient(base_url=base_url, timeout=timeout)


@pytest.fixture
def layer5_client() -> AsyncClient:
    """Create HTTP client for Layer 5 Ground Truth API tests."""
    if _is_mock_mode() and RESPX_AVAILABLE:
        return AsyncClient(base_url="http://localhost:8005", timeout=10.0)

    base_url = os.getenv("LAYER5_API_URL", "http://localhost:8005").rstrip("/")
    timeout = float(os.getenv("CONTRACT_TEST_TIMEOUT", "10.0"))
    return AsyncClient(base_url=base_url, timeout=timeout)


# Example respx mock configuration for L3 entity endpoints
@pytest.fixture
def mock_l3_entities():
    """Mock L3 entity endpoints for isolated contract testing.

    Usage:
        @pytest.mark.asyncio
        async def test_entity_endpoint(mock_l3_entities, client):
            # Test runs against mocked endpoint
            response = await client.get("/v1/entities/test-id")
            assert response.status_code == 200
    """
    if not RESPX_AVAILABLE:
        pytest.skip("respx not installed - run: pip install respx>=0.20.0")

    with respx.mock(base_url="http://localhost:8003") as router:
        # Mock entity traverse endpoint
        router.post("/v1/entity/traverse").mock(
            return_value=Response(
                200,
                json={
                    "nodes": [{"id": "test-entity-123", "type": "test"}],
                    "edges": []
                }
            )
        )

        # Mock entity context endpoint
        router.get(url__regex=r"/v1/entity/[^/]+/context").mock(
            return_value=Response(
                200,
                json={
                    "center": {"id": "test-entity-123"},
                    "neighbors": [],
                    "relationships": []
                }
            )
        )

        # Mock hybrid search endpoint
        router.post("/v1/search/hybrid").mock(
            return_value=Response(
                200,
                json={"results": [{"id": "result-1", "score": 0.95}]}
            )
        )

        yield router


# Example respx mock configuration for L4 workflow endpoints
@pytest.fixture
def mock_l4_workflows():
    """Mock L4 workflow endpoints for isolated contract testing."""
    if not RESPX_AVAILABLE:
        pytest.skip("respx not installed - run: pip install respx>=0.20.0")

    with respx.mock(base_url="http://localhost:8004") as router:
        router.post("/v1/workflows").mock(
            return_value=Response(
                201,
                json={"id": "workflow-123", "status": "created"}
            )
        )

        router.get(url__regex=r"/v1/workflows/[^/]+").mock(
            return_value=Response(
                200,
                json={"id": "workflow-123", "status": "running"}
            )
        )

        yield router


# Example respx mock configuration for L5 ground truth endpoints
@pytest.fixture
def mock_l5_ground_truth():
    """Mock L5 ground truth endpoints for isolated contract testing."""
    if not RESPX_AVAILABLE:
        pytest.skip("respx not installed - run: pip install respx>=0.20.0")

    with respx.mock(base_url="http://localhost:8005") as router:
        router.get("/v1/truth/entities").mock(
            return_value=Response(
                200,
                json={"entities": [{"id": "gt-entity-1", "verified": True}]}
            )
        )

        router.post("/v1/truth/verify").mock(
            return_value=Response(
                200,
                json={"verification_id": "vrf-123", "status": "verified"}
            )
        )

        yield router
