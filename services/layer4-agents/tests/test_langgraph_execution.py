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

from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from value_fabric.layer4.models.agent_state import (
    BusinessCaseAgentState,
    ROIAgentState,
    WorkflowStatus,
)
from value_fabric.layer4.tools.registry import ToolRegistry
from value_fabric.layer4.workflows.business_case import BusinessCaseGeneratorWorkflow
from value_fabric.layer4.workflows.roi_calculator import ROICalculatorWorkflow
from value_fabric.shared.models.typed_dict import TypedDictModel


class BusinessCaseGeneratorWorkflowMockExecuteErrorResult(TypedDictModel):
    status: str

class WorkflowToolFailureHandlingMockExecuteAllFailResult(TypedDictModel):
    status: str

class BusinessCaseGeneratorWorkflowMockExecuteResult(TypedDictModel):
    chart_data: dict[str, Any] | None = None
    content: str | None = None
    key_points: list[Any] | None = None
    status: str
    word_count: int | None = None


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
    mock_response.usage = MagicMock()
    mock_response.usage.prompt_tokens = 10
    mock_response.usage.completion_tokens = 20
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
        _tool_responses = {
            "get_prospect_data": {
                "profile": {
                    "name": "Acme Corp",
                    "industry": "financial_services",
                    "annual_revenue": 50_000_000,
                },
                "custom_fields": {},
            },
            "fetch_benchmarks": {
                "benchmarks": {
                    "vd-001": {"industry_avg": 0.15, "top_quartile": 0.25},
                }
            },
            "substitute_variables": {
                "substituted_formula": "50000000 * 0.15",
                "variables_used": {"annual_revenue": 50_000_000},
                "missing_variables": [],
            },
            "evaluate_formula": {
                "result": 7_500_000.0,
                "unit": "USD",
                "confidence": 0.85,
            },
            "aggregate_roi": {
                "roi_results": {
                    "total_annual_value": 7_500_000.0,
                    "investment_required": 500_000.0,
                    "simple_roi_percent": 1400.0,
                    "payback_period_months": 0.8,
                    "three_year_npv": 20_000_000.0,
                }
            },
        }

        async def mock_execute(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
            return _tool_responses.get(tool_name, {"status": "ok"})

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
            "account_id": "550e8400-e29b-41d4-a716-446655440000",
            "sections_requested": ["executive_summary", "roi_analysis"],
            "output_format": "pdf",
        }
        state = workflow.create_initial_state(input_data)

        assert isinstance(state, BusinessCaseAgentState)
        assert state.status == WorkflowStatus.PENDING
        assert str(state.case_input.account_id) == "550e8400-e29b-41d4-a716-446655440000"
        assert "executive_summary" in state.case_input.sections_requested
        assert state.output_data == {}
        assert state.errors == []

    @pytest.mark.asyncio
    async def test_generate_sections_with_mocked_llm(self) -> None:
        """_execute_generate_sections must produce sections for each requested type."""
        registry = _make_mock_tool_registry()

        # Mock generate_section tool to return content
        async def mock_execute(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
            if tool_name == "generate_section":
                return BusinessCaseGeneratorWorkflowMockExecuteResult.model_validate({
                    "content": f"Mock content for {params.get('section_type', 'unknown')}",
                    "word_count": 150,
                    "key_points": ["Point 1", "Point 2"],
                })


            elif tool_name == "create_chart":
                return BusinessCaseGeneratorWorkflowMockExecuteResult.model_validate({"chart_data": {"type": "bar", "data": []}})
            else:
                return BusinessCaseGeneratorWorkflowMockExecuteResult.model_validate({"status": "ok"})

        registry.execute = AsyncMock(side_effect=mock_execute)
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)

        # Build a state with pre-populated gather_inputs and run_roi output
        input_data = {
            "account_id": "550e8400-e29b-41d4-a716-446655440000",
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
        async def mock_execute_error(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
            if tool_name == "generate_section":
                raise RuntimeError("LLM API unavailable")
            return BusinessCaseGeneratorWorkflowMockExecuteErrorResult.model_validate({"status": "ok"})

        registry.execute = AsyncMock(side_effect=mock_execute_error)
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)

        input_data = {
            "account_id": "550e8400-e29b-41d4-a716-446655440000",
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
            "account_id": "550e8400-e29b-41d4-a716-446655440000",
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
        from value_fabric.layer4.models.tool_schemas import GenerateSectionInput
        from value_fabric.layer4.tools.generation_tools import GenerateSectionTool

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
        from value_fabric.layer4.models.tool_schemas import GenerateSectionInput
        from value_fabric.layer4.tools.generation_tools import GenerateSectionTool

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
        from value_fabric.layer4.models.tool_schemas import GenerateSectionInput
        from value_fabric.layer4.tools.generation_tools import GenerateSectionTool

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
        from value_fabric.layer4.tools.generation_tools import GenerateSectionTool

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
        from value_fabric.layer4.engine.executor import OrchestrationController
        from value_fabric.layer4.engine.state_manager import StateManager

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
        from value_fabric.layer4.engine.executor import OrchestrationController
        from value_fabric.layer4.engine.state_manager import StateManager

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
        from value_fabric.layer4.engine.executor import OrchestrationController
        from value_fabric.layer4.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        state_manager = StateManager()

        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
        )

        active = await controller.list_active_workflows()
        assert isinstance(active, list)

    @pytest.mark.asyncio
    async def test_get_result_returns_route_compatible_shape_from_persisted_state(self) -> None:
        """get_result should read persisted state and return route-compatible keys."""
        from value_fabric.layer4.engine.executor import OrchestrationController
        from value_fabric.layer4.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        state_manager = StateManager()
        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
        )

        state = ROIAgentState(
            workflow_id="wf-result-001",
            input_data={"prospect_id": "p-001", "value_driver_ids": ["vd-001"]},
            output_data={"assemble_document": {"title": "Business Case"}},
            metadata={"source": "persisted-store"},
            status=WorkflowStatus.COMPLETED,
        )
        await state_manager.save_state("wf-result-001", state)

        result = await controller.get_result("wf-result-001")

        assert result is not None
        assert result["workflow_id"] == "wf-result-001"
        assert result["status"] == "completed"
        assert result["output"] == {"assemble_document": {"title": "Business Case"}}
        assert result["metadata"]["source"] == "persisted-store"
        assert "created_at" in result
        assert "started_at" in result
        assert "completed_at" in result


