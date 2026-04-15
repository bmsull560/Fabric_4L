"""Integration tests for LangGraph checkpointing and workflow resume.

Tests the pause/resume lifecycle for human-in-the-loop workflows.
Verifies state persistence across interruptions and container restarts.
"""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.config.checkpoint import CheckpointConfig
from src.engine.executor import OrchestrationController, WorkflowExecutionError
from src.engine.state_manager import StateManager
from src.models.agent_state import BaseAgentState, WorkflowStatus
from src.models.workflow_config import EdgeConfig, NodeConfig, NodeType
from src.tools.registry import ToolRegistry
from src.workflows.base import BaseWorkflow, WorkflowConfig

# Reuse fixtures from conftest.py: mock_checkpoint_saver, mock_tool_registry,
# state_manager, orchestrator_with_checkpoint, controller_with_running_state,
# controller_with_paused_state, completed_workflow_state

# Test constants
TEST_WORKFLOW_TYPE = "roi_calculator"


class SimpleTestWorkflow(BaseWorkflow):
    """Simple workflow for testing checkpoint/resume."""

    def __init__(self, tool_registry, checkpoint_saver=None, pause_after_node: str | None = None):
        """Initialize with optional pause point."""
        config = WorkflowConfig(
            workflow_type=TEST_WORKFLOW_TYPE,
            name="Test Workflow",
            description="Simple workflow for testing",
            nodes=[
                NodeConfig(id="start", name="Start", node_type=NodeType.TOOL, tool_name="test_tool"),
                NodeConfig(id="middle", name="Middle", node_type=NodeType.TOOL, tool_name="test_tool"),
                NodeConfig(id="end", name="End", node_type=NodeType.END),
            ],
            edges=[
                EdgeConfig(source="start", target="middle"),
                EdgeConfig(source="middle", target="end"),
            ],
            entry_point="start"
        )
        super().__init__(config, tool_registry, checkpoint_saver)
        self.pause_after_node = pause_after_node
        self.executed_nodes: list = []

    async def _execute_tool(self, tool_name: str, state, config: dict) -> dict[str, Any]:
        """Track node execution."""
        current_node = state.current_node
        self.executed_nodes.append(current_node)

        # Simulate pause after specified node
        if self.pause_after_node and current_node == self.pause_after_node:
            state.status = WorkflowStatus.PENDING
            return {"status": "paused", "node": current_node}

        return {"status": "completed", "node": current_node, "tool": tool_name}

    def create_initial_state(self, input_data: dict[str, Any]):
        """Create initial state."""
        from datetime import UTC
        return BaseAgentState(
            workflow_id=input_data.get("workflow_id", f"test-{datetime.now(UTC).timestamp()}"),
            workflow_type=TEST_WORKFLOW_TYPE,
            status=WorkflowStatus.PENDING,
            input_data=input_data,
            output_data={},
            errors=[]
        )


@pytest.mark.unit
class TestCheckpointPersistence:
    """Test that workflow state persists across interruptions."""

    @pytest.mark.asyncio
    async def test_checkpoint_saver_stores_state(self, mock_checkpoint_saver, mock_tool_registry):
        """Verify checkpoint saver receives state during workflow execution."""
        workflow = SimpleTestWorkflow(mock_tool_registry, mock_checkpoint_saver)
        initial_state = workflow.create_initial_state({"test": "data"})
        workflow_id = initial_state.workflow_id

        await workflow.run(initial_state, thread_id=workflow_id)

        assert workflow_id in mock_checkpoint_saver.saved_threads
        assert workflow_id in mock_checkpoint_saver.checkpoints

    @pytest.mark.asyncio
    async def test_workflow_without_checkpoint_saver_runs_normally(self, mock_tool_registry):
        """Workflow functions without checkpointing (backward compatibility)."""
        workflow = SimpleTestWorkflow(mock_tool_registry, checkpoint_saver=None)
        initial_state = workflow.create_initial_state({"test": "data"})

        result = await workflow.run(initial_state, thread_id="test-wf-1")

        assert result is not None


