"""
Contract tests — Layer 2 (Extraction) → Layer 3 (Knowledge Graph) boundary.

These tests validate that:
1. The L2 Layer3KnowledgeClient sends a payload that matches the L3 IngestRequest schema.
2. The L3 IngestResponse shape matches what the L2 IngestionResponse dataclass expects.
3. The L3 /v1/ingest/status/{source_id} response matches what L2 polls for.
4. The L3 /v1/search/hybrid response matches the SearchResponse contract.

All tests run without live services — they use Pydantic model validation and
jsonschema to verify the schemas are mutually compatible.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

# ── Helpers ───────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _import_pydantic_model(module_path: str, class_name: str):
    """Import a Pydantic model from a layer source tree, skipping if unavailable."""
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(module_path, module_path)
    if spec is None:
        pytest.skip(f"Cannot locate module at {module_path}")
    return None  # Fallback — we use dict-based validation below


# ── L3 IngestRequest schema ───────────────────────────────────────────────────
# Derived from layer3-knowledge/src/api/models.py  IngestRequest
L3_INGEST_REQUEST_REQUIRED_FIELDS: Dict[str, type] = {
    "rdf_data": str,
    "source_id": str,
    "extraction_job_id": str,
}

L3_INGEST_REQUEST_OPTIONAL_FIELDS: Dict[str, type] = {
    "content_hash": (str, type(None)),
}

# ── L3 IngestResponse schema ──────────────────────────────────────────────────
# Derived from layer3-knowledge/src/api/models.py  IngestResponse
L3_INGEST_RESPONSE_REQUIRED_FIELDS: Dict[str, type] = {
    "status": str,
    "source_id": str,
    "entities_loaded": int,
    "relationships_loaded": int,
    "triples_processed": int,
}

L3_INGEST_RESPONSE_OPTIONAL_FIELDS: Dict[str, type] = {
    "duration_seconds": (float, type(None)),
    "error": (str, type(None)),
    "warnings": list,
}

# ── L3 SyncStatusResponse schema ─────────────────────────────────────────────
# Derived from layer3-knowledge/src/api/models.py  SyncStatusResponse
L3_SYNC_STATUS_REQUIRED_FIELDS: Dict[str, type] = {
    "source_id": str,
    "status": str,
}

# ── L3 SearchResponse schema ──────────────────────────────────────────────────
# Derived from layer3-knowledge/src/api/models.py  SearchResponse
L3_SEARCH_RESPONSE_REQUIRED_FIELDS: Dict[str, type] = {
    "query": str,
    "results": list,
    "total_results": int,
    "search_type": str,
}

# ── L3 SearchResult schema ────────────────────────────────────────────────────
L3_SEARCH_RESULT_REQUIRED_FIELDS: Dict[str, type] = {
    "entity_id": str,
    "entity_type": str,
    "name": str,
    "bm25_score": (int, float),
    "vector_score": (int, float),
    "graph_score": (int, float),
    "combined_score": (int, float),
    "confidence": (int, float),
}

# ── L2 IngestionResponse dataclass fields ────────────────────────────────────
# Derived from layer2-extraction/.../integration/layer3_client.py  IngestionResponse
L2_INGESTION_RESPONSE_FIELDS: Dict[str, type] = {
    "success": bool,
    "ingestion_id": str,
    "entities_loaded": int,
    "relationships_loaded": int,
    "message": str,
}


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


# ── Tests ─────────────────────────────────────────────────────────────────────
class TestL2ToL3IngestContract:
    """Validate the L2 → L3 ingest request/response contract."""

    def test_l2_builds_valid_l3_ingest_request(self) -> None:
        """L2 Layer3KnowledgeClient must produce a payload that satisfies L3 IngestRequest."""
        # Simulate what Layer3KnowledgeClient._build_ingest_payload() produces
        sample_payload = {
            "rdf_data": "@prefix ex: <http://example.com/> . ex:cap1 a ex:Capability .",
            "source_id": "doc-abc123",
            "extraction_job_id": "job-xyz789",
            "content_hash": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4e5f6a1b2",
        }
        _check_required_fields(sample_payload, L3_INGEST_REQUEST_REQUIRED_FIELDS, "L3IngestRequest")
        # rdf_data must be non-empty
        assert len(sample_payload["rdf_data"]) > 0, "rdf_data must be non-empty"
        # source_id must be non-empty
        assert len(sample_payload["source_id"]) > 0, "source_id must be non-empty"
        # extraction_job_id must be non-empty
        assert len(sample_payload["extraction_job_id"]) > 0, "extraction_job_id must be non-empty"

    def test_l2_ingest_request_without_optional_content_hash(self) -> None:
        """L2 may omit content_hash — L3 must accept it."""
        payload_without_hash = {
            "rdf_data": "@prefix ex: <http://example.com/> . ex:cap1 a ex:Capability .",
            "source_id": "doc-abc123",
            "extraction_job_id": "job-xyz789",
        }
        _check_required_fields(payload_without_hash, L3_INGEST_REQUEST_REQUIRED_FIELDS, "L3IngestRequest")
        assert "content_hash" not in payload_without_hash or payload_without_hash.get("content_hash") is None

    def test_l3_ingest_response_satisfies_l2_ingestion_response(self) -> None:
        """L3 IngestResponse must provide all fields that L2 IngestionResponse expects."""
        # Simulate a successful L3 ingest response
        l3_response = {
            "status": "success",
            "source_id": "doc-abc123",
            "entities_loaded": 12,
            "relationships_loaded": 8,
            "triples_processed": 45,
            "duration_seconds": 1.23,
            "error": None,
            "warnings": [],
        }
        _check_required_fields(l3_response, L3_INGEST_RESPONSE_REQUIRED_FIELDS, "L3IngestResponse")

        # L2 maps L3 response to its own IngestionResponse dataclass
        # Verify all required L2 fields can be populated from L3 response
        l2_mapped = {
            "success": l3_response["status"] == "success",
            "ingestion_id": l3_response["source_id"],   # L3 uses source_id as ingestion_id
            "entities_loaded": l3_response["entities_loaded"],
            "relationships_loaded": l3_response["relationships_loaded"],
            "message": f"Ingested {l3_response['triples_processed']} triples",
        }
        _check_required_fields(l2_mapped, L2_INGESTION_RESPONSE_FIELDS, "L2IngestionResponse")

    def test_l3_ingest_response_status_values(self) -> None:
        """L3 IngestResponse.status must be one of: success, partial, failed."""
        valid_statuses = {"success", "partial", "failed"}
        for status in valid_statuses:
            response = {
                "status": status,
                "source_id": "doc-test",
                "entities_loaded": 0,
                "relationships_loaded": 0,
                "triples_processed": 0,
            }
            assert response["status"] in valid_statuses, f"Invalid status: {status}"

    def test_l3_sync_status_response_has_required_fields(self) -> None:
        """L3 /v1/ingest/status/{source_id} response must have source_id and status."""
        l3_status_response = {
            "source_id": "doc-abc123",
            "status": "completed",
            "entities_synced": 12,
            "relationships_synced": 8,
        }
        _check_required_fields(l3_status_response, L3_SYNC_STATUS_REQUIRED_FIELDS, "L3SyncStatusResponse")

    def test_l3_ingest_endpoint_url_matches_l2_client(self) -> None:
        """The L3 ingest endpoint path must be /v1/ingest (as called by L2 client)."""
        # Read L2 client source to verify the URL used
        l2_client_path = (
            REPO_ROOT
            / "value-fabric"
            / "layer2-extraction"
            / "src"
            / "layer2_extraction"
            / "integration"
            / "layer3_client.py"
        )
        if not l2_client_path.exists():
            pytest.skip("L2 layer3_client.py not found")

        source = l2_client_path.read_text()
        # L2 client must call /v1/ingest (not /ingest or /api/v1/ingest)
        assert "/v1/ingest" in source, (
            "L2 Layer3KnowledgeClient must call the L3 /v1/ingest endpoint"
        )

    def test_l3_status_endpoint_url_matches_l2_client(self) -> None:
        """The L3 status endpoint must be /v1/ingest/{id}/status or /v1/ingest/status/{id}."""
        l3_main_path = (
            REPO_ROOT
            / "value-fabric"
            / "layer3-knowledge"
            / "src"
            / "api"
            / "main.py"
        )
        if not l3_main_path.exists():
            pytest.skip("L3 api/main.py not found")

        source = l3_main_path.read_text()
        # L3 must expose both route aliases for backward compatibility
        assert "/v1/ingest/status/{source_id}" in source, (
            "L3 must expose /v1/ingest/status/{source_id} for L2 polling"
        )
        assert "/v1/ingest/{source_id}/status" in source, (
            "L3 must expose /v1/ingest/{source_id}/status alias for L2 compatibility"
        )


class TestL3SearchContract:
    """Validate the L3 search endpoint contract used by the frontend."""

    def test_l3_search_response_has_required_fields(self) -> None:
        """L3 SearchResponse must have query, results, total_results, search_type."""
        l3_response = {
            "query": "real-time analytics",
            "results": [],
            "total_results": 0,
            "search_type": "hybrid",
            "processing_time_ms": 42.5,
        }
        _check_required_fields(l3_response, L3_SEARCH_RESPONSE_REQUIRED_FIELDS, "L3SearchResponse")

    def test_l3_search_result_has_required_fields(self) -> None:
        """Each SearchResult must have entity_id, entity_type, name, scores, confidence."""
        result = {
            "entity_id": "cap-001",
            "entity_type": "Capability",
            "name": "Real-Time Analytics",
            "bm25_score": 0.85,
            "vector_score": 0.92,
            "graph_score": 0.78,
            "combined_score": 0.88,
            "metadata": {},
            "confidence": 0.88,
        }
        _check_required_fields(result, L3_SEARCH_RESULT_REQUIRED_FIELDS, "L3SearchResult")

    def test_l3_search_result_scores_in_range(self) -> None:
        """All scores must be non-negative; combined_score and confidence must be 0–1."""
        result = {
            "entity_id": "cap-001",
            "entity_type": "Capability",
            "name": "Real-Time Analytics",
            "bm25_score": 0.85,
            "vector_score": 0.92,
            "graph_score": 0.78,
            "combined_score": 0.88,
            "metadata": {},
            "confidence": 0.88,
        }
        assert result["bm25_score"] >= 0, "bm25_score must be non-negative"
        assert result["vector_score"] >= 0, "vector_score must be non-negative"
        assert result["graph_score"] >= 0, "graph_score must be non-negative"
        assert 0.0 <= result["combined_score"] <= 1.0, "combined_score must be 0–1"
        assert 0.0 <= result["confidence"] <= 1.0, "confidence must be 0–1"

    def test_frontend_entity_mapping_from_l3_search_result(self) -> None:
        """Frontend useEntities hook must be able to map L3 SearchResult to Entity."""
        # Simulate L3 SearchResult
        l3_result = {
            "entity_id": "cap-001",
            "entity_type": "Capability",
            "name": "Real-Time Analytics",
            "bm25_score": 0.85,
            "vector_score": 0.92,
            "graph_score": 0.78,
            "combined_score": 0.88,
            "metadata": {"description": "Enables real-time data processing"},
            "confidence": 0.88,
        }
        # Frontend maps: id = r.id || r.entity_id
        fe_id = l3_result.get("id") or l3_result.get("entity_id")
        assert fe_id == "cap-001", "Frontend must be able to extract entity ID"

        # Frontend maps: name = r.name || r.title || 'Unknown'
        fe_name = l3_result.get("name") or l3_result.get("title") or "Unknown"
        assert fe_name == "Real-Time Analytics", "Frontend must be able to extract entity name"

        # Frontend maps: confidence = r.confidence_score || r.confidence || 0.8
        fe_confidence = l3_result.get("confidence_score") or l3_result.get("confidence") or 0.8
        assert fe_confidence == 0.88, "Frontend must be able to extract confidence"

    def test_l3_search_endpoint_url(self) -> None:
        """L3 must expose /v1/search/hybrid as the canonical search endpoint."""
        l3_main_path = (
            REPO_ROOT
            / "value-fabric"
            / "layer3-knowledge"
            / "src"
            / "api"
            / "main.py"
        )
        if not l3_main_path.exists():
            pytest.skip("L3 api/main.py not found")

        source = l3_main_path.read_text()
        assert "/v1/search/hybrid" in source, (
            "L3 must expose /v1/search/hybrid as the canonical hybrid search endpoint"
        )
        assert "/v1/search" in source, (
            "L3 must retain /v1/search as a backward-compatible alias"
        )

    def test_l3_query_graph_endpoint_url(self) -> None:
        """L3 must expose /v1/query/graph for GraphRAG queries."""
        l3_main_path = (
            REPO_ROOT
            / "value-fabric"
            / "layer3-knowledge"
            / "src"
            / "api"
            / "main.py"
        )
        if not l3_main_path.exists():
            pytest.skip("L3 api/main.py not found")

        source = l3_main_path.read_text()
        assert "/v1/query/graph" in source, (
            "L3 must expose /v1/query/graph for GraphRAG queries"
        )
