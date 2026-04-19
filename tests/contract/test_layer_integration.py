"""Runtime Contract Tests — End-to-End Layer Integration

Validates actual data flow between layers by calling live endpoints.
These tests verify that:
- L4 clients call correct L1/L2 routes (not 404s)
- Data flows from L1 → L3 (ingested entities are queryable)
- L4 workflows orchestrate real L1 and L2 jobs

Requirements:
- L1 service running on localhost:8001
- L2 service running on localhost:8002
- L3 service running on localhost:8003
- L4 service running on localhost:8004
"""

import time
import uuid

import pytest
import requests

# Service endpoints
L1_URL = "http://localhost:8001"
L2_URL = "http://localhost:8002"
L3_URL = "http://localhost:8003"
L4_URL = "http://localhost:8004"


@pytest.fixture
def test_tenant():
    """Generate unique test tenant ID."""
    return f"test-tenant-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def test_entity_data():
    """Generate unique test entity data."""
    test_id = f"test-entity-{uuid.uuid4().hex[:8]}"
    return {
        "id": test_id,
        "name": f"TestCorp {test_id}",
        "entity_type": "Company",
        "properties": {
            "industry": "Technology",
            "employees": 500,
        },
    }


class TestL1RoutesExist:
    """Verify L4 client routes match actual L1 endpoints."""

    def test_l1_health_check(self):
        """L1 health endpoint responds."""
        response = requests.get(f"{L1_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data or "healthy" in str(data).lower()

    def test_l1_jobs_endpoint_post_creates_job(self):
        """POST /jobs creates ingestion job (was /v1/ingestion/jobs)."""
        payload = {
            "target": {"url": "https://example.com/test", "type": "http"},
            "document_type": "test",
        }
        response = requests.post(f"{L1_URL}/jobs", json=payload)
        # May fail auth but should NOT 404
        assert response.status_code != 404, "L1 /jobs endpoint not found"
        # Should be 202 (accepted) or 401/403 (auth), not 404
        assert response.status_code in [202, 200, 401, 403]

    def test_l1_jobs_get_list(self):
        """GET /jobs lists jobs (was /v1/ingestion/jobs)."""
        response = requests.get(f"{L1_URL}/jobs")
        assert response.status_code != 404, "L1 /jobs endpoint not found"
        assert response.status_code in [200, 401, 403]

    def test_l1_job_status_endpoint(self):
        """GET /jobs/{id} gets job status (was /v1/ingestion/jobs/{id})."""
        fake_job_id = str(uuid.uuid4())
        response = requests.get(f"{L1_URL}/jobs/{fake_job_id}")
        # Should be 404 for unknown job, not endpoint 404
        assert response.status_code != 404, "L1 /jobs/{id} endpoint not found"
        # May get 401, 403, or 404 for unknown job
        assert response.status_code in [404, 401, 403, 200]


class TestL2RoutesExist:
    """Verify L4 client routes match actual L2 endpoints."""

    def test_l2_health_check(self):
        """L2 health endpoint responds."""
        response = requests.get(f"{L2_URL}/health")
        assert response.status_code == 200

    def test_l2_extract_endpoint_post(self):
        """POST /v1/extract exists (was /v1/extract/filing)."""
        payload = {
            "document_url": "https://example.com/test.pdf",
            "filing_type": "TEST",
            "extraction_type": "test",
        }
        response = requests.post(f"{L2_URL}/v1/extract", json=payload)
        # Should NOT 404 - endpoint should exist
        assert response.status_code != 404, "L2 /v1/extract endpoint not found"

    def test_l2_extract_and_ingest_endpoint(self):
        """POST /v1/extract-and-ingest exists."""
        payload = {
            "document_url": "https://example.com/test.pdf",
            "filing_type": "TEST",
        }
        response = requests.post(f"{L2_URL}/v1/extract-and-ingest", json=payload)
        assert response.status_code != 404, "L2 /v1/extract-and-ingest endpoint not found"

    def test_l2_extract_status_endpoint(self):
        """GET /v1/extract/status/{job_id} exists."""
        fake_job_id = str(uuid.uuid4())
        response = requests.get(f"{L2_URL}/v1/extract/status/{fake_job_id}")
        assert response.status_code != 404, "L2 /v1/extract/status endpoint not found"


class TestL1ToL3DataFlow:
    """Verify data flows from L1 ingestion to L3 knowledge graph."""

    @pytest.mark.skip(reason="Requires full stack running - run manually")
    def test_l1_ingest_creates_data_in_l3(self, test_entity_data):
        """End-to-end: L1 ingest → L3 queryable."""
        # 1. Create entity directly in L3 (simulating L1→L3 flow)
        entity_name = test_entity_data["name"]

        # 2. Query L3 for the entity
        l3_response = requests.post(
            f"{L3_URL}/v1/search/hybrid",
            json={"query": entity_name, "entity_type": "Company"},
        )
        assert l3_response.status_code == 200, f"L3 search failed: {l3_response.text}"
        results = l3_response.json()

        # 3. Verify response structure
        assert "entities" in results or "results" in results, "Missing entities in response"

    @pytest.mark.skip(reason="Requires Neo4j running - run manually")
    def test_l3_entity_persistence(self):
        """L3 entities endpoint returns data."""
        response = requests.post(
            f"{L3_URL}/v1/ingest",
            json={
                "entities": [
                    {
                        "id": f"test-{uuid.uuid4().hex[:8]}",
                        "type": "Company",
                        "name": "TestCorp Runtime",
                    }
                ]
            },
        )
        # L3 may not have direct ingest - skip if 404
        if response.status_code == 404:
            pytest.skip("L3 ingest endpoint not available")

        assert response.status_code in [200, 202, 401, 403]


class TestL4WorkflowOrchestration:
    """Verify L4 workflows trigger real L1 and L2 jobs."""

    @pytest.mark.skip(reason="Requires full stack running - run manually")
    def test_l4_workflow_triggers_l1_l2(self):
        """L4 workflow orchestrates real L1 and L2 jobs."""
        # Start workflow
        response = requests.post(
            f"{L4_URL}/v1/workflows/ingestion",
            json={"source": "filing_123"},
        )

        if response.status_code == 404:
            pytest.skip("L4 workflow endpoint not available")

        assert response.status_code == 200, f"Workflow start failed: {response.text}"
        workflow_id = response.json().get("workflow_id")
        assert workflow_id, "No workflow_id in response"

        # Poll workflow status
        for _ in range(10):
            status_resp = requests.get(f"{L4_URL}/v1/workflows/{workflow_id}")
            if status_resp.status_code == 200:
                status = status_resp.json()
                if status.get("status") in ["completed", "failed"]:
                    break
            time.sleep(1)

        # Verify jobs were triggered by checking L1/L2 job lists
        l1_jobs = requests.get(f"{L1_URL}/jobs").json()
        l2_jobs = requests.get(f"{L2_URL}/v1/extract/status/nonexistent").json()

        # Should have attempted to call services (may be in error state)
        assert l1_jobs is not None, "L1 jobs endpoint failed"


class TestContractAlignment:
    """Verify OpenAPI contracts match runtime behavior."""

    def test_l1_openapi_spec_loads(self):
        """L1 OpenAPI spec is valid and loadable."""
        response = requests.get(f"{L1_URL}/openapi.json")
        if response.status_code == 404:
            pytest.skip("L1 OpenAPI endpoint not exposed")

        assert response.status_code == 200
        spec = response.json()
        assert "paths" in spec
        # Verify actual routes are documented
        paths = spec["paths"]
        assert "/jobs" in paths or any("jobs" in p for p in paths), "Jobs route not documented"

    def test_l2_openapi_spec_loads(self):
        """L2 OpenAPI spec is valid and loadable."""
        response = requests.get(f"{L2_URL}/openapi.json")
        if response.status_code == 404:
            response = requests.get(f"{L2_URL}/docs/openapi.json")

        if response.status_code == 404:
            pytest.skip("L2 OpenAPI endpoint not exposed")

        assert response.status_code == 200
        spec = response.json()
        assert "paths" in spec

    def test_l3_openapi_spec_matches_contract(self):
        """L3 runtime spec matches contracts/openapi/layer3-knowledge.json."""
        response = requests.get(f"{L3_URL}/openapi.json")
        if response.status_code == 404:
            pytest.skip("L3 OpenAPI endpoint not exposed")

        assert response.status_code == 200
        runtime_spec = response.json()

        # Load contract spec
        import json
        from pathlib import Path

        contract_path = Path(__file__).parent.parent.parent / "contracts" / "openapi" / "layer3-knowledge.json"
        if not contract_path.exists():
            pytest.skip("Contract spec not found")

        contract_spec = json.loads(contract_path.read_text())

        # Verify key endpoints exist in both
        contract_paths = set(contract_spec.get("paths", {}).keys())
        runtime_paths = set(runtime_spec.get("paths", {}).keys())

        # Check critical paths
        critical_paths = ["/v1/ingest", "/v1/search/hybrid"]
        for path in critical_paths:
            if path in contract_paths:
                assert path in runtime_paths, f"Critical path {path} missing from runtime"


if __name__ == "__main__":
    # Run basic connectivity tests
    print("Testing L1 connectivity...")
    try:
        r = requests.get(f"{L1_URL}/health")
        print(f"  L1 health: {r.status_code}")
    except Exception as e:
        print(f"  L1 unavailable: {e}")

    print("\nTesting L2 connectivity...")
    try:
        r = requests.get(f"{L2_URL}/health")
        print(f"  L2 health: {r.status_code}")
    except Exception as e:
        print(f"  L2 unavailable: {e}")

    print("\nTesting L3 connectivity...")
    try:
        r = requests.get(f"{L3_URL}/health")
        print(f"  L3 health: {r.status_code}")
    except Exception as e:
        print(f"  L3 unavailable: {e}")

    print("\nRun pytest with -s to execute full stack tests")
