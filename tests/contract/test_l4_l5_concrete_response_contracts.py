"""Contract checks for externally consumed Layer 4/5 response envelopes."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

pytestmark = pytest.mark.contract_static_no_service

CONTRACT_ROOT = Path(__file__).resolve().parents[2] / "contracts" / "openapi"


def _spec(name: str) -> dict[str, Any]:
    return json.loads((CONTRACT_ROOT / name).read_text(encoding="utf-8"))


def _schema(spec: dict[str, Any], name: str) -> dict[str, Any]:
    return spec["components"]["schemas"][name]


def _response_schema(spec: dict[str, Any], path: str, method: str = "get") -> dict[str, Any]:
    response = spec["paths"][path][method]["responses"]["200"]
    return response["content"]["application/json"]["schema"]


def test_layer4_workflow_routes_publish_concrete_response_models() -> None:
    spec = _spec("layer4-agents.json")

    assert _response_schema(spec, "/v1/workflows/types") == {
        "$ref": "#/components/schemas/AvailableWorkflowsResponse"
    }
    assert _response_schema(spec, "/v1/workflows/{workflow_id}", "delete") == {
        "$ref": "#/components/schemas/WorkflowCancelResponse"
    }
    assert _response_schema(spec, "/v1/workflows/{workflow_id}/result") == {
        "$ref": "#/components/schemas/WorkflowResultResponse"
    }

    workflow_result = _schema(spec, "WorkflowResultResponse")
    assert {"workflow_id", "status"}.issubset(set(workflow_result["required"]))
    # Resolve the non-null branch of output.anyOf regardless of position.
    # Pydantic may emit [{"$ref": ...}, {"type": "null"}] or the reverse.
    output_anyof = workflow_result["properties"]["output"]["anyOf"]
    non_null = next(s for s in output_anyof if s.get("type") != "null")
    if "$ref" in non_null:
        output_schema = _schema(spec, non_null["$ref"].split("/")[-1])
    else:
        output_schema = non_null
    assert output_schema["type"] == "object"
    assert "additionalProperties" in output_schema


def test_layer5_freshness_and_sync_routes_publish_concrete_response_models() -> None:
    spec = _spec("layer5-ground-truth.json")

    assert _response_schema(spec, "/api/v1/truths/sync-kg", "post") == {
        "$ref": "#/components/schemas/SyncToKgResponse"
    }
    assert _response_schema(spec, "/api/v1/truths/check-stale", "post") == {
        "$ref": "#/components/schemas/FreshnessCheckResponse"
    }
    assert _response_schema(spec, "/api/v1/truths/stale") == {
        "$ref": "#/components/schemas/StaleTruthsResponse"
    }
    assert _response_schema(spec, "/api/v1/truths/freshness-summary") == {
        "$ref": "#/components/schemas/FreshnessSummaryResponse"
    }

    assert set(_schema(spec, "SyncToKgResponse")["required"]) >= {"synced", "failed", "total_pending"}
    assert set(_schema(spec, "FreshnessCheckResponse")["required"]) >= {
        "checked",
        "marked_stale",
        "dry_run",
        "timestamp",
    }
    assert set(_schema(spec, "FreshnessSummaryResponse")["required"]) >= {
        "tenant_id",
        "timestamp",
        "summary",
        "warning_threshold_days",
    }


def test_error_envelope_shape_is_canonical_for_layer4_and_layer5() -> None:
    for spec_name in ("layer4-agents.json", "layer5-ground-truth.json"):
        error_schema = _schema(_spec(spec_name), "ErrorResponse")
        assert error_schema["required"] == ["message", "code", "trace_id"]
        assert error_schema["additionalProperties"] is False
        assert set(error_schema["properties"]) == {"message", "code", "trace_id", "details"}
