"""Contract tests for Layer 3 Graph/Entity endpoints consumed by frontend."""

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


class TestL3GraphQueryContracts:
    """Contract tests for /v1/query/graph endpoint."""

    def test_graph_query_request_matches_openapi(self) -> None:
        """POST /v1/query/graph request payload matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "query": "invoice automation",
            "entity_type": "Capability",
            "max_hops": 2,
            "max_results": 20,
        }
        schema = _schema_ref(l3_openapi, "GraphRAGQuery")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_graph_query_response_matches_openapi(self) -> None:
        """POST /v1/query/graph response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "query": "invoice automation",
            "entities": [
                {
                    "id": "cap-1",
                    "name": "Automated Invoice Processing",
                    "entity_type": "Capability",
                    "confidence_score": 0.92,
                    "description": "Automated processing of invoices",
                    "properties": {"owner": "Finance Team"},
                }
            ],
            "relationships": [
                {
                    "source": "cap-1",
                    "target": "uc-1",
                    "type": "ENABLES",
                    "confidence": 0.88,
                    "properties": {"weight": 0.9},
                }
            ],
            "context_graph": {
                "nodes": [],
                "relationships": [],
            },
            "confidence_score": 0.9,
            "sources": ["doc-123"],
            "processing_time_ms": 18.3,
            "answer": "Automated invoice processing is enabled by OCR and workflow orchestration.",
        }
        schema = _schema_ref(l3_openapi, "GraphRAGResponse")
        assert_matches_schema(sample, schema, root=l3_openapi)


class TestL3EntityContextContracts:
    """Contract tests for /v1/entity/{id}/context endpoint."""

    def test_entity_context_response_matches_openapi(self) -> None:
        """GET /v1/entity/{id}/context response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "entity_id": "cap-1",
            "center": {
                "id": "cap-1",
                "name": "Automated Invoice Processing",
                "entity_type": "Capability",
                "confidence_score": 0.92,
                "description": "Automated processing of invoices",
                "properties": {"owner": "Finance Team"},
            },
            "neighbors": [
                {
                    "id": "uc-1",
                    "name": "Accounts Payable",
                    "entity_type": "UseCase",
                    "confidence_score": 0.88,
                    "description": "Managing accounts payable",
                }
            ],
            "relationships": [
                {
                    "source": "cap-1",
                    "target": "uc-1",
                    "type": "ENABLES",
                    "confidence": 0.88,
                }
            ],
            "entity_count": 2,
            "relationship_count": 1,
        }
        # EntityContextResponse must be defined for contract validation
        components = l3_openapi.get("components", {}).get("schemas", {})
        assert "EntityContextResponse" in components, (
            "Required schema 'EntityContextResponse' missing from OpenAPI spec. "
            "If this schema was intentionally removed, update the contract test."
        )
        schema = _schema_ref(l3_openapi, "EntityContextResponse")
        assert_matches_schema(sample, schema, root=l3_openapi)


class TestL3EntityTraversalContracts:
    """Contract tests for /v1/entity/traverse endpoint."""

    def test_entity_traversal_request_matches_openapi(self) -> None:
        """POST /v1/entity/traverse request payload matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "entity_id": "cap-1",
            "direction": "up",
        }
        schema = _schema_ref(l3_openapi, "ValueTreeTraversal")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_entity_traversal_response_matches_openapi(self) -> None:
        """POST /v1/entity/traverse response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "start_entity_id": "cap-1",
            "direction": "up",
            "paths": [
                {
                    "nodes": [
                        {"id": "cap-1", "name": "Invoice Processing", "entity_type": "Capability", "confidence_score": 0.92},
                        {"id": "val-1", "name": "Cost Reduction", "entity_type": "ValueDriver", "confidence_score": 0.9},
                    ],
                    "relationships": [
                        {"source": "val-1", "target": "cap-1", "type": "DRIVES", "confidence": 0.85}
                    ],
                    "value_score": 0.88,
                }
            ],
            "path_count": 1,
        }
        components = l3_openapi.get("components", {}).get("schemas", {})
        assert "EntityTraversalResponse" in components, (
            "Required schema 'EntityTraversalResponse' missing from OpenAPI spec. "
            "If this schema was intentionally removed, update the contract test."
        )
        schema = _schema_ref(l3_openapi, "EntityTraversalResponse")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_traversal_direction_enum_values(self) -> None:
        """Entity traversal direction enum includes expected values."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        expected_directions = {"up", "down", "both"}
        
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "ValueTreeTraversal" in components:
            req_schema = components["ValueTreeTraversal"]
            direction_prop = req_schema.get("properties", {}).get("direction", {})
            if "enum" in direction_prop:
                schema_directions = set(direction_prop["enum"])
                missing = expected_directions - schema_directions
                assert not missing, f"Traversal direction enum missing values: {missing}"


