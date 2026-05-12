"""Contract tests for Layer 3 Value Trees and Variables endpoints consumed by frontend."""

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


class TestL3ValueTreeContracts:
    """Contract tests for /v1/value-trees/* endpoints."""

    def test_value_tree_response_matches_openapi(self) -> None:
        """GET /v1/value-trees/{entity_id} response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "entity_id": "val-1",
            "name": "Revenue Growth",
            "entity_type": "ValueDriver",
            "upstream": [
                {"entity_id": "cap-1", "name": "Sales Automation", "entity_type": "Capability", "type": "ENABLES"},
            ],
            "downstream": [
                {"entity_id": "out-1", "name": "Increased Revenue", "entity_type": "Outcome", "type": "ACHIEVES"},
            ],
            "depth": 2,
            "total_nodes": 3,
        }
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "ValueTree" in components:
            schema = _schema_ref(l3_openapi, "ValueTree")
            assert_matches_schema(sample, schema, root=l3_openapi)

    def test_value_tree_paths_response_matches_openapi(self) -> None:
        """GET /v1/value-trees/{entity_id}/paths response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "paths": [
                {
                    "nodes": [
                        {"id": "val-1", "name": "Revenue Growth", "entity_type": "ValueDriver"},
                        {"id": "cap-1", "name": "Sales Automation", "entity_type": "Capability"},
                        {"id": "out-1", "name": "Increased Revenue", "entity_type": "Outcome"},
                    ],
                    "relationships": [
                        {"source": "cap-1", "target": "val-1", "type": "ENABLES"},
                        {"source": "val-1", "target": "out-1", "type": "ACHIEVES"},
                    ],
                    "value_score": 0.85,
                    "impact": "high",
                }
            ],
            "total_paths": 1,
        }
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "ValueTreePaths" in components:
            schema = _schema_ref(l3_openapi, "ValueTreePaths")
            assert_matches_schema(sample, schema, root=l3_openapi)


class TestL3VariableContracts:
    """Contract tests for /v1/formulas/variables endpoints."""

    def test_variables_list_response_matches_openapi(self) -> None:
        """GET /v1/formulas/variables response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = [
            {
                "id": "var-1",
                "variable_id": "var-1",
                "name": "revenue",
                "display_name": "Revenue",
                "description": "Total revenue amount",
                "type": "number",
                "unit": "USD",
                "default_value": 0,
                "source": "manual",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-15T10:00:00Z",
            }
        ]
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "Variable" in components:
            schema = _schema_ref(l3_openapi, "Variable")
            for item in sample:
                assert_matches_schema(item, schema, root=l3_openapi)

    def test_variable_types_enum_values(self) -> None:
        """Variable type enum includes expected values."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        expected_types = {"number", "string", "boolean", "date", "currency", "percentage"}
        
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "Variable" in components:
            var_schema = components["Variable"]
            type_prop = var_schema.get("properties", {}).get("type", {})
            if "enum" in type_prop:
                schema_types = set(type_prop["enum"])
                missing = expected_types - schema_types
                assert not missing, f"Variable type enum missing values: {missing}"

    def test_variable_source_enum_values(self) -> None:
        """Variable source enum includes expected values."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        expected_sources = {"manual", "extracted", "calculated", "external"}
        
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "Variable" in components:
            var_schema = components["Variable"]
            source_prop = var_schema.get("properties", {}).get("source", {})
            if "enum" in source_prop:
                schema_sources = set(source_prop["enum"])
                missing = expected_sources - schema_sources
                assert not missing, f"Variable source enum missing values: {missing}"


class TestL3BusinessCaseContracts:
    """Contract tests for Business Case endpoints."""

    def test_business_case_response_matches_openapi(self) -> None:
        """GET /v1/business-cases/{id} response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "id": "bc-1",
            "name": "ROI Analysis Q1 2024",
            "description": "Return on investment analysis for automation project",
            "status": "active",
            "entity_id": "cap-1",
            "formula_id": "formula-1",
            "calculated_value": 1250000,
            "currency": "USD",
            "confidence_score": 0.92,
            "inputs": {
                "revenue": 2000000,
                "cost": 750000,
            },
            "variables_used": ["revenue", "cost"],
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z",
            "created_by": "user-1",
        }
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "BusinessCase" in components:
            schema = _schema_ref(l3_openapi, "BusinessCase")
            assert_matches_schema(sample, schema, root=l3_openapi)

    def test_formula_evaluation_request_matches_openapi(self) -> None:
        """POST /v1/formulas/evaluate request matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "formula_id": "formula-1",
            "inputs": {
                "revenue": 1000000,
                "cost": 500000,
            },
            "entity_id": "cap-1",
        }
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "FormulaEvaluationRequest" in components:
            schema = _schema_ref(l3_openapi, "FormulaEvaluationRequest")
            assert_matches_schema(sample, schema, root=l3_openapi)

    def test_formula_evaluation_response_matches_openapi(self) -> None:
        """POST /v1/formulas/evaluate response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "formula_id": "formula-1",
            "result": 2.0,
            "unit": "ratio",
            "confidence_score": 0.95,
            "inputs_used": {
                "revenue": 1000000,
                "cost": 500000,
            },
            "missing_inputs": [],
            "calculation_trace": ["revenue / cost = 1000000 / 500000 = 2.0"],
        }
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "FormulaEvaluationResponse" in components:
            schema = _schema_ref(l3_openapi, "FormulaEvaluationResponse")
            assert_matches_schema(sample, schema, root=l3_openapi)
