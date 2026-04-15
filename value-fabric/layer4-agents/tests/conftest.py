"""Pytest configuration for Layer 4 Agents tests.

Requires package to be installed in editable mode:
    pip install -e value-fabric/layer4-agents
"""

import sys
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

from unittest.mock import AsyncMock, MagicMock, Mock


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


# ── Checkpoint/Resume Test Fixtures ─────────────────────────────────────────
# These fixtures reduce duplication in test_checkpoint_resume.py

from datetime import UTC, datetime
from typing import Any

import pytest_asyncio
from langgraph.checkpoint.memory import InMemorySaver

from src.engine.executor import OrchestrationController
from src.engine.state_manager import StateManager
from src.models.agent_state import BaseAgentState, WorkflowStatus

TEST_WORKFLOW_TYPE = "roi_calculator"


class MockCheckpointSaver(InMemorySaver):
    """Mock checkpoint saver extending InMemorySaver for testing.

    InMemorySaver provides full BaseCheckpointSaver implementation
    with in-memory storage - perfect for testing without Postgres.
    """

    @property
    def checkpoints(self) -> dict[str, Any]:
        """Expose underlying storage for test assertions."""
        return getattr(self, 'storage', {})

    @property
    def saved_threads(self) -> set:
        """Expose saved thread IDs for test assertions."""
        return set(self.checkpoints.keys())


@pytest.fixture
def mock_checkpoint_saver() -> MockCheckpointSaver:
    """Provide mock checkpoint saver."""
    return MockCheckpointSaver()


@pytest.fixture
def state_manager() -> StateManager:
    """Provide fresh StateManager instance."""
    return StateManager()


@pytest_asyncio.fixture
async def orchestrator_with_checkpoint(
    mock_tool_registry: Mock,
    mock_checkpoint_saver: MockCheckpointSaver
) -> OrchestrationController:
    """Provide OrchestrationController with checkpointing enabled."""
    state_manager = StateManager()
    controller = OrchestrationController(
        tool_registry=mock_tool_registry,
        state_manager=state_manager,
        checkpoint_saver=mock_checkpoint_saver
    )
    await controller.start()
    yield controller
    await controller.stop()


@pytest.fixture
def controller_with_running_state(
    mock_tool_registry: Mock,
    mock_checkpoint_saver: MockCheckpointSaver,
    state_manager: StateManager
) -> tuple[OrchestrationController, str, BaseAgentState]:
    """Provide controller with pre-existing running workflow state.

    Returns:
        Tuple of (controller, workflow_id, existing_state)
    """
    workflow_id = "test-resume-wf"
    existing_state = BaseAgentState(
        workflow_id=workflow_id,
        workflow_type=TEST_WORKFLOW_TYPE,
        status=WorkflowStatus.RUNNING,
        current_node="middle",
        input_data={"test": "data"},
        output_data={"start": {"status": "completed"}},
        errors=[]
    )

    controller = OrchestrationController(
        tool_registry=mock_tool_registry,
        state_manager=state_manager,
        checkpoint_saver=mock_checkpoint_saver
    )
    controller._workflow_metadata[workflow_id] = {
        "workflow_type": TEST_WORKFLOW_TYPE,
        "started_at": datetime.now(UTC).isoformat()
    }

    return controller, workflow_id, existing_state


@pytest.fixture
def controller_with_paused_state(
    mock_tool_registry: Mock,
    mock_checkpoint_saver: MockCheckpointSaver,
    state_manager: StateManager
) -> tuple[OrchestrationController, str, BaseAgentState]:
    """Provide controller with pre-existing paused workflow state.

    Returns:
        Tuple of (controller, workflow_id, initial_state)
    """
    workflow_id = "lifecycle-wf"
    initial_state = BaseAgentState(
        workflow_id=workflow_id,
        workflow_type=TEST_WORKFLOW_TYPE,
        status=WorkflowStatus.PAUSED,
        current_node="middle",
        input_data={"test": "lifecycle"},
        output_data={"start": {"status": "completed"}},
        errors=[]
    )

    controller = OrchestrationController(
        tool_registry=mock_tool_registry,
        state_manager=state_manager,
        checkpoint_saver=mock_checkpoint_saver
    )
    controller._workflow_metadata[workflow_id] = {
        "workflow_type": TEST_WORKFLOW_TYPE,
        "started_at": datetime.now(UTC).isoformat()
    }

    return controller, workflow_id, initial_state


@pytest.fixture
def completed_workflow_state() -> BaseAgentState:
    """Provide a completed workflow state fixture."""
    return BaseAgentState(
        workflow_id="completed-wf",
        workflow_type=TEST_WORKFLOW_TYPE,
        status=WorkflowStatus.COMPLETED,
        input_data={},
        output_data={},
        errors=[]
    )