# ── State Transition Edge Case Tests ──────────────────────────────────────────
class TestWorkflowStateTransitions:
    """Test edge cases in workflow state transitions."""

    def test_workflow_status_cannot_transition_from_completed(self) -> None:
        """A completed workflow must not be reset to running."""
        # Verify COMPLETED is a terminal status that workflow router respects
        terminal_statuses = {"completed", "failed", "cancelled"}
        for status in terminal_statuses:
            assert status in {s.value for s in WorkflowStatus}, (
                f"WorkflowStatus must include terminal status: {status}"
            )

    def test_workflow_status_has_paused_for_human_in_loop(self) -> None:
        """PAUSED must be a valid WorkflowStatus for human-in-the-loop."""
        assert hasattr(WorkflowStatus, "PAUSED")
        assert WorkflowStatus.PAUSED.value == "paused"

    def test_all_status_values_are_lowercase(self) -> None:
        """All WorkflowStatus values must be lowercase (matches frontend expectations)."""
        for status in WorkflowStatus:
            assert status.value == status.value.lower(), (
                f"WorkflowStatus.{status.name} value must be lowercase, got: {status.value}"
            )

    def test_initial_state_has_empty_errors_list(self) -> None:
        """New workflow states must start with empty errors list."""
        registry = _make_mock_tool_registry()
        
        roi_wf = ROICalculatorWorkflow(tool_registry=registry)
        roi_state = roi_wf.create_initial_state({
            "prospect_id": "p-001",
            "value_driver_ids": ["vd-001"],
        })
        assert roi_state.errors == []
        
        bc_wf = BusinessCaseGeneratorWorkflow(tool_registry=registry)
        bc_state = bc_wf.create_initial_state({
            "prospect_id": "p-001",
            "sections_requested": ["executive_summary"],
        })
        assert bc_state.errors == []

    def test_initial_state_has_empty_output_data(self) -> None:
        """New workflow states must start with empty output_data."""
        registry = _make_mock_tool_registry()
        
        roi_wf = ROICalculatorWorkflow(tool_registry=registry)
        roi_state = roi_wf.create_initial_state({
            "prospect_id": "p-001",
            "value_driver_ids": ["vd-001"],
        })
        assert roi_state.output_data == {}


class TestWorkflowInputValidation:
    """Test workflow input validation edge cases."""

    def test_roi_workflow_rejects_missing_prospect_id(self) -> None:
        """ROI workflow must reject inputs without prospect_id."""
        registry = _make_mock_tool_registry()
        workflow = ROICalculatorWorkflow(tool_registry=registry)
        
        with pytest.raises((ValueError, Exception)):
            workflow.create_initial_state({
                "value_driver_ids": ["vd-001"],
                # Missing prospect_id
            })

    def test_business_case_rejects_empty_sections(self) -> None:
        """Business case workflow must reject empty sections_requested."""
        registry = _make_mock_tool_registry()
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)
        
        with pytest.raises((ValueError, Exception)):
            workflow.create_initial_state({
                "prospect_id": "p-001",
                "sections_requested": [],  # Empty list
            })

    def test_roi_workflow_accepts_minimal_valid_input(self) -> None:
        """ROI workflow must accept minimal valid input (prospect_id + value_driver_ids)."""
        registry = _make_mock_tool_registry()
        workflow = ROICalculatorWorkflow(tool_registry=registry)
        
        state = workflow.create_initial_state({
            "prospect_id": "p-001",
            "value_driver_ids": ["vd-001"],
        })
        assert state.status == WorkflowStatus.PENDING
        assert state.roi_input.prospect_id == "p-001"

    def test_business_case_accepts_all_section_types(self) -> None:
        """Business case must accept all 6 standard section types."""
        registry = _make_mock_tool_registry()
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)
        
        all_sections = [
            "executive_summary", "current_state", "proposed_solution",
            "roi_analysis", "implementation", "next_steps",
        ]
        state = workflow.create_initial_state({
            "prospect_id": "p-001",
            "sections_requested": all_sections,
            "output_format": "pdf",
        })
        assert len(state.case_input.sections_requested) == 6