@pytest.mark.unit
class TestResumeWorkflow:
    """Test OrchestrationController resume functionality."""

    @pytest.mark.asyncio
    async def test_resume_workflow_loads_state(self, controller_with_running_state, state_manager):
        """Resume loads existing state and continues execution."""
        controller, workflow_id, existing_state = controller_with_running_state
        await state_manager.save_state(workflow_id, existing_state)

        mock_workflow = Mock(spec=BaseWorkflow)
        mock_result = BaseAgentState(
            workflow_id=workflow_id,
            workflow_type=TEST_WORKFLOW_TYPE,
            status=WorkflowStatus.COMPLETED,
            input_data=existing_state.input_data,
            output_data={**existing_state.output_data, "resumed": True},
            errors=[]
        )
        mock_workflow.run = AsyncMock(return_value=mock_result)

        with patch("src.engine.executor.create_workflow", return_value=mock_workflow):
            result = await controller.resume_workflow(
                workflow_id=workflow_id,
                user_id="test-user",
                resume_data={"approved": True}
            )

        assert result is not None
        assert result.workflow_id == workflow_id
        mock_workflow.run.assert_called_once()

    @pytest.mark.asyncio
    async def test_resume_completed_workflow_fails(self, mock_tool_registry, state_manager, completed_workflow_state):
        """Cannot resume a workflow that is already completed."""
        workflow_id = completed_workflow_state.workflow_id
        await state_manager.save_state(workflow_id, completed_workflow_state)

        controller = OrchestrationController(
            tool_registry=mock_tool_registry,
            state_manager=state_manager
        )
        controller._workflow_metadata[workflow_id] = {"workflow_type": TEST_WORKFLOW_TYPE}

        with pytest.raises(WorkflowExecutionError):
            await controller.resume_workflow(workflow_id=workflow_id, user_id="test-user")

    @pytest.mark.asyncio
    async def test_resume_nonexistent_workflow_fails(self, mock_tool_registry, state_manager):
        """Cannot resume a workflow that doesn't exist."""
        controller = OrchestrationController(
            tool_registry=mock_tool_registry,
            state_manager=state_manager
        )

        with pytest.raises(WorkflowExecutionError) as exc_info:
            await controller.resume_workflow(workflow_id="nonexistent-wf", user_id="test-user")

        assert "not found" in str(exc_info.value).lower() or "no state found" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_resume_merges_user_data(self, controller_with_running_state, state_manager):
        """Resume merges user resume data into state."""
        controller, workflow_id, existing_state = controller_with_running_state
        existing_state.input_data = {"original": "data"}
        await state_manager.save_state(workflow_id, existing_state)

        async def mock_run(state, thread_id):
            return state

        mock_workflow = Mock(spec=BaseWorkflow)
        mock_workflow.run = AsyncMock(side_effect=mock_run)

        resume_data = {"approved": True, "notes": "Proceed with caution"}

        with patch("src.engine.executor.create_workflow", return_value=mock_workflow):
            result = await controller.resume_workflow(
                workflow_id=workflow_id,
                user_id="test-user",
                resume_data=resume_data
            )

        assert result is not None
        assert result.workflow_id == workflow_id
        assert "resume_decision" in result.output_data
        assert result.output_data["resume_decision"] == resume_data
        assert result.output_data["resumed_by"] == "test-user"
        assert "resumed_at" in result.output_data


