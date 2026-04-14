"""Pytest configuration for Layer 4 Agents tests.

Requires package to be installed in editable mode:
    pip install -e value-fabric/layer4-agents
"""

import sys
import os
from pathlib import Path

# ── Path Setup ─────────────────────────────────────────────────────────────
# Add layer4-agents/src to path for imports when running tests directly
tests_dir = Path(__file__).parent
layer4_dir = tests_dir.parent
src_dir = layer4_dir / "src"

if str(layer4_dir) not in sys.path:
    sys.path.insert(0, str(layer4_dir))

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


# ── Workflow Test Fixtures ─────────────────────────────────────────────────
# These fixtures reduce boilerplate in workflow tests by providing
# pre-configured mocks for common dependencies.

from unittest.mock import Mock, AsyncMock, MagicMock


@pytest.fixture
def mock_tool_registry():
    """Create a mocked ToolRegistry for workflow testing.

    Returns a Mock spec'd to ToolRegistry with execute method as AsyncMock.
    Usage:
        def test_workflow(self, mock_tool_registry):
            mock_tool_registry.execute.return_value = {"result": "mocked"}
            workflow = BusinessCaseGeneratorWorkflow(tool_registry=mock_tool_registry)
    """
    from src.tools.registry import ToolRegistry
    registry = Mock(spec=ToolRegistry)
    registry.execute = AsyncMock()
    return registry


@pytest.fixture
def mock_openai_response():
    """Factory fixture for creating mock AsyncOpenAI responses."""
    def _make_response(content: str = "Mock LLM content") -> MagicMock:
        """Create a mock AsyncOpenAI chat completion response."""
        mock_choice = MagicMock()
        mock_choice.message.content = content
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response
    return _make_response


@pytest.fixture
def mock_openai_client(mock_openai_response):
    """Create a mocked AsyncOpenAI client for workflow testing.

    Returns a mock client with chat.completions.create as AsyncMock.
    Usage:
        def test_workflow(self, mock_openai_client):
            mock_openai_client.chat.completions.create.return_value = mock_openai_response("content")
            workflow = MyWorkflow(openai_client=mock_openai_client)
    """
    client = Mock()
    client.chat = Mock()
    client.chat.completions = Mock()
    client.chat.completions.create = AsyncMock()
    client.chat.completions.create.return_value = mock_openai_response("Mock LLM content")
    return client


@pytest.fixture
def business_case_workflow(mock_tool_registry, mock_openai_client):
    """Create a BusinessCaseGeneratorWorkflow with mocked dependencies.

    This fixture provides a workflow instance ready for testing with
    all external calls (LLM, tools) pre-mocked.
    """
    from src.workflows.business_case import BusinessCaseGeneratorWorkflow
    return BusinessCaseGeneratorWorkflow(
        tool_registry=mock_tool_registry,
        openai_client=mock_openai_client,
    )


@pytest.fixture
def roi_calculator_workflow(mock_tool_registry, mock_openai_client):
    """Create a ROICalculatorWorkflow with mocked dependencies."""
    from src.workflows.roi_calculator import ROICalculatorWorkflow
    return ROICalculatorWorkflow(
        tool_registry=mock_tool_registry,
        openai_client=mock_openai_client,
    )
