"""Pytest configuration for Layer 4 Agents tests.

Requires package to be installed in editable mode:
    pip install -e value-fabric/layer4-agents
"""

import pytest


# ── Fixtures ────────────────────────────────────────────────────────────────
@pytest.fixture
def inmemory_checkpointer():
    """Provide LangGraph InMemorySaver for fast checkpoint testing."""
    try:
        from langgraph.checkpoint.memory import InMemorySaver
        return InMemorySaver()
    except ImportError:
        pytest.skip("langgraph InMemorySaver not available")


@pytest.fixture(scope="session")
def redis_container():
    """Provide Redis container for integration tests (requires Docker)."""
    try:
        from testcontainers.redis import RedisContainer
        with RedisContainer("redis:7-alpine") as redis:
            yield redis.get_connection_url()
    except Exception as e:
        pytest.skip(f"Redis container not available: {e}")