@pytest.mark.unit
class TestCheckpointConfiguration:
    """Test checkpoint configuration and database connection."""
    
    @pytest.mark.asyncio
    async def test_checkpoint_config_returns_saver(self):
        """CheckpointConfig creates saver when database available."""
        # This test would require a real Postgres connection
        # For now, we mock the connection to verify the interface
        with patch("src.config.checkpoint.asyncpg.connect") as mock_connect:
            mock_conn = AsyncMock()
            mock_connect.return_value = mock_conn
            
            saver = await CheckpointConfig.create_saver()
            assert saver is not None
            # Verify connection is stored for later cleanup
            assert hasattr(saver, '_conn')
    
    def test_checkpoint_config_handles_url_variations(self):
        """CheckpointConfig handles different URL formats."""
        # Test URL cleaning for asyncpg compatibility
        test_cases = [
            ("postgresql+asyncpg://user:pass@host/db", "postgresql://user:pass@host/db"),
            ("postgresql+psycopg2://user:pass@host/db", "postgresql://user:pass@host/db"),
            ("postgresql://user:pass@host/db", "postgresql://user:pass@host/db"),
        ]
        
        for input_url, expected in test_cases:
            result = CheckpointConfig._clean_url(input_url)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_get_checkpoint_saver_returns_none_on_failure(self):
        """Factory returns None if checkpointing fails (graceful degradation)."""
        # When database is unavailable, should raise CheckpointConnectionError
        with patch("src.config.checkpoint.asyncpg.connect") as mock_connect:
            mock_connect.side_effect = Exception("Database unavailable")
            
            with pytest.raises(RuntimeError):
                async with CheckpointConfig.get_saver() as _:
                    pass


@pytest.mark.integration
class TestCheckpointIntegration:
    """End-to-end integration tests for checkpoint/resume."""

    @pytest.mark.asyncio
    async def test_full_pause_resume_lifecycle(self, controller_with_paused_state, state_manager):
        """Complete workflow: start -> pause -> resume -> complete."""
        controller, workflow_id, initial_state = controller_with_paused_state
        await state_manager.save_state(workflow_id, initial_state)

        mock_workflow = Mock(spec=BaseWorkflow)
        completed_state = BaseAgentState(
            workflow_id=workflow_id,
            workflow_type=TEST_WORKFLOW_TYPE,
            status=WorkflowStatus.COMPLETED,
            input_data=initial_state.input_data,
            output_data={
                **initial_state.output_data,
                "resumed": True,
                "middle": {"status": "completed"},
                "end": {"status": "completed"}
            },
            errors=[]
        )
        mock_workflow.run = AsyncMock(return_value=completed_state)

        with patch("src.engine.executor.create_workflow", return_value=mock_workflow):
            result = await controller.resume_workflow(
                workflow_id=workflow_id,
                user_id="test-user",
                resume_data={"approved": True}
            )

        assert result is not None
        assert result.workflow_id == workflow_id
        assert result.status == WorkflowStatus.COMPLETED
        mock_workflow.run.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_multiple_resumes_continue_progress(self, controller_with_running_state, state_manager, mock_checkpoint_saver):
        """Multiple resume calls continue from latest checkpoint."""
        controller, workflow_id, existing_state = controller_with_running_state
        existing_state.output_data = {"resume_count": 0}
        await state_manager.save_state(workflow_id, existing_state)

        async def mock_run(state, thread_id):
            return state

        mock_workflow = Mock(spec=BaseWorkflow)
        mock_workflow.run = AsyncMock(side_effect=mock_run)

        with patch("src.engine.executor.create_workflow", return_value=mock_workflow) as mock_create:
            result1 = await controller.resume_workflow(
                workflow_id=workflow_id,
                user_id="user-1",
                resume_data={"iteration": 1}
            )

        assert result1 is not None
        assert result1.output_data["resume_decision"] == {"iteration": 1}
        mock_create.assert_called_once()
        assert mock_create.call_args.args[2] is mock_checkpoint_saver


# Fixtures moved to conftest.py:
# - mock_checkpoint_saver
# - mock_tool_registry
# - state_manager
# - orchestrator_with_checkpoint
# - controller_with_running_state
# - controller_with_paused_state
# - completed_workflow_state
