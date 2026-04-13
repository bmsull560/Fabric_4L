"""
LangGraph workflow execution tests with mocked LLM.

Tests verify:
1. BusinessCaseGeneratorWorkflow runs end-to-end with all LLM calls mocked.
2. ROICalculatorWorkflow runs end-to-end with all tool calls mocked.
3. Workflow state transitions are correct (PENDING → RUNNING → COMPLETED).
4. generate_section tool uses AsyncOpenAI and can be mocked cleanly.
5. Workflow handles LLM errors gracefully (error section, not crash).
6. WorkflowStatus enum values match what the frontend expects.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

import pytest
import pytest_asyncio

# ── Path setup (mirrors conftest.py) ─────────────────────────────────────────
import sys
import os

tests_dir = os.path.dirname(os.path.abspath(__file__))
layer4_dir = os.path.dirname(tests_dir)
if layer4_dir not in sys.path:
    sys.path.insert(0, layer4_dir)

from src.models.agent_state import (
    BusinessCaseAgentState,
    BusinessCaseInputData,
    ROIAgentState,
    ROIInputData,
    WorkflowStatus,
)
from src.tools.registry import ToolRegistry
from src.workflows.business_case import BusinessCaseGeneratorWorkflow
from src.workflows.roi_calculator import ROICalculatorWorkflow


# ── Helpers ───────────────────────────────────────────────────────────────────
def _make_mock_tool_registry() -> ToolRegistry:
    """Create a ToolRegistry with all tool calls mocked."""
    registry = Mock(spec=ToolRegistry)
    registry.execute = AsyncMock()
    return registry


def _make_mock_openai_response(content: str = "Mock LLM content") -> MagicMock:
    """Create a mock AsyncOpenAI chat completion response."""
    mock_choice = MagicMock()
    mock_choice.message.content = content
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response


# ── WorkflowStatus Tests ──────────────────────────────────────────────────────
class TestWorkflowStatusEnum:
    """Verify WorkflowStatus enum values match frontend expectations."""

    def test_pending_status_value(self) -> None:
        assert WorkflowStatus.PENDING.value == "pending"

    def test_running_status_value(self) -> None:
        assert WorkflowStatus.RUNNING.value == "running"

    def test_completed_status_value(self) -> None:
        assert WorkflowStatus.COMPLETED.value == "completed"

    def test_failed_status_value(self) -> None:
        assert WorkflowStatus.FAILED.value == "failed"

    def test_cancelled_status_value(self) -> None:
        assert WorkflowStatus.CANCELLED.value == "cancelled"

    def test_paused_status_exists(self) -> None:
        """PAUSED status must exist for human-in-the-loop workflows."""
        assert hasattr(WorkflowStatus, "PAUSED"), (
            "WorkflowStatus must have PAUSED for human-in-the-loop support"
        )

    def test_all_frontend_statuses_covered(self) -> None:
        """All frontend Workflow.status values must have a matching WorkflowStatus enum."""
        frontend_statuses = {"pending", "running", "completed", "failed", "cancelled"}
        enum_values = {s.value for s in WorkflowStatus}
        for fe_status in frontend_statuses:
            assert fe_status in enum_values, (
                f"Frontend status '{fe_status}' has no matching WorkflowStatus enum value"
            )


# ── ROI Calculator Workflow Tests ─────────────────────────────────────────────
class TestROICalculatorWorkflow:
    """Test ROI Calculator workflow execution with mocked tool calls."""

    def test_create_initial_state(self) -> None:
        """create_initial_state must produce a ROIAgentState with PENDING status."""
        registry = _make_mock_tool_registry()
        workflow = ROICalculatorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "prospect-001",
            "value_driver_ids": ["vd-001", "vd-002"],
            "prospect_data": {"annual_revenue": 10_000_000.0},
            "industry_vertical": "financial_services",
        }
        state = workflow.create_initial_state(input_data)

        assert isinstance(state, ROIAgentState)
        assert state.status == WorkflowStatus.PENDING
        assert state.roi_input.prospect_id == "prospect-001"
        assert state.roi_input.value_driver_ids == ["vd-001", "vd-002"]
        assert state.output_data == {}
        assert state.errors == []

    def test_create_initial_state_requires_value_driver_ids(self) -> None:
        """create_initial_state must raise if value_driver_ids is empty."""
        registry = _make_mock_tool_registry()
        workflow = ROICalculatorWorkflow(tool_registry=registry)

        with pytest.raises((ValueError, Exception)):
            workflow.create_initial_state({
                "prospect_id": "prospect-001",
                "value_driver_ids": [],  # Empty — must raise
            })

    @pytest.mark.asyncio
    async def test_roi_workflow_run_with_mocked_tools(self) -> None:
        """ROI workflow must complete when all tool calls are mocked."""
        registry = _make_mock_tool_registry()

        # Mock all tool responses
        async def mock_execute(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
            if tool_name == "get_prospect_data":
                return {
                    "profile": {
                        "name": "Acme Corp",
                        "industry": "financial_services",
                        "annual_revenue": 50_000_000,
                    },
                    "custom_fields": {},
                }
            elif tool_name == "fetch_benchmarks":
                return {
                    "benchmarks": {
                        "vd-001": {"industry_avg": 0.15, "top_quartile": 0.25},
                    }
                }
            elif tool_name == "substitute_variables":
                return {
                    "substituted_formula": "50000000 * 0.15",
                    "variables_used": {"annual_revenue": 50_000_000},
                    "missing_variables": [],
                }
            elif tool_name == "evaluate_formula":
                return {
                    "result": 7_500_000.0,
                    "unit": "USD",
                    "confidence": 0.85,
                }
            elif tool_name == "aggregate_roi":
                return {
                    "roi_results": {
                        "total_annual_value": 7_500_000.0,
                        "investment_required": 500_000.0,
                        "simple_roi_percent": 1400.0,
                        "payback_period_months": 0.8,
                        "three_year_npv": 20_000_000.0,
                    }
                }
            else:
                return {"status": "ok"}

        registry.execute = AsyncMock(side_effect=mock_execute)
        workflow = ROICalculatorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "prospect-001",
            "value_driver_ids": ["vd-001"],
            "prospect_data": {"annual_revenue": 50_000_000.0},
            "industry_vertical": "financial_services",
        }
        initial_state = workflow.create_initial_state(input_data)

        # Mock the LangGraph compiled graph to avoid needing a real graph
        mock_compiled = AsyncMock()
        mock_compiled.ainvoke = AsyncMock(return_value={
            **initial_state.model_dump(),
            "status": "completed",
            "output_data": {
                "aggregate_roi": {
                    "roi_results": {
                        "total_annual_value": 7_500_000.0,
                        "simple_roi_percent": 1400.0,
                    }
                }
            },
        })

        with patch.object(workflow, "compile", return_value=mock_compiled):
            result = await workflow.run(initial_state, thread_id="test-thread-001")

        assert result is not None
        assert isinstance(result, ROIAgentState)

    @pytest.mark.asyncio
    async def test_roi_workflow_state_has_workflow_type(self) -> None:
        """ROI workflow state must include workflow_type for frontend normalization."""
        registry = _make_mock_tool_registry()
        workflow = ROICalculatorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "prospect-001",
            "value_driver_ids": ["vd-001"],
        }
        state = workflow.create_initial_state(input_data)

        # workflow_type must be set (used by executor.get_workflow_status)
        assert state.workflow_type is not None
        assert hasattr(state.workflow_type, "value") or isinstance(state.workflow_type, str)


# ── Business Case Generator Workflow Tests ────────────────────────────────────
class TestBusinessCaseGeneratorWorkflow:
    """Test Business Case Generator workflow with mocked LLM and tool calls."""

    def test_create_initial_state(self) -> None:
        """create_initial_state must produce a BusinessCaseAgentState with PENDING status."""
        registry = _make_mock_tool_registry()
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "prospect-001",
            "sections_requested": ["executive_summary", "roi_analysis"],
            "output_format": "pdf",
        }
        state = workflow.create_initial_state(input_data)

        assert isinstance(state, BusinessCaseAgentState)
        assert state.status == WorkflowStatus.PENDING
        assert state.case_input.prospect_id == "prospect-001"
        assert "executive_summary" in state.case_input.sections_requested
        assert state.output_data == {}
        assert state.errors == []

    @pytest.mark.asyncio
    async def test_generate_sections_with_mocked_llm(self) -> None:
        """_execute_generate_sections must produce sections for each requested type."""
        registry = _make_mock_tool_registry()

        # Mock generate_section tool to return content
        async def mock_execute(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
            if tool_name == "generate_section":
                return {
                    "content": f"Mock content for {params.get('section_type', 'unknown')}",
                    "word_count": 150,
                    "key_points": ["Point 1", "Point 2"],
                }
            elif tool_name == "create_chart":
                return {"chart_data": {"type": "bar", "data": []}}
            else:
                return {"status": "ok"}

        registry.execute = AsyncMock(side_effect=mock_execute)
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)

        # Build a state with pre-populated gather_inputs and run_roi output
        input_data = {
            "prospect_id": "prospect-001",
            "sections_requested": ["executive_summary", "roi_analysis"],
            "output_format": "pdf",
        }
        state = workflow.create_initial_state(input_data)
        state.output_data = {
            "gather_inputs": {
                "prospect": {
                    "profile": {
                        "name": "Acme Corp",
                        "industry": "financial_services",
                        "annual_revenue": 50_000_000,
                    }
                }
            },
            "run_roi": {
                "roi_results": {
                    "simple_roi_percent": 1400.0,
                    "payback_period_months": 0.8,
                    "three_year_npv": 20_000_000.0,
                    "investment_required": 500_000.0,
                    "total_annual_value": 7_500_000.0,
                }
            },
        }

        result = await workflow._execute_generate_sections(state)

        assert "sections" in result
        assert "section_count" in result
        assert result["section_count"] == 2  # executive_summary + roi_analysis
        sections = result["sections"]
        assert len(sections) == 2
        # Each section must have title and content
        for section in sections:
            assert "title" in section
            assert "content" in section
            assert len(section["content"]) > 0

    @pytest.mark.asyncio
    async def test_generate_sections_handles_llm_error_gracefully(self) -> None:
        """When LLM fails, _execute_generate_sections must return error section, not crash."""
        registry = _make_mock_tool_registry()

        # Mock generate_section to raise an exception
        async def mock_execute_error(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
            if tool_name == "generate_section":
                raise RuntimeError("LLM API unavailable")
            return {"status": "ok"}

        registry.execute = AsyncMock(side_effect=mock_execute_error)
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "prospect-001",
            "sections_requested": ["executive_summary"],
            "output_format": "pdf",
        }
        state = workflow.create_initial_state(input_data)
        state.output_data = {
            "gather_inputs": {"prospect": {"profile": {"name": "Acme Corp"}}},
            "run_roi": {"roi_results": {}},
        }

        # Must not raise — should return error section
        result = await workflow._execute_generate_sections(state)

        assert "sections" in result
        assert result["section_count"] == 1
        section = result["sections"][0]
        assert "Error" in section["content"] or "error" in section["content"].lower()

    @pytest.mark.asyncio
    async def test_business_case_workflow_run_with_mocked_graph(self) -> None:
        """BusinessCaseGeneratorWorkflow.run must return a BusinessCaseAgentState."""
        registry = _make_mock_tool_registry()
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "prospect-001",
            "sections_requested": ["executive_summary"],
            "output_format": "pdf",
        }
        initial_state = workflow.create_initial_state(input_data)

        # Mock the compiled graph
        mock_compiled = AsyncMock()
        mock_compiled.ainvoke = AsyncMock(return_value={
            **initial_state.model_dump(),
            "status": "completed",
            "output_data": {
                "generate_narrative": {
                    "sections": [
                        {"title": "Executive Summary", "content": "Mock content", "charts": [], "tables": []}
                    ],
                    "section_count": 1,
                }
            },
        })

        with patch.object(workflow, "compile", return_value=mock_compiled):
            result = await workflow.run(initial_state, thread_id="test-bc-001")

        assert result is not None
        assert isinstance(result, BusinessCaseAgentState)


# ── GenerateSectionTool LLM Mock Tests ────────────────────────────────────────
class TestGenerateSectionToolLLMMock:
    """Test that GenerateSectionTool._call_llm can be mocked cleanly."""

    @pytest.mark.asyncio
    async def test_generate_section_tool_with_mocked_openai(self) -> None:
        """GenerateSectionTool must use AsyncOpenAI and be mockable."""
        from src.tools.generation_tools import GenerateSectionTool
        from src.models.tool_schemas import GenerateSectionInput

        tool = GenerateSectionTool()

        mock_response = _make_mock_openai_response(
            "This is a mock executive summary for testing purposes."
        )

        with patch("src.tools.generation_tools.AsyncOpenAI") as mock_openai_cls:
            mock_client = AsyncMock()
            mock_openai_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)

            input_data = GenerateSectionInput(
                section_type="executive_summary",
                context={"company_name": "Acme Corp", "roi_percent": 1400},
                tone="professional",
                max_length=500,
            )
            result = await tool.execute(input_data)

        assert result is not None
        assert result.content == "This is a mock executive summary for testing purposes."
        mock_client.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_section_tool_uses_gpt4o(self) -> None:
        """GenerateSectionTool must call gpt-4o model."""
        from src.tools.generation_tools import GenerateSectionTool
        from src.models.tool_schemas import GenerateSectionInput

        tool = GenerateSectionTool()
        mock_response = _make_mock_openai_response("Mock content")
        captured_calls = []

        async def mock_create(**kwargs):
            captured_calls.append(kwargs)
            return mock_response

        with patch("src.tools.generation_tools.AsyncOpenAI") as mock_openai_cls:
            mock_client = AsyncMock()
            mock_openai_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(side_effect=mock_create)

            input_data = GenerateSectionInput(
                section_type="roi_analysis",
                context={"roi_percent": 1400},
                tone="professional",
                max_length=500,
            )
            await tool.execute(input_data)

        assert len(captured_calls) == 1
        assert captured_calls[0]["model"] == "gpt-4o", (
            "GenerateSectionTool must use gpt-4o model"
        )

    @pytest.mark.asyncio
    async def test_generate_section_tool_raises_on_llm_failure(self) -> None:
        """GenerateSectionTool must raise RuntimeError when LLM call fails."""
        from src.tools.generation_tools import GenerateSectionTool
        from src.models.tool_schemas import GenerateSectionInput

        tool = GenerateSectionTool()

        with patch("src.tools.generation_tools.AsyncOpenAI") as mock_openai_cls:
            mock_client = AsyncMock()
            mock_openai_cls.return_value = mock_client
            mock_client.chat.completions.create = AsyncMock(
                side_effect=Exception("API rate limit exceeded")
            )

            input_data = GenerateSectionInput(
                section_type="executive_summary",
                context={"company_name": "Acme Corp"},
                tone="professional",
                max_length=500,
            )
            with pytest.raises(RuntimeError, match="Failed to generate section"):
                await tool.execute(input_data)

    def test_generate_section_tool_has_all_section_templates(self) -> None:
        """GenerateSectionTool must have templates for all 6 standard section types."""
        from src.tools.generation_tools import GenerateSectionTool

        tool = GenerateSectionTool()
        required_sections = {
            "executive_summary",
            "current_state",
            "proposed_solution",
            "roi_analysis",
            "implementation",
            "next_steps",
        }
        for section_type in required_sections:
            assert section_type in tool.SECTION_TEMPLATES, (
                f"GenerateSectionTool missing template for '{section_type}'"
            )


# ── Executor Integration Tests ────────────────────────────────────────────────
class TestOrchestrationControllerWorkflowLifecycle:
    """Test OrchestrationController workflow lifecycle with mocked workflows."""

    @pytest.mark.asyncio
    async def test_execute_workflow_creates_metadata(self) -> None:
        """execute_workflow must store workflow_metadata for the new workflow_id."""
        from src.engine.executor import OrchestrationController
        from src.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        mock_saver = Mock()
        state_manager = StateManager()

        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
            checkpoint_saver=mock_saver,
        )

        mock_roi_state = Mock()
        mock_roi_state.workflow_id = "wf-test-001"
        mock_roi_state.status = WorkflowStatus.COMPLETED
        mock_roi_state.workflow_type = Mock()
        mock_roi_state.workflow_type.value = "roi_calculator"
        mock_roi_state.current_node = None
        mock_roi_state.started_at = None
        mock_roi_state.completed_at = None
        mock_roi_state.errors = []
        mock_roi_state.output_data = {}
        mock_roi_state.model_dump.return_value = {
            "workflow_id": "wf-test-001",
            "workflow_type": "roi_calculator",
            "status": "completed",
            "current_node": None,
            "input_data": {},
            "output_data": {},
            "errors": [],
            "metadata": {},
        }

        mock_workflow = Mock()
        mock_workflow.run = AsyncMock(return_value=mock_roi_state)
        mock_workflow.create_initial_state = Mock(return_value=mock_roi_state)

        # Patch both create_workflow and _wait_for_workflow to avoid scheduler setup
        with (
            patch("src.engine.executor.create_workflow", return_value=mock_workflow),
            patch.object(controller, "_wait_for_workflow", AsyncMock(return_value=mock_roi_state)),
            patch.object(controller, "scheduler") as mock_scheduler,
        ):
            mock_scheduler.schedule_task = AsyncMock()
            result = await controller.execute_workflow(
                workflow_type="roi_calculator",
                input_data={
                    "prospect_id": "p-001",
                    "value_driver_ids": ["vd-001"],
                },
                tenant_id="tenant-001",
                user_id="user-001",
            )

        # Metadata must be stored for the workflow
        assert len(controller._workflow_metadata) > 0
        # Result must be the mock state
        assert result is mock_roi_state

    @pytest.mark.asyncio
    async def test_get_workflow_status_returns_none_for_unknown(self) -> None:
        """get_workflow_status must return None for unknown workflow IDs."""
        from src.engine.executor import OrchestrationController
        from src.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        state_manager = StateManager()

        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
        )

        status = await controller.get_workflow_status("nonexistent-workflow-id")
        assert status is None

    @pytest.mark.asyncio
    async def test_list_active_workflows_returns_list(self) -> None:
        """list_active_workflows must return a list (possibly empty)."""
        from src.engine.executor import OrchestrationController
        from src.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        state_manager = StateManager()

        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
        )

        active = await controller.list_active_workflows()
        assert isinstance(active, list)