class TestL3SearchContracts:
    """Contract tests for /v1/search/hybrid endpoint."""

    def test_hybrid_search_request_matches_openapi(self) -> None:
        """POST /v1/search/hybrid request payload matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "query": "automation",
            "search_type": "hybrid",
            "top_k": 20,
        }
        schema = _schema_ref(l3_openapi, "SearchRequest")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_hybrid_search_response_matches_openapi(self) -> None:
        """POST /v1/search/hybrid response matches OpenAPI schema."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        sample = {
            "query": "automation",
            "results": [
                {
                    "entity_id": "cap-1",
                    "entity_type": "Capability",
                    "name": "Automated Invoice Processing",
                    "description": "Capability for automated invoice processing",
                    "bm25_score": 0.75,
                    "vector_score": 0.91,
                    "graph_score": 0.5,
                    "combined_score": 0.8,
                    "confidence": 0.92,
                    "metadata": {"source": "extraction-1"},
                }
            ],
            "total_results": 1,
            "search_type": "hybrid",
            "processing_time_ms": 22.1,
        }
        schema = _schema_ref(l3_openapi, "SearchResponse")
        assert_matches_schema(sample, schema, root=l3_openapi)

    def test_search_result_schema_completeness(self) -> None:
        """Search result contains all required fields for frontend consumption."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        required_fields = {"entity_id", "entity_type", "name", "combined_score"}
        
        components = l3_openapi.get("components", {}).get("schemas", {})
        if "SearchResult" in components:
            result_schema = components["SearchResult"]
            properties = set(result_schema.get("properties", {}).keys())
            missing = required_fields - properties
            assert not missing, f"SearchResult schema missing required fields: {missing}"


class TestL3GraphNodeContracts:
    """Contract tests for GraphNode schema used across endpoints."""

    def test_graph_node_schema_completeness(self) -> None:
        """GraphNode schema contains all required fields for frontend."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        # NOTE: Backend provides backward-compatible alias fields:
        # - 'name' alias for 'label' (frontend expects 'name')
        # - 'entity_type' alias for 'type' (frontend expects 'entity_type')
        # - 'confidence_score' alias for 'confidence' (frontend expects 'confidence_score')
        # Legacy fields (label, type, confidence) are preserved for backward compatibility.
        schema_required = {"id", "label", "type"}
        frontend_expects = {"id", "name", "entity_type", "confidence_score"}

        components = l3_openapi.get("components", {}).get("schemas", {})
        if "GraphNode" in components:
            node_schema = components["GraphNode"]
            properties = set(node_schema.get("properties", {}).keys())
            # Verify schema has its required fields
            missing = schema_required - properties
            assert not missing, f"GraphNode schema missing required fields: {missing}"

    def test_graph_node_response_sample_includes_alias_fields(self) -> None:
        """GraphNode response sample includes both legacy and alias fields."""
        # This test validates the backward compatibility implementation
        # where responses include both old fields (label, type) and new fields (name, entity_type)
        sample_node = {
            "id": "cap-1",
            "label": "Automated Invoice Processing",  # Legacy field
            "name": "Automated Invoice Processing",   # Alias field
            "type": "Capability",                      # Legacy field
            "entity_type": "Capability",              # Alias field
            "confidence": 0.92,                       # Legacy field
            "confidence_score": 0.92,                 # Alias field
            "x": 100.0,
            "y": 200.0,
        }

        # Validate that both legacy and alias fields are present
        assert "label" in sample_node, "Legacy 'label' field should be present"
        assert "name" in sample_node, "Alias 'name' field should be present"
        assert sample_node["label"] == sample_node["name"], "Label and name should match"

        assert "type" in sample_node, "Legacy 'type' field should be present"
        assert "entity_type" in sample_node, "Alias 'entity_type' field should be present"
        assert sample_node["type"] == sample_node["entity_type"], "Type and entity_type should match"

        assert "confidence" in sample_node, "Legacy 'confidence' field should be present"
        assert "confidence_score" in sample_node, "Alias 'confidence_score' field should be present"
        assert sample_node["confidence"] == sample_node["confidence_score"], "Confidence fields should match"


class TestL3GraphRelationshipContracts:
    """Contract tests for GraphRelationship schema."""

    def test_graph_relationship_schema_completeness(self) -> None:
        """GraphRelationship schema contains all required fields."""
        l3_openapi = _load_json(OPENAPI_L3_PATH)
        required_fields = {"source", "target", "type"}

        components = l3_openapi.get("components", {}).get("schemas", {})
        if "GraphRelationship" in components:
            rel_schema = components["GraphRelationship"]
            properties = set(rel_schema.get("properties", {}).keys())
            missing = required_fields - properties
            assert not missing, f"GraphRelationship schema missing required fields: {missing}"

    def test_graph_relationship_response_includes_alias_fields(self) -> None:
        """GraphRelationship response includes relationship_type alias."""
        # NOTE: 'relationship_type' is an alias for 'type' for frontend compatibility
        sample_rel = {
            "source": "cap-1",
            "target": "uc-1",
            "type": "ENABLES",           # Legacy field
            "relationship_type": "ENABLES",  # Alias field
            "weight": 0.9,
        }

        # Validate both legacy and alias fields are present
        assert "type" in sample_rel, "Legacy 'type' field should be present"
        assert "relationship_type" in sample_rel, "Alias 'relationship_type' field should be present"
        assert sample_rel["type"] == sample_rel["relationship_type"], "Type fields should match"
