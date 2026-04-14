"""Contract tests for Layer 3/Layer 4 responses consumed by frontend."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any

from .schema_assertions import assert_matches_schema

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


def _extract_fastapi_paths(source_file: Path, app_names: set[str]) -> set[str]:
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
        l3_openapi = _load_json(OPENAPI_L3_PATH)
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
        schema = _schema_ref(l3_openapi, "GraphRAGResponse")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_hybrid_search_response_sample_matches_l3_openapi(self) -> None:
        l3_openapi = _load_json(OPENAPI_L3_PATH)
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
        schema = _schema_ref(l3_openapi, "SearchResponse")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_monitored_l3_frontend_paths_exist_in_openapi_contract(self) -> None:
        implementation_paths = _extract_fastapi_paths(L3_MAIN_PATH, {"app"})
        contract_paths = set(_load_json(OPENAPI_L3_PATH).get("paths", {}).keys())
        monitored = {"/v1/query/graph", "/v1/search/hybrid", "/v1/entity/{entity_id}/context", "/v1/entity/traverse"}
        missing = {p for p in monitored if p in implementation_paths and p not in contract_paths}
        assert not missing, f"Layer 3 OpenAPI drift for frontend-consumed endpoints: {sorted(missing)}"


class TestL4WorkflowSSEContractsConsumedByUI:
    def test_workflow_event_payload_matches_l4_openapi(self) -> None:
        l4_openapi = _load_json(OPENAPI_L4_PATH)
        sample_event = {
            "event_id": "evt-123",
            "event_type": "progress",
            "timestamp": "2026-04-14T00:00:00Z",
            "message": "Workflow running",
            "payload": {"workflow_id": "wf-123", "workflow_type": "business_case", "status": "running", "progress_percentage": 45},
        }
        schema = _schema_ref(l4_openapi, "WorkflowEvent")
        assert_matches_schema(sample_event, schema, root=l4_openapi)

    def test_workflow_sse_endpoint_is_declared_as_event_stream(self) -> None:
        l4_openapi = _load_json(OPENAPI_L4_PATH)
        content = l4_openapi["paths"]["/workflows/{workflow_id}/events"]["get"]["responses"]["200"]["content"]
        assert "text/event-stream" in content

    def test_monitored_l4_workflow_paths_exist_in_openapi_contract(self) -> None:
        implementation_paths = _extract_fastapi_paths(L4_WORKFLOWS_PATH, {"router"})
        contract_paths = set(_load_json(OPENAPI_L4_PATH).get("paths", {}).keys())
        monitored = {"/workflows", "/workflows/active", "/workflows/{workflow_id}", "/workflows/{workflow_id}/events", "/workflows/{workflow_id}/resume"}
        missing = {p for p in monitored if p in implementation_paths and p not in contract_paths}
        assert not missing, f"Layer 4 OpenAPI drift for workflow endpoints: {sorted(missing)}"
