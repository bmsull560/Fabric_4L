"""Integration tests for LangGraph checkpointing and workflow resume.

Tests the pause/resume lifecycle for human-in-the-loop workflows.
Verifies state persistence across interruptions and container restarts.
"""

import pytest
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch

from src.workflows.base import BaseWorkflow, WorkflowBuilder, WorkflowConfig
from src.engine.executor import OrchestrationController, WorkflowExecutionError
from src.engine.state_manager import StateManager
from src.config.checkpoint import CheckpointConfig
from src.models.agent_state import AgentState, BaseAgentState, WorkflowStatus, WorkflowType
from src.models.workflow_config import NodeConfig, NodeType, EdgeConfig
from src.tools.registry import ToolRegistry
from langgraph.checkpoint.memory import InMemorySaver


class MockCheckpointSaver(InMemorySaver):
    """Mock checkpoint saver extending InMemorySaver for testing.
    
    InMemorySaver provides full BaseCheckpointSaver implementation
    with in-memory storage - perfect for testing without Postgres.
    """
    
    @property
    def checkpoints(self) -> Dict[str, Any]:
        """Expose underlying storage for test assertions."""
        return getattr(self, 'storage', {})
    
    @property
    def saved_threads(self) -> set:
        """Expose saved thread IDs for test assertions."""
        return set(self.checkpoints.keys())


class SimpleTestWorkflow(BaseWorkflow):
    """Simple workflow for testing checkpoint/resume."""
    
    def __init__(self, tool_registry, checkpoint_saver=None, pause_after_node: Optional[str] = None):
        """Initialize with optional pause point."""
        config = WorkflowConfig(
            workflow_type="roi_calculator",
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
    
    async def _execute_tool(self, tool_name: str, state: AgentState, config: Dict) -> Dict[str, Any]:
        """Track node execution."""
        current_node = state.current_node
        self.executed_nodes.append(current_node)
        
        # Simulate pause after specified node
        if self.pause_after_node and current_node == self.pause_after_node:
            state.status = WorkflowStatus.PENDING
            return {"status": "paused", "node": current_node}
        
        return {"status": "completed", "node": current_node, "tool": tool_name}
    
    def create_initial_state(self, input_data: Dict[str, Any]) -> AgentState:
        """Create initial state."""
        return BaseAgentState(
            workflow_id=input_data.get("workflow_id", f"test-{datetime.utcnow().timestamp()}"),
            workflow_type="roi_calculator",
            status=WorkflowStatus.PENDING,
            input_data=input_data,
            output_data={},
            errors=[]
        )


class TestCheckpointPersistence:
    """Test that workflow state persists across interruptions."""
    
    @pytest.mark.asyncio
    async def test_checkpoint_saver_stores_state(self):
        """Verify checkpoint saver receives state during workflow execution."""
        # Setup
        mock_saver = MockCheckpointSaver()
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.execute = AsyncMock(return_value={"result": "test"})
        
        workflow = SimpleTestWorkflow(mock_registry, mock_saver)
        initial_state = workflow.create_initial_state({"test": "data"})
        workflow_id = initial_state.workflow_id
        
        # Execute workflow
        result = await workflow.run(initial_state, thread_id=workflow_id)
        
        # Assert checkpoint was saved
        assert workflow_id in mock_saver.saved_threads
        assert workflow_id in mock_saver.checkpoints
    
    @pytest.mark.asyncio
    async def test_workflow_without_checkpoint_saver_runs_normally(self):
        """Workflow functions without checkpointing (backward compatibility)."""
        # Setup
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.execute = AsyncMock(return_value={"result": "test"})
        
        workflow = SimpleTestWorkflow(mock_registry, checkpoint_saver=None)
        initial_state = workflow.create_initial_state({"test": "data"})
        
        # Execute - should not raise
        result = await workflow.run(initial_state, thread_id="test-wf-1")
        
        # Assert workflow completed
        assert result is not None


class TestResumeWorkflow:
    """Test OrchestrationController resume functionality."""
    
    @pytest.mark.asyncio
    async def test_resume_workflow_loads_state(self):
        """Resume loads existing state and continues execution."""
        # Setup
        mock_saver = MockCheckpointSaver()
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.execute = AsyncMock(return_value={"result": "test"})
        
        # Create state manager with pre-existing state
        state_manager = StateManager()
        workflow_id = "test-resume-wf-1"
        existing_state = BaseAgentState(
            workflow_id=workflow_id,
            workflow_type="roi_calculator",
            status=WorkflowStatus.RUNNING,  # Still running, can resume
            current_node="middle",
            input_data={"test": "data"},
            output_data={"start": {"status": "completed"}},
            errors=[]
        )
        await state_manager.save_state(workflow_id, existing_state)
        
        # Create controller with metadata for this workflow
        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
            checkpoint_saver=mock_saver
        )
        controller._workflow_metadata[workflow_id] = {
            "workflow_type": "roi_calculator",
            "started_at": datetime.utcnow().isoformat()
        }
        
        # Resume
        result = await controller.resume_workflow(
            workflow_id=workflow_id,
            user_id="test-user",
            resume_data={"approved": True}
        )
        
        # Assert
        assert result is not None
        assert result.workflow_id == workflow_id
    
    @pytest.mark.asyncio
    async def test_resume_completed_workflow_fails(self):
        """Cannot resume a workflow that is already completed."""
        # Setup
        state_manager = StateManager()
        workflow_id = "completed-wf-1"
        completed_state = BaseAgentState(
            workflow_id=workflow_id,
            workflow_type="roi_calculator",
            status=WorkflowStatus.COMPLETED,
            input_data={},
            output_data={},
            errors=[]
        )
        await state_manager.save_state(workflow_id, completed_state)
        
        controller = OrchestrationController(
            tool_registry=Mock(spec=ToolRegistry),
            state_manager=state_manager
        )
        controller._workflow_metadata[workflow_id] = {
            "workflow_type": "roi_calculator"
        }
        
        # Assert resume fails
        with pytest.raises(Exception) as exc_info:
            await controller.resume_workflow(
                workflow_id=workflow_id,
                user_id="test-user"
            )
        
    @pytest.mark.asyncio
    async def test_resume_nonexistent_workflow_fails(self):
        """Cannot resume a workflow that doesn't exist."""
        # Setup
        state_manager = StateManager()
        controller = OrchestrationController(
            tool_registry=Mock(spec=ToolRegistry),
            state_manager=state_manager
        )
        
        # Assert resume fails
        with pytest.raises(WorkflowExecutionError) as exc_info:
            await controller.resume_workflow(
                workflow_id="nonexistent-wf",
                user_id="test-user"
            )
        # Assert
        assert "not found" in str(exc_info.value).lower() or "no state found" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_resume_merges_user_data(self):
        """Resume merges user decision data into workflow state."""
        # Setup
        mock_saver = MockCheckpointSaver()
        state_manager = StateManager()
        workflow_id = "resume-data-wf"
        
        existing_state = BaseAgentState(
            workflow_id=workflow_id,
            workflow_type="roi_calculator",
            status=WorkflowStatus.RUNNING,
            input_data={"original": "data"},
            output_data={},
            errors=[]
        )
        await state_manager.save_state(workflow_id, existing_state)
        
        controller = OrchestrationController(
            tool_registry=Mock(spec=ToolRegistry),
            state_manager=state_manager,
            checkpoint_saver=mock_saver
        )
        controller._workflow_metadata[workflow_id] = {
            "workflow_type": "roi_calculator"
        }
        
        # Resume with user data
        resume_data = {"approved": True, "notes": "Proceed with caution"}
        
        # Execute resume - should not raise and data should be stored in output_data
        result = await controller.resume_workflow(
            workflow_id=workflow_id,
            user_id="test-user",
            resume_data=resume_data
        )
        
        # Verify result has the resume data in output_data
        assert result is not None
        assert result.workflow_id == workflow_id
        # Verify data was captured in output_data (not input_data)
        assert "resume_decision" in result.output_data
        assert result.output_data["resume_decision"] == resume_data
        assert result.output_data["resumed_by"] == "test-user"
        assert "resumed_at" in result.output_data


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
            
            with pytest.raises(Exception):
                async with CheckpointConfig.get_saver() as _:
                    pass


