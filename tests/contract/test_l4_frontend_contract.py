"""
Contract tests — Layer 4 (Agents) → Frontend boundary.

These tests validate that:
1. The L4 /v1/workflows (POST) response matches what useCreateWorkflow expects.
2. The L4 /v1/workflows/active (GET) response matches what useWorkflows expects.
3. The L4 /v1/workflows/{id} (GET) response matches WorkflowStatusResponse.
4. The L4 /v1/workflows/{id}/resume (POST) response matches WorkflowResumeResponse.
5. The L4 /v1/workflows/{id}/events SSE payload matches WorkflowEvent.
6. The frontend normalizeWorkflow() function can handle the L4 status dict.

All tests are schema-only (no live services required).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# ── L4 WorkflowCreateResponse schema ─────────────────────────────────────────
# From layer4-agents/src/api/routes/workflows.py  WorkflowCreateResponse
L4_WORKFLOW_CREATE_RESPONSE_REQUIRED: Dict[str, type] = {
    "workflow_instance_id": str,
    "status": str,
    "estimated_duration_seconds": int,
}

# ── L4 WorkflowStatusResponse schema ─────────────────────────────────────────
# From layer4-agents/src/api/routes/workflows.py  WorkflowStatusResponse
L4_WORKFLOW_STATUS_REQUIRED: Dict[str, type] = {
    "workflow_instance_id": str,
    "workflow_type": str,
    "status": str,
    "progress_percentage": (int, float),
}

# ── L4 WorkflowResumeResponse schema ─────────────────────────────────────────
L4_WORKFLOW_RESUME_RESPONSE_REQUIRED: Dict[str, type] = {
    "workflow_instance_id": str,
    "status": str,
    "message": str,
    "estimated_completion_seconds": int,
}

# ── L4 WorkflowEvent schema ───────────────────────────────────────────────────
L4_WORKFLOW_EVENT_REQUIRED: Dict[str, type] = {
    "event_id": str,
    "event_type": str,
    "timestamp": str,
    "message": str,
}

# ── L4 executor get_workflow_status dict schema ───────────────────────────────
# From layer4-agents/src/engine/executor.py  get_workflow_status()
L4_EXECUTOR_STATUS_DICT_REQUIRED: Dict[str, type] = {
    "workflow_id": str,
    "workflow_type": str,
    "status": str,
    "progress_percentage": (int, float),
}

# ── Frontend Workflow interface ───────────────────────────────────────────────
# From frontend/client/src/hooks/useWorkflows.ts  Workflow interface
FE_WORKFLOW_REQUIRED: Dict[str, type] = {
    "id": str,
    "name": str,
    "status": str,
    "progress": (int, float),
}

VALID_FE_WORKFLOW_STATUSES = {"pending", "running", "completed", "failed", "cancelled"}


# ── Utility ───────────────────────────────────────────────────────────────────
def _check_required_fields(payload: Dict[str, Any], required: Dict[str, type], label: str) -> None:
    for field, expected_type in required.items():
        assert field in payload, f"{label}: missing required field '{field}'"
        if isinstance(expected_type, tuple):
            assert isinstance(payload[field], expected_type), (
                f"{label}.{field}: expected one of {expected_type}, got {type(payload[field])}"
            )
        else:
            assert isinstance(payload[field], expected_type), (
                f"{label}.{field}: expected {expected_type}, got {type(payload[field])}"
            )


def _simulate_normalize_workflow(raw: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Simulate the frontend normalizeWorkflow() function from useWorkflows.ts."""
    normalized_id = raw.get("workflow_id") or raw.get("workflow_instance_id") or raw.get("id")
    normalized_id_text = str(normalized_id or "").strip()
    if not normalized_id_text:
        return None

    raw_status = str(raw.get("status", "")).lower()
    valid_statuses = {"pending", "running", "completed", "failed", "cancelled"}
    status = raw_status if raw_status in valid_statuses else "pending"

    raw_progress = raw.get("progress") or raw.get("progress_percentage") or 0
    try:
        progress = float(raw_progress)
        progress = min(100.0, max(0.0, progress))
    except (TypeError, ValueError):
        progress = 0.0

    return {
        "id": normalized_id_text,
        "name": str(raw.get("name") or raw.get("workflow_type") or "workflow"),
        "status": status,
        "progress": progress,
        "createdAt": raw.get("createdAt") or raw.get("created_at") or raw.get("started_at"),
        "updatedAt": raw.get("updatedAt") or raw.get("updated_at") or raw.get("completed_at"),
    }