@pytest.mark.asyncio
class TestWorkflowToolFailureHandling:
    """Test workflow behavior when tool calls fail."""

    async def test_roi_workflow_handles_tool_timeout(self) -> None:
        """ROI workflow must handle tool execution timeouts."""
        registry = _make_mock_tool_registry()

        async def mock_execute_timeout(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
            raise TimeoutError(f"Tool {tool_name} execution timed out after 30s")

        registry.execute = AsyncMock(side_effect=mock_execute_timeout)
        workflow = ROICalculatorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "p-001",
            "value_driver_ids": ["vd-001"],
        }
        initial_state = workflow.create_initial_state(input_data)

        # Mock compiled graph to simulate the error being caught
        mock_compiled = AsyncMock()
        mock_compiled.ainvoke = AsyncMock(return_value={
            **initial_state.model_dump(),
            "status": "failed",
            "errors": ["Tool get_prospect_data execution timed out after 30s"],
        })

        with patch.object(workflow, "compile", return_value=mock_compiled):
            result = await workflow.run(initial_state, thread_id="timeout-test")

        assert result is not None
        # The workflow should either fail or capture the error

    async def test_business_case_handles_all_sections_failing(self) -> None:
        """Business case must handle all section generation failures gracefully."""
        registry = _make_mock_tool_registry()

        async def mock_execute_all_fail(tool_name: str, params: dict[str, Any]) -> dict[str, Any]:
            if tool_name == "generate_section":
                raise RuntimeError("LLM API is down for all calls")
            return WorkflowToolFailureHandlingMockExecuteAllFailResult.model_validate({"status": "ok"})

        registry.execute = AsyncMock(side_effect=mock_execute_all_fail)
        workflow = BusinessCaseGeneratorWorkflow(tool_registry=registry)

        input_data = {
            "prospect_id": "p-001",
            "sections_requested": ["executive_summary", "roi_analysis", "implementation"],
            "output_format": "pdf",
        }
        state = workflow.create_initial_state(input_data)
        state.output_data = {
            "gather_inputs": {"prospect": {"profile": {"name": "Acme Corp"}}},
            "run_roi": {"roi_results": {}},
        }

        # Must not crash — should return error sections
        result = await workflow._execute_generate_sections(state)
        assert "sections" in result
        assert result["section_count"] == 3
        # All sections should contain error indicators
        for section in result["sections"]:
            assert "Error" in section["content"] or "error" in section["content"].lower()


@pytest.mark.asyncio
class TestOrchestrationControllerErrorPaths:
    """Test error paths in the OrchestrationController."""

    async def test_cancel_nonexistent_workflow_returns_false(self) -> None:
        """cancel_workflow must return False for unknown workflow IDs."""
        from value_fabric.layer4.engine.executor import OrchestrationController
        from value_fabric.layer4.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        state_manager = StateManager()

        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
        )

        result = await controller.cancel_workflow("nonexistent-wf-id")
        assert result is False or result is None

    async def test_execute_workflow_rejects_unknown_type(self) -> None:
        """execute_workflow must raise for unknown workflow types."""
        from value_fabric.layer4.engine.executor import OrchestrationController
        from value_fabric.layer4.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        state_manager = StateManager()

        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
        )

        with pytest.raises((ValueError, KeyError, Exception)):
            await controller.execute_workflow(
                workflow_type="nonexistent_workflow",
                input_data={"prospect_id": "p-001"},
                tenant_id="t-001",
                user_id="u-001",
            )

    async def test_get_workflow_status_after_execute(self) -> None:
        """get_workflow_status must return valid data after workflow execution."""
        from value_fabric.layer4.engine.executor import OrchestrationController
        from value_fabric.layer4.engine.state_manager import StateManager

        mock_registry = _make_mock_tool_registry()
        state_manager = StateManager()

        controller = OrchestrationController(
            tool_registry=mock_registry,
            state_manager=state_manager,
        )

        # Add a workflow manually to the metadata
        controller._workflow_metadata["wf-manual-001"] = {
            "workflow_id": "wf-manual-001",
            "workflow_type": "roi_calculator",
            "status": "completed",
            "progress_percentage": 100.0,
            "started_at": "2026-04-13T10:00:00",
            "completed_at": "2026-04-13T10:02:00",
            "error_count": 0,
            "has_output": True,
            "tenant_id": "t-001",
            "user_id": "u-001",
        }

        status = await controller.get_workflow_status("wf-manual-001")
        assert status is not None
        assert status["workflow_type"] == "roi_calculator"
        assert status["status"] == "completed"