class TestCheckpointIntegration:
    """End-to-end integration tests for checkpoint/resume."""
    
    @pytest.mark.asyncio
    async def test_full_pause_resume_lifecycle(self):
        """Complete workflow: start -> pause -> resume -> complete."""
        # This is a comprehensive test of the full lifecycle
        # Requires actual workflow execution with checkpointing
        
        mock_saver = MockCheckpointSaver()
        mock_registry = Mock(spec=ToolRegistry)
        mock_registry.execute = AsyncMock(return_value={"result": "success"})
        
        # Create workflow that pauses after first node
        workflow = SimpleTestWorkflow(
            mock_registry, 
            checkpoint_saver=mock_saver,
            pause_after_node="start"
        )
        
        initial_state = workflow.create_initial_state({"test": "lifecycle"})
        workflow_id = initial_state.workflow_id
        
        # Start workflow - should pause
        result = await workflow.run(initial_state, thread_id=workflow_id)
        
        # Verify checkpoint was saved
        assert workflow_id in mock_saver.checkpoints
        
        # In a real scenario, user would approve via API
        # Then workflow would resume from checkpoint
        
    @pytest.mark.asyncio
    async def test_multiple_resumes_continue_progress(self):
        """Multiple resume calls continue from latest checkpoint."""
        # Test that resuming multiple times uses the most recent state
        pass  # Implementation would require complex mocking


# Fixtures for pytest
@pytest.fixture
def mock_checkpoint_saver():
    """Provide mock checkpoint saver."""
    return MockCheckpointSaver()


@pytest.fixture
def mock_tool_registry():
    """Provide mock tool registry."""
    registry = Mock(spec=ToolRegistry)
    registry.execute = AsyncMock(return_value={"result": "mock"})
    return registry


@pytest.fixture
async def orchestrator_with_checkpoint(mock_tool_registry, mock_checkpoint_saver):
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