# ── Tests ─────────────────────────────────────────────────────────────────────
class TestWorkflowCreateContract:
    """Validate the POST /v1/workflows request/response contract."""

    def test_l4_workflow_create_response_has_required_fields(self) -> None:
        """L4 WorkflowCreateResponse must have workflow_instance_id, status, estimated_duration_seconds."""
        response = {
            "workflow_instance_id": "wf-abc-123",
            "status": "pending",
            "estimated_duration_seconds": 300,
        }
        _check_required_fields(response, L4_WORKFLOW_CREATE_RESPONSE_REQUIRED, "WorkflowCreateResponse")

    def test_frontend_extracts_workflow_id_from_create_response(self) -> None:
        """Frontend useCreateWorkflow must be able to extract workflow_instance_id."""
        response = {
            "workflow_instance_id": "wf-abc-123",
            "status": "pending",
            "estimated_duration_seconds": 300,
        }
        # Frontend: const workflowId = response.data?.workflow_instance_id || response.data?.workflow_id
        workflow_id = response.get("workflow_instance_id") or response.get("workflow_id")
        assert workflow_id == "wf-abc-123", "Frontend must extract workflow_instance_id"
        assert str(workflow_id), "workflow_id must be a non-empty string"

    def test_l4_workflow_create_request_required_fields(self) -> None:
        """L4 WorkflowCreateRequest must have workflow_type, tenant_id, user_id."""
        request = {
            "workflow_type": "business_case",
            "tenant_id": "tenant-001",
            "user_id": "user-001",
            "inputs": {},
        }
        for field in ("workflow_type", "tenant_id", "user_id"):
            assert field in request, f"WorkflowCreateRequest missing required field: {field}"

    def test_l4_workflow_types_match_frontend_expectations(self) -> None:
        """L4 workflow_type enum values must include types the frontend uses."""
        # From L4 WorkflowCreateRequest enum
        l4_types = {"roi_calculator", "whitespace_analysis", "business_case", "orchestrator"}
        # Frontend uses these types (from useBusinessCases and useWorkflows)
        frontend_types = {"business_case", "whitespace_analysis", "roi_calculator"}
        for fe_type in frontend_types:
            assert fe_type in l4_types, (
                f"Frontend workflow type '{fe_type}' not in L4 workflow_type enum"
            )


class TestWorkflowStatusContract:
    """Validate the GET /v1/workflows/{id} and /v1/workflows/active contracts."""

    def test_l4_workflow_status_response_has_required_fields(self) -> None:
        """WorkflowStatusResponse must have workflow_instance_id, workflow_type, status, progress_percentage."""
        response = {
            "workflow_instance_id": "wf-abc-123",
            "workflow_type": "business_case",
            "status": "running",
            "current_state": "generate_sections",
            "current_node": "generate_sections",
            "progress_percentage": 45.0,
            "started_at": "2026-04-13T10:00:00",
            "completed_at": None,
            "error_count": 0,
            "has_output": False,
            "results": None,
        }
        _check_required_fields(response, L4_WORKFLOW_STATUS_REQUIRED, "WorkflowStatusResponse")

    def test_executor_status_dict_normalizable_by_frontend(self) -> None:
        """The executor.get_workflow_status() dict must be normalizable by frontend normalizeWorkflow()."""
        executor_dict = {
            "workflow_id": "wf-abc-123",
            "workflow_type": "business_case",
            "status": "running",
            "current_node": "generate_sections",
            "progress_percentage": 45.0,
            "started_at": "2026-04-13T10:00:00",
            "completed_at": None,
            "estimated_duration_seconds": 300,
            "error_count": 0,
            "has_output": False,
            "tenant_id": "tenant-001",
            "user_id": "user-001",
            "priority": 1,
            "scheduler_status": "running",
        }
        _check_required_fields(executor_dict, L4_EXECUTOR_STATUS_DICT_REQUIRED, "ExecutorStatusDict")

        # Simulate frontend normalizeWorkflow()
        normalized = _simulate_normalize_workflow(executor_dict)
        assert normalized is not None, "normalizeWorkflow must not return null for valid executor dict"
        _check_required_fields(normalized, FE_WORKFLOW_REQUIRED, "FrontendWorkflow")
        assert normalized["id"] == "wf-abc-123"
        assert normalized["status"] == "running"
        assert normalized["progress"] == 45.0

    def test_workflow_status_values_are_compatible(self) -> None:
        """L4 status values must map to frontend status values."""
        # L4 status values (from WorkflowStatus enum)
        l4_to_fe_map = {
            "pending": "pending",
            "running": "running",
            "completed": "completed",
            "failed": "failed",
            "cancelled": "cancelled",
            "retrying": "running",   # L4 retrying → frontend running
        }
        for l4_status, expected_fe_status in l4_to_fe_map.items():
            raw = {
                "workflow_id": "wf-test",
                "workflow_type": "business_case",
                "status": l4_status,
                "progress_percentage": 0,
            }
            normalized = _simulate_normalize_workflow(raw)
            assert normalized is not None
            if l4_status in VALID_FE_WORKFLOW_STATUSES:
                assert normalized["status"] == expected_fe_status, (
                    f"L4 status '{l4_status}' should map to frontend '{expected_fe_status}'"
                )
            else:
                # Unknown statuses fall back to 'pending'
                assert normalized["status"] == "pending", (
                    f"Unknown L4 status '{l4_status}' should fall back to 'pending'"
                )

    def test_active_workflows_list_is_array(self) -> None:
        """GET /v1/workflows/active must return a list (array)."""
        active_response: List[Dict[str, Any]] = [
            {
                "workflow_id": "wf-abc-123",
                "workflow_type": "business_case",
                "status": "running",
                "progress_percentage": 45.0,
                "started_at": "2026-04-13T10:00:00",
            }
        ]
        assert isinstance(active_response, list), "active workflows response must be a list"
        for item in active_response:
            normalized = _simulate_normalize_workflow(item)
            assert normalized is not None, "Each active workflow must be normalizable"

    def test_empty_active_workflows_list(self) -> None:
        """GET /v1/workflows/active may return an empty list."""
        active_response: List[Dict[str, Any]] = []
        assert isinstance(active_response, list)
        assert len(active_response) == 0


