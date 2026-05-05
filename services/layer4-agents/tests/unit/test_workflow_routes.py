"""Unit tests for workflow API routes.

Validates request/response models and route behavior to prevent
frontend-backend contract drift.
"""

import pytest
from fastapi import HTTPException

from src.api.routes.workflows import (
    ESTIMATED_DURATION_SECONDS,
    TERMINAL_STATUSES,
    PAUSABLE_STATUSES,
    WorkflowCreateRequest,
    WorkflowStatusResponse,
    WorkflowInputs,
    extract_status_value,
)


class TestWorkflowCreateRequest:
    """Test workflow creation request model."""

    def test_valid_request_with_all_fields(self):
        req = WorkflowCreateRequest(
            workflow_type="roi_calculator",
            tenant_id="tenant-001",
            user_id="user-001",
            inputs=WorkflowInputs(prospect_id="p-001"),
            priority="HIGH",
        )
        assert req.workflow_type == "roi_calculator"
        assert req.tenant_id == "tenant-001"
        assert req.user_id == "user-001"
        assert req.inputs.prospect_id == "p-001"
        assert req.priority == "HIGH"

    def test_valid_request_without_tenant_id(self):
        """tenant_id should be optional (falls back to auth context)."""
        req = WorkflowCreateRequest(
            workflow_type="business_case_generation",
            user_id="user-001",
        )
        assert req.tenant_id is None
        assert req.workflow_type == "business_case_generation"

    def test_valid_request_without_user_id(self):
        """user_id should be optional (falls back to auth context)."""
        req = WorkflowCreateRequest(
            workflow_type="whitespace_analysis",
            tenant_id="tenant-001",
        )
        assert req.user_id is None

    def test_valid_request_minimal(self):
        """Only workflow_type is strictly required."""
        req = WorkflowCreateRequest(workflow_type="orchestrator")
        assert req.tenant_id is None
        assert req.user_id is None
        assert req.priority == "NORMAL"

    def test_invalid_workflow_type_rejected(self):
        with pytest.raises(ValueError):
            WorkflowCreateRequest(workflow_type="invalid_type")

    def test_all_valid_workflow_types_accepted(self):
        valid_types = [
            "roi_calculator",
            "whitespace_analysis",
            "business_case",
            "business_case_generation",
            "orchestrator",
        ]
        for wt in valid_types:
            req = WorkflowCreateRequest(workflow_type=wt)
            assert req.workflow_type == wt


class TestWorkflowStatusResponse:
    """Test workflow status response model."""

    def test_valid_status_response(self):
        resp = WorkflowStatusResponse(
            workflow_instance_id="wf-001",
            workflow_type="roi_calculator",
            status="running",
            progress_percentage=45.0,
        )
        assert resp.workflow_instance_id == "wf-001"
        assert resp.status == "running"
        assert resp.progress_percentage == 45.0

    def test_status_response_with_progress(self):
        from src.api.schemas.workflow_progress import WorkflowProgressSchema

        progress = WorkflowProgressSchema(
            step_id="node-1",
            status="running",
            percent=50.0,
            message="Processing",
            updated_at="2024-01-15T10:00:00Z",
            actionable_next_state={
                "can_retry": False,
                "can_resume": False,
                "can_cancel": True,
                "requires_user_action": False,
                "next_action": "wait",
            },
        )
        resp = WorkflowStatusResponse(
            workflow_instance_id="wf-001",
            workflow_type="business_case",
            status="running",
            progress=progress,
        )
        assert resp.progress is not None
        assert resp.progress.percent == 50.0


class TestWorkflowConstants:
    """Test workflow constants and helpers."""

    def test_estimated_duration_for_all_types(self):
        for wt in ["roi_calculator", "whitespace_analysis", "business_case", "business_case_generation", "orchestrator"]:
            assert wt in ESTIMATED_DURATION_SECONDS
            assert ESTIMATED_DURATION_SECONDS[wt] > 0

    def test_terminal_statuses(self):
        assert "completed" in TERMINAL_STATUSES
        assert "failed" in TERMINAL_STATUSES
        assert "cancelled" in TERMINAL_STATUSES
        assert "running" not in TERMINAL_STATUSES

    def test_pausable_statuses(self):
        assert "pending" in PAUSABLE_STATUSES
        assert "running" in PAUSABLE_STATUSES
        assert "completed" not in PAUSABLE_STATUSES

    def test_extract_status_value_with_enum(self):
        class FakeEnum:
            value = "running"
        assert extract_status_value(FakeEnum()) == "running"

    def test_extract_status_value_with_string(self):
        assert extract_status_value("paused") == "paused"
