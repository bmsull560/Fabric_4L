"""Pytest configuration for Layer 4 Agents tests.

Adds layer4-agents and value-fabric directories to PYTHONPATH so that
``from src.…`` and ``from shared.…`` imports resolve correctly.
"""

import os
import sys

import pytest

# ── Path setup ──────────────────────────────────────────────────────────────
tests_dir = os.path.dirname(os.path.abspath(__file__))
layer4_dir = os.path.dirname(tests_dir)
value_fabric_dir = os.path.dirname(layer4_dir)

if layer4_dir not in sys.path:
    sys.path.insert(0, layer4_dir)
if value_fabric_dir not in sys.path:
    sys.path.insert(0, value_fabric_dir)


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