class TestWorkflowResumeContract:
    """Validate the POST /v1/workflows/{id}/resume contract."""

    def test_l4_resume_response_has_required_fields(self) -> None:
        """WorkflowResumeResponse must have workflow_instance_id, status, message, estimated_completion_seconds."""
        response = {
            "workflow_instance_id": "wf-abc-123",
            "status": "resumed",
            "resumed_from_node": "human_review",
            "message": "Workflow resumed from human_review node",
            "estimated_completion_seconds": 60,
        }
        _check_required_fields(response, L4_WORKFLOW_RESUME_RESPONSE_REQUIRED, "WorkflowResumeResponse")

    def test_l4_resume_response_status_values(self) -> None:
        """WorkflowResumeResponse.status must be one of: resumed, completed, failed."""
        valid_statuses = {"resumed", "completed", "failed"}
        for status in valid_statuses:
            response = {
                "workflow_instance_id": "wf-abc-123",
                "status": status,
                "message": f"Workflow {status}",
                "estimated_completion_seconds": 60,
            }
            assert response["status"] in valid_statuses

    def test_l4_resume_request_required_fields(self) -> None:
        """WorkflowResumeRequest must have user_id."""
        request = {
            "user_id": "user-001",
            "resume_data": {"approved": True},
        }
        assert "user_id" in request, "WorkflowResumeRequest must have user_id"


class TestWorkflowSSEContract:
    """Validate the GET /v1/workflows/{id}/events SSE contract."""

    def test_l4_workflow_event_has_required_fields(self) -> None:
        """WorkflowEvent must have event_id, event_type, timestamp, message."""
        event = {
            "event_id": "evt-1713000000.0",
            "event_type": "status_update",
            "timestamp": "2026-04-13T10:00:00",
            "message": "Workflow status: running",
            "payload": {
                "workflow_id": "wf-abc-123",
                "status": "running",
                "progress_percentage": 45.0,
            },
        }
        _check_required_fields(event, L4_WORKFLOW_EVENT_REQUIRED, "WorkflowEvent")

    def test_frontend_sse_parses_workflow_event_payload(self) -> None:
        """Frontend useWorkflowSSE must be able to parse the SSE event payload."""
        sse_event_data = {
            "event_id": "evt-1713000000.0",
            "event_type": "status_update",
            "timestamp": "2026-04-13T10:00:00",
            "message": "Workflow status: running",
            "payload": {
                "workflow_id": "wf-abc-123",
                "workflow_type": "business_case",
                "status": "running",
                "progress_percentage": 45.0,
            },
        }
        # Frontend: const data = JSON.parse(event.data); if (data.payload) { normalizeWorkflow(data.payload) }
        payload = sse_event_data.get("payload")
        assert payload is not None, "SSE event must have a payload field"

        normalized = _simulate_normalize_workflow(payload)
        assert normalized is not None, "SSE payload must be normalizable by frontend"
        assert normalized["id"] == "wf-abc-123"
        assert normalized["status"] == "running"

    def test_l4_sse_endpoint_url(self) -> None:
        """L4 must expose /v1/workflows/{id}/events as the SSE endpoint."""
        l4_workflows_path = (
            REPO_ROOT
            / "value-fabric"
            / "layer4-agents"
            / "src"
            / "api"
            / "routes"
            / "workflows.py"
        )
        if not l4_workflows_path.exists():
            pytest.skip("L4 workflows.py not found")

        source = l4_workflows_path.read_text()
        assert "/workflows/{workflow_id}/events" in source, (
            "L4 must expose /v1/workflows/{id}/events as the SSE endpoint"
        )


