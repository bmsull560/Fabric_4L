"""Contract tests for Layer 3/Layer 4 responses consumed by frontend.

NOTE: If tests fail due to missing schemas, regenerate OpenAPI contracts:
    python scripts/export_openapi.py
"""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

import pytest

from .schema_assertions import SchemaValidationError, assert_matches_schema

REPO_ROOT = Path(__file__).resolve().parents[2]
OPENAPI_L3_PATH = REPO_ROOT / "contracts" / "openapi" / "layer3-knowledge.json"
OPENAPI_L4_PATH = REPO_ROOT / "contracts" / "openapi" / "layer4-agents.json"
L3_MAIN_PATH = REPO_ROOT / "value-fabric" / "layer3-knowledge" / "src" / "api" / "main.py"
L4_WORKFLOWS_PATH = REPO_ROOT / "value-fabric" / "layer4-agents" / "src" / "api" / "routes" / "workflows.py"

HTTP_DECORATORS = {"get", "post", "put", "delete", "patch"}


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _schema_ref(doc: dict[str, Any], name: str) -> dict[str, Any]:
    return {"$ref": f"#/components/schemas/{name}", "components": doc.get("components", {})}


def _assert_schema(sample: dict[str, Any], openapi_path: Path, schema_name: str) -> None:
    """Helper to validate a sample against an OpenAPI schema with clear error messages.

    Args:
        sample: The data sample to validate
        openapi_path: Path to the OpenAPI specification file
        schema_name: Name of the schema in components/schemas to validate against

    Raises:
        pytest.fail: If schema validation fails with a descriptive message
    """
    openapi = _load_json(openapi_path)
    schema = _schema_ref(openapi, schema_name)
    try:
        assert_matches_schema(sample, schema, root=openapi)
    except SchemaValidationError as e:
        pytest.fail(f"Schema '{schema_name}' validation failed (contract may need regeneration): {e}")


def _extract_fastapi_paths(source_file: Path, app_names: set[str]) -> set[str]:
    """Extract FastAPI route paths from source file using AST parsing.

    WARNING: This function is sensitive to FastAPI decorator patterns.
    If routes use unusual patterns (e.g., @app.get() called indirectly,
    or decorators wrapped in other decorators), extraction may fail.

    Known supported patterns:
        @app.get("/path")
        @router.post("/path")
        @app.put("/path/{id}")

    If routes are missing from contract verification, check that they
    follow these patterns or update this function to handle new patterns.

    Args:
        source_file: Path to the Python source file to analyze
        app_names: Set of variable names that are FastAPI apps/routers (e.g., {"app", "router"})

    Returns:
        Set of route paths found in the file
    """
    tree = ast.parse(source_file.read_text(encoding="utf-8"))
    paths: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call) or not isinstance(decorator.func, ast.Attribute):
                continue
            if decorator.func.attr not in HTTP_DECORATORS:
                continue
            owner = decorator.func.value
            if not isinstance(owner, ast.Name) or owner.id not in app_names:
                continue
            if decorator.args and isinstance(decorator.args[0], ast.Constant) and isinstance(decorator.args[0].value, str):
                paths.add(decorator.args[0].value)
    return paths


class TestL3GraphContractsConsumedByFrontend:
    def test_graph_query_response_sample_matches_l3_openapi(self) -> None:
        sample = {
            "query": "invoice automation",
            "entities": [{"id": "cap-1", "name": "Automated Invoice Processing", "entity_type": "Capability", "confidence_score": 0.92}],
            "relationships": [{"source": "cap-1", "target": "uc-1", "type": "ENABLES", "confidence": 0.88}],
            "context_graph": {"nodes": [], "relationships": []},
            "confidence_score": 0.9,
            "sources": ["doc-123"],
            "processing_time_ms": 18.3,
            "answer": "Automated invoice processing is enabled by OCR and workflow orchestration.",
        }
        _assert_schema(sample, OPENAPI_L3_PATH, "GraphRAGResponse")

    def test_hybrid_search_response_sample_matches_l3_openapi(self) -> None:
        sample = {
            "query": "automation",
            "results": [{
                "entity_id": "cap-1",
                "entity_type": "Capability",
                "name": "Automated Invoice Processing",
                "description": "Capability",
                "bm25_score": 0.0,
                "vector_score": 0.91,
                "graph_score": 0.5,
                "combined_score": 0.8,
                "confidence": 0.92,
                "metadata": {},
            }],
            "total_results": 1,
            "search_type": "hybrid",
            "processing_time_ms": 22.1,
        }
        _assert_schema(sample, OPENAPI_L3_PATH, "SearchResponse")

    def test_monitored_l3_frontend_paths_exist_in_openapi_contract(self) -> None:
        implementation_paths = _extract_fastapi_paths(L3_MAIN_PATH, {"app"})
        contract_paths = set(_load_json(OPENAPI_L3_PATH).get("paths", {}).keys())
        monitored = {"/v1/query/graph", "/v1/search/hybrid", "/v1/entity/{entity_id}/context", "/v1/entity/traverse"}
        missing = {p for p in monitored if p in implementation_paths and p not in contract_paths}
        if missing:
            pytest.fail(
                f"Layer 3 OpenAPI drift: {sorted(missing)} exist in implementation but not in contract. "
                f"Run 'python scripts/export_openapi.py' to regenerate contracts."
            )


class TestL4WorkflowSSEContractsConsumedByUI:
    def test_workflow_event_payload_matches_l4_openapi(self) -> None:
        sample_event = {
            "event_id": "evt-123",
            "event_type": "progress",
            "timestamp": "2026-04-14T00:00:00Z",
            "message": "Workflow running",
            "payload": {"workflow_id": "wf-123", "workflow_type": "business_case", "status": "running", "progress_percentage": 45},
        }
        _assert_schema(sample_event, OPENAPI_L4_PATH, "WorkflowEvent")

    def test_workflow_sse_endpoint_is_declared_as_event_stream(self) -> None:
        l4_openapi = _load_json(OPENAPI_L4_PATH)
        try:
            content = l4_openapi["paths"]["/workflows/{workflow_id}/events"]["get"]["responses"]["200"]["content"]
        except KeyError as e:
            pytest.fail(f"SSE endpoint not found in OpenAPI contract (may need regeneration): {e}")
        assert "text/event-stream" in content, "Expected 'text/event-stream' content type for SSE endpoint"

    def test_monitored_l4_workflow_paths_exist_in_openapi_contract(self) -> None:
        implementation_paths = _extract_fastapi_paths(L4_WORKFLOWS_PATH, {"router"})
        contract_paths = set(_load_json(OPENAPI_L4_PATH).get("paths", {}).keys())
        monitored = {"/workflows", "/workflows/active", "/workflows/{workflow_id}", "/workflows/{workflow_id}/events", "/workflows/{workflow_id}/resume"}
        missing = {p for p in monitored if p in implementation_paths and p not in contract_paths}
        if missing:
            pytest.fail(
                f"Layer 4 OpenAPI drift: {sorted(missing)} exist in implementation but not in contract. "
                f"Run 'python scripts/export_openapi.py' to regenerate contracts."
            )
