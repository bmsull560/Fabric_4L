"""Contract tests for Layer 3 Formula endpoints consumed by frontend."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schema_assertions import assert_matches_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENAPI_L3_PATH = REPO_ROOT / "contracts" / "openapi" / "layer3-knowledge.json"


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _schema_ref(doc: dict[str, Any], name: str) -> dict[str, Any]:
    return {"$ref": f"#/components/schemas/{name}", "components": doc.get("components", {})}


class TestL3FormulaContracts:
    """Contract tests for /v1/formulas/* endpoints."""

    def test_formula_list_response_matches_openapi(self) -> None:
        """GET /v1/formulas response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = [
            {
                "id": "formula-1",
                "formula_id": "formula-1",
                "name": "ROI Calculation",
                "description": "Calculate return on investment",
                "pack_id": "pack-1",
                "pack_name": "Financial Pack",
                "version": "1.0.0",
                "status": "active",
                "owner": "user-1",
                "updated_at": "2024-01-15T10:00:00Z",
                "created_at": "2024-01-01T00:00:00Z",
                "used_in_count": 3,
                "governance_score": 0.95,
                "last_reviewed": "2024-01-10T00:00:00Z",
                "reviewers": ["user-1", "user-2"],
                "expression": "revenue / cost",
                "variables": ["revenue", "cost"],
            }
        ]
        # Formulas list returns FormulasRegistryResponse wrapper
        schema = _schema_ref(l3_openapi, "FormulasRegistryResponse")
        # Test wrapper structure
        wrapper_sample = {"formulas": sample, "total": len(sample)}
        assert_matches_schema(wrapper_sample, schema, root=l3_openapi)

    def test_formula_detail_response_matches_openapi(self) -> None:
        """GET /v1/formulas/{id} response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "id": "formula-1",
            "formula_id": "formula-1",
            "name": "ROI Calculation",
            "description": "Calculate return on investment",
            "pack_id": "pack-1",
            "pack_name": "Financial Pack",
            "version": "1.0.0",
            "status": "active",
            "owner": "user-1",
            "updated_at": "2024-01-15T10:00:00Z",
            "created_at": "2024-01-01T00:00:00Z",
            "used_in_count": 3,
            "governance_score": 0.95,
            "last_reviewed": "2024-01-10T00:00:00Z",
            "reviewers": ["user-1", "user-2"],
            "expression": "revenue / cost",
            "variables": ["revenue", "cost"],
        }
        schema = _schema_ref(l3_openapi, "FormulaMetadata")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_formula_approvals_response_matches_openapi(self) -> None:
        """GET /v1/formulas/approvals/pending response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = [
            {
                "id": "approval-1",
                "formula_id": "formula-2",
                "formula_name": "Cost Analysis",
                "submitted_by": "user-3",
                "submitted_at": "2024-01-14T10:00:00Z",
                "change_summary": "Added new variable",
                "previous_version": "1.0.0",
                "status": "pending",
            }
        ]
        # Approvals list is an array of ApprovalQueueItem objects
        schema = _schema_ref(l3_openapi, "ApprovalQueueItem")
        for item in sample:
            assert_matches_schema(item, schema, root=l3_openapi)

    def test_formula_approval_request_payload_matches_openapi(self) -> None:
        """POST /v1/formulas/{id}/approve request payload matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "action": "approve",
            "reason": "Formula looks correct",
        }
        # Approval request uses ApproveRequest schema
        schema = _schema_ref(l3_openapi, "ApproveRequest")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_formula_submit_response_matches_openapi(self) -> None:
        """POST /v1/formulas/{id}/submit response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "id": "formula-2",
            "formula_id": "formula-2",
            "name": "Cost Analysis",
            "status": "pending",
            "version": "1.1.0",
            "updated_at": "2024-01-15T12:00:00Z",
        }
        # Submit response returns FormulaMetadata
        schema = _schema_ref(l3_openapi, "FormulaMetadata")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_formula_status_enum_values(self) -> None:
        """Formula status values match expected enum."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        expected_statuses = {"active", "draft", "pending", "deprecated", "archived"}
        
        # Check schema defines all expected statuses
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "FormulaMetadata" in components:
            formula_schema = components["FormulaMetadata"]
            status_prop = formula_schema.get("properties", {}).get("status", {})
            if "enum" in status_prop:
                schema_statuses = set(status_prop["enum"])
                missing = expected_statuses - schema_statuses
                assert not missing, f"Formula status enum missing values: {missing}"

    def test_formula_approval_action_enum_values(self) -> None:
        """Formula approval action values match expected enum."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        expected_actions = {"approve", "reject", "request_changes"}
        
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "ApproveRequest" in components:
            req_schema = components["ApproveRequest"]
            action_prop = req_schema.get("properties", {}).get("action", {})
            if "enum" in action_prop:
                schema_actions = set(action_prop["enum"])
                missing = expected_actions - schema_actions
                assert not missing, f"Approval action enum missing values: {missing}"