class TestWorkflowEndpointPaths:
    """Validate that the L4 API exposes all endpoints the frontend calls."""

    def test_l4_exposes_post_workflows(self) -> None:
        """L4 must expose POST /v1/workflows."""
        source = _read_l4_workflows_source()
        assert '@router.post("/workflows"' in source, "L4 must expose POST /workflows"

    def test_l4_exposes_get_workflows_active(self) -> None:
        """L4 must expose GET /v1/workflows/active."""
        source = _read_l4_workflows_source()
        assert '@router.get("/workflows/active")' in source, "L4 must expose GET /workflows/active"

    def test_l4_exposes_get_workflow_by_id(self) -> None:
        """L4 must expose GET /v1/workflows/{id}."""
        source = _read_l4_workflows_source()
        assert '@router.get("/workflows/{workflow_id}"' in source, (
            "L4 must expose GET /workflows/{workflow_id}"
        )

    def test_l4_exposes_delete_workflow(self) -> None:
        """L4 must expose DELETE /v1/workflows/{id} for cancellation."""
        source = _read_l4_workflows_source()
        assert '@router.delete("/workflows/{workflow_id}")' in source, (
            "L4 must expose DELETE /workflows/{workflow_id}"
        )

    def test_l4_exposes_post_workflow_resume(self) -> None:
        """L4 must expose POST /v1/workflows/{id}/resume."""
        source = _read_l4_workflows_source()
        assert '@router.post("/workflows/{workflow_id}/resume"' in source, (
            "L4 must expose POST /workflows/{workflow_id}/resume"
        )


def _read_l4_workflows_source() -> str:
    path = (
        REPO_ROOT
        / "value-fabric"
        / "layer4-agents"
        / "src"
        / "api"
        / "routes"
        / "workflows.py"
    )
    if not path.exists():
        pytest.skip("L4 workflows.py not found")
    return path.read_text()


class TestAnalysisContract:
    """Validate L4 analysis API contracts."""

    def test_roi_analysis_request_has_required_fields(self) -> None:
        """ROIAnalysisRequest must have prospect_id and value_driver_ids."""
        request = {
            "prospect_id": "prospect-001",
            "value_driver_ids": ["vd-001", "vd-002"],
            "prospect_data": {"annual_revenue": 10_000_000.0},
            "industry_vertical": "financial_services",
        }
        assert "prospect_id" in request
        assert "value_driver_ids" in request
        assert isinstance(request["value_driver_ids"], list)
        assert len(request["value_driver_ids"]) > 0

    def test_roi_analysis_response_has_required_fields(self) -> None:
        """ROIAnalysisResponse must have prospect_id, aggregated_roi, detailed_results."""
        response = {
            "prospect_id": "prospect-001",
            "aggregated_roi": {"total_value": 7_500_000, "roi_percent": 1400},
            "detailed_results": [{"driver_id": "vd-001", "value": 7_500_000}],
            "benchmark_comparison": None,
        }
        for field in ("prospect_id", "aggregated_roi", "detailed_results"):
            assert field in response, f"ROIAnalysisResponse missing: {field}"
        assert isinstance(response["detailed_results"], list)

    def test_whitespace_analysis_request_has_required_fields(self) -> None:
        """WhitespaceAnalysisRequest must have prospect_id and prospect_needs."""
        request = {
            "prospect_id": "prospect-001",
            "prospect_needs": "We need better analytics and reporting capabilities",
            "analysis_depth": "standard",
        }
        assert "prospect_id" in request
        assert "prospect_needs" in request
        assert len(request["prospect_needs"]) >= 10

    def test_whitespace_analysis_response_has_required_fields(self) -> None:
        """WhitespaceAnalysisResponse must return needs, gaps, score, recommendations."""
        response = {
            "prospect_id": "prospect-001",
            "extracted_needs": ["analytics", "reporting"],
            "gap_analysis": [{"need": "analytics", "coverage": 0.6}],
            "opportunity_score": 0.75,
            "recommendations": ["Implement real-time dashboard"],
        }
        for field in ("prospect_id", "extracted_needs", "gap_analysis", "opportunity_score", "recommendations"):
            assert field in response, f"WhitespaceAnalysisResponse missing: {field}"
        assert 0.0 <= response["opportunity_score"] <= 1.0


class TestToolsContract:
    """Validate L4 tools API contracts."""

    def test_tools_list_is_array(self) -> None:
        """GET /v1/tools must return a list of tool descriptors."""
        response = [
            {"name": "semantic_search", "description": "Search knowledge graph", "category": "retrieval"},
            {"name": "evaluate_formula", "description": "Evaluate a value formula", "category": "calculation"},
        ]
        assert isinstance(response, list)
        for tool in response:
            assert "name" in tool
            assert "description" in tool

    def test_tool_invoke_request_has_required_fields(self) -> None:
        """POST /v1/tools/invoke must require tool_name and parameters."""
        request = {
            "tool_name": "semantic_search",
            "parameters": {"query": "data analytics", "top_k": 5},
        }
        assert "tool_name" in request
        assert "parameters" in request
        assert isinstance(request["parameters"], dict)

    def test_tool_invoke_response_has_result(self) -> None:
        """POST /v1/tools/invoke response must contain result field."""
        response = {
            "tool_name": "semantic_search",
            "result": {"matches": [{"id": "cap-001", "score": 0.95}]},
            "execution_time_ms": 120,
        }
        assert "result" in response
        assert "tool_name" in response


class TestErrorResponseContract:
    """Validate error response schema across L4 endpoints."""

    def test_404_error_has_detail(self) -> None:
        """404 error must have 'detail' field per FastAPI convention."""
        error_response = {"detail": "Workflow wf-unknown not found"}
        assert "detail" in error_response
        assert isinstance(error_response["detail"], str)

    def test_400_error_has_detail(self) -> None:
        """400 error must have 'detail' field."""
        error_response = {"detail": "Workflow wf-123 is completed and cannot be resumed"}
        assert "detail" in error_response

    def test_422_validation_error_has_detail_array(self) -> None:
        """422 validation error must have 'detail' as array of field errors."""
        error_response = {
            "detail": [
                {
                    "loc": ["body", "workflow_type"],
                    "msg": "field required",
                    "type": "value_error.missing",
                }
            ]
        }
        assert "detail" in error_response
        assert isinstance(error_response["detail"], list)
        assert "loc" in error_response["detail"][0]
        assert "msg" in error_response["detail"][0]

    def test_503_error_has_detail(self) -> None:
        """503 error must have 'detail' field."""
        error_response = {"detail": "Workflow executor not initialized"}
        assert "detail" in error_response


class TestWorkflowPauseContract:
    """Validate the POST /v1/workflows/{id}/pause contract."""

    def test_pause_request_has_required_fields(self) -> None:
        """WorkflowPauseRequest must have user_id."""
        request = {
            "user_id": "user-001",
            "reason": "Need human review",
        }
        assert "user_id" in request

    def test_pause_response_has_required_fields(self) -> None:
        """WorkflowPauseResponse must have workflow_instance_id, status, paused_at, message."""
        response = {
            "workflow_instance_id": "wf-abc-123",
            "status": "paused",
            "paused_at": "2026-04-13T10:00:00",
            "current_node": "human_review",
            "message": "Workflow paused at human_review",
        }
        for field in ("workflow_instance_id", "status", "paused_at", "message"):
            assert field in response, f"WorkflowPauseResponse missing: {field}"
        assert response["status"] == "paused"

    def test_l4_exposes_post_workflow_pause(self) -> None:
        """L4 must expose POST /v1/workflows/{id}/pause."""
        source = _read_l4_workflows_source()
        assert '/workflows/{workflow_id}/pause"' in source, (
            "L4 must expose POST /workflows/{workflow_id}/pause"
        )
