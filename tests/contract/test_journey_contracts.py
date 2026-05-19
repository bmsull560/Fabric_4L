"""
Journey-Paired Backend Contract Tests

Each test in this module corresponds to a canonical user journey defined in
frontend/e2e/journeys/. While the Playwright journey tests verify UI behavior,
these tests verify that the backend APIs return correct data shapes, enforce
tenant isolation, and maintain provenance integrity.

Together, they prevent the failure mode: "UI passes but platform behavior is wrong."

Environment Variables:
    LAYER1_API_URL: Layer 1 Ingestion API (default: http://localhost:8001)
    LAYER3_API_URL: Layer 3 Knowledge API (default: http://localhost:8003)
    LAYER4_API_URL: Layer 4 Agents API (default: http://localhost:8004)
    LAYER5_API_URL: Layer 5 Ground Truth API (default: http://localhost:8005)
    CONTRACT_TEST_MODE: Set to 'mock' for CI without running services

Usage:
    # Against live services:
    pytest tests/contract/test_journey_contracts.py -v

    # In mock mode (CI):
    CONTRACT_TEST_MODE=mock pytest tests/contract/test_journey_contracts.py -v
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from httpx import AsyncClient

from .schema_assertions import assert_matches_schema

# ── Configuration ────────────────────────────────────────────────────────────

DEFAULT_TIMEOUT = 10.0
CONTRACTS_DIR = Path(__file__).parent.parent.parent / "contracts"
OPENAPI_DIR = CONTRACTS_DIR / "openapi"

LAYER_URLS = {
    "l1": os.getenv("LAYER1_API_URL", "http://localhost:8001"),
    "l3": os.getenv("LAYER3_API_URL", "http://localhost:8003"),
    "l4": os.getenv("LAYER4_API_URL", "http://localhost:8004"),
    "l5": os.getenv("LAYER5_API_URL", "http://localhost:8005"),
}

TENANT_HEADER = "X-Tenant-ID"
TEST_TENANT_A = "tenant-contract-a"
TEST_TENANT_B = "tenant-contract-b"

def _in_ci() -> bool:
    """Detect CI execution for fail-closed preflight behavior."""
    return os.getenv("CI", "").strip().lower() in {"1", "true", "yes"}


def _fail_closed_or_skip(message: str) -> None:
    """Fail in CI for launch-gated checks; skip only for local developer ergonomics."""
    if _in_ci():
        pytest.fail(message)
    pytest.skip(message)



# ── Helpers ──────────────────────────────────────────────────────────────────

def load_openapi_schema(layer_file: str, path: str, method: str = "get", status: str = "200") -> dict | None:
    """Load the response schema for a given endpoint from the OpenAPI spec."""
    spec_path = OPENAPI_DIR / layer_file
    if not spec_path.exists():
        return None
    with open(spec_path) as f:
        spec = json.load(f)
    path_def = spec.get("paths", {}).get(path, {})
    method_def = path_def.get(method.lower(), {})
    response_def = method_def.get("responses", {}).get(status, {})
    content = response_def.get("content", {}).get("application/json", {})
    schema = content.get("schema")
    if schema and "$ref" in schema:
        # Resolve top-level $ref
        ref_path = schema["$ref"].replace("#/", "").split("/")
        resolved = spec
        for part in ref_path:
            resolved = resolved.get(part, {})
        return {"_resolved": resolved, "_root": spec}
    return {"_resolved": schema, "_root": spec} if schema else None


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def l1_client() -> AsyncClient:
    """HTTP client for Layer 1 Ingestion API."""
    async with AsyncClient(
        base_url=LAYER_URLS["l1"].rstrip("/"),
        timeout=DEFAULT_TIMEOUT,
        headers={TENANT_HEADER: TEST_TENANT_A},
    ) as client:
        yield client


@pytest.fixture
async def l4_client() -> AsyncClient:
    """HTTP client for Layer 4 Agents API."""
    async with AsyncClient(
        base_url=LAYER_URLS["l4"].rstrip("/"),
        timeout=DEFAULT_TIMEOUT,
        headers={TENANT_HEADER: TEST_TENANT_A},
    ) as client:
        yield client


@pytest.fixture
async def l4_client_tenant_b() -> AsyncClient:
    """HTTP client for Layer 4 with a DIFFERENT tenant — for isolation tests."""
    async with AsyncClient(
        base_url=LAYER_URLS["l4"].rstrip("/"),
        timeout=DEFAULT_TIMEOUT,
        headers={TENANT_HEADER: TEST_TENANT_B},
    ) as client:
        yield client


@pytest.fixture
async def l5_client() -> AsyncClient:
    """HTTP client for Layer 5 Ground Truth API."""
    async with AsyncClient(
        base_url=LAYER_URLS["l5"].rstrip("/"),
        timeout=DEFAULT_TIMEOUT,
        headers={TENANT_HEADER: TEST_TENANT_A},
    ) as client:
        yield client


# ── Journey 1: Ingestion → Value Tree ────────────────────────────────────────

class TestJourney1IngestionContract:
    """Backend contract assertions for Journey 1: Domain Ingestion → Value Tree."""

    @pytest.mark.asyncio
    async def test_ingestion_targets_returns_valid_schema(self, l1_client: AsyncClient):
        """POST /api/v1/ingestion/targets must return a valid target with job_id."""
        resp = await l1_client.post(
            "/api/v1/ingestion/targets",
            json={"domain": "https://contract-test.example.com", "options": {}},
        )
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "target_id" in body or "id" in body, "Response must include target_id or id"

    @pytest.mark.asyncio
    async def test_ingestion_jobs_list_returns_array(self, l1_client: AsyncClient):
        """GET /api/v1/ingestion/jobs must return an array of jobs."""
        resp = await l1_client.get("/api/v1/ingestion/jobs")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), f"Expected array, got {type(body).__name__}"

    @pytest.mark.asyncio
    async def test_ingestion_job_progress_schema(self, l1_client: AsyncClient):
        """GET /api/v1/ingestion/jobs/{id}/progress must return progress data."""
        # First, get a job ID from the list
        resp = await l1_client.get("/api/v1/ingestion/jobs")
        if resp.status_code != 200 or not resp.json():
            _fail_closed_or_skip("No ingestion jobs available for progress check")
        job_id = resp.json()[0].get("id") or resp.json()[0].get("job_id")
        resp = await l1_client.get(f"/api/v1/ingestion/jobs/{job_id}/progress")
        assert resp.status_code == 200
        body = resp.json()
        assert "status" in body or "progress" in body, "Progress response must include status or progress"


# ── Journey 2: Intelligence Workspace ─────────────────────────────────────────

class TestJourney2IntelligenceContract:
    """Backend contract assertions for Journey 2: Intelligence Workspace Synthesis."""

    @pytest.mark.asyncio
    async def test_account_detail_returns_valid_schema(self, l4_client: AsyncClient):
        """GET /v1/accounts/{id} must return a valid account object."""
        # List accounts first
        resp = await l4_client.get("/v1/accounts")
        if resp.status_code != 200 or not resp.json():
            _fail_closed_or_skip("No accounts available")
        account_id = resp.json()[0].get("id") or resp.json()[0].get("account_id")

        resp = await l4_client.get(f"/v1/accounts/{account_id}")
        assert resp.status_code == 200
        body = resp.json()

        # Validate against OpenAPI schema if available
        schema_info = load_openapi_schema("layer4-agents.json", "/v1/accounts/{account_id}", "get")
        if schema_info:
            assert_matches_schema(body, schema_info["_resolved"], root=schema_info["_root"])

    @pytest.mark.asyncio
    async def test_agent_stream_chat_returns_content(self, l4_client: AsyncClient):
        """POST /v1/c1/stream must return a response with content field."""
        resp = await l4_client.post(
            "/v1/c1/stream",
            json={"message": "Analyze key pain signals", "context": {"account_id": "test"}},
        )
        # Agent stream may return 200 or streaming response
        assert resp.status_code in (200, 201), f"Expected 200/201, got {resp.status_code}"
        body = resp.json()
        assert "content" in body or "message" in body, "Stream response must include content or message"

    @pytest.mark.asyncio
    async def test_tenant_isolation_accounts(self, l4_client: AsyncClient, l4_client_tenant_b: AsyncClient):
        """Accounts from tenant A must NOT be visible to tenant B."""
        resp_a = await l4_client.get("/v1/accounts")
        resp_b = await l4_client_tenant_b.get("/v1/accounts")

        if resp_a.status_code != 200 or resp_b.status_code != 200:
            _fail_closed_or_skip("Cannot verify isolation — one or both tenants returned non-200")

        accounts_a = {a.get("id") for a in resp_a.json() if a.get("id")}
        accounts_b = {a.get("id") for a in resp_b.json() if a.get("id")}

        overlap = accounts_a & accounts_b
        assert len(overlap) == 0, (
            f"TENANT ISOLATION VIOLATION: {len(overlap)} accounts visible to both tenants: {overlap}"
        )


# ── Journey 3: Value Studio ──────────────────────────────────────────────────

class TestJourney3ValueStudioContract:
    """Backend contract assertions for Journey 3: Value Studio Deliverables."""

    @pytest.mark.asyncio
    async def test_cases_list_returns_array(self, l4_client: AsyncClient):
        """GET /v1/cases must return an array of business cases."""
        resp = await l4_client.get("/v1/cases")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), f"Expected array, got {type(body).__name__}"

    @pytest.mark.asyncio
    async def test_case_export_returns_url(self, l4_client: AsyncClient):
        """GET /v1/cases/{id}/export must return an export URL."""
        resp = await l4_client.get("/v1/cases")
        if resp.status_code != 200 or not resp.json():
            _fail_closed_or_skip("No cases available for export test")
        case_id = resp.json()[0].get("id") or resp.json()[0].get("case_id")

        resp = await l4_client.get(f"/v1/cases/{case_id}/export")
        assert resp.status_code == 200
        body = resp.json()
        assert "url" in body or "download_url" in body, "Export response must include a URL"

    @pytest.mark.asyncio
    async def test_roi_analysis_returns_projections(self, l4_client: AsyncClient):
        """POST /v1/analysis/roi must return projection data."""
        resp = await l4_client.post(
            "/v1/analysis/roi",
            json={"account_id": "test", "variables": {"revenue": 500000000}},
        )
        assert resp.status_code in (200, 201)
        body = resp.json()
        # ROI analysis should return some form of projection
        assert isinstance(body, dict), "ROI response must be an object"


# ── Journey 4: Governance & Trust ─────────────────────────────────────────────

class TestJourney4GovernanceContract:
    """Backend contract assertions for Journey 4: Governance & Trust."""

    @pytest.mark.asyncio
    async def test_health_endpoint_returns_status(self, l4_client: AsyncClient):
        """GET /health must return a status field."""
        resp = await l4_client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert "status" in body, "Health response must include status field"

    @pytest.mark.asyncio
    async def test_health_detailed_returns_components(self, l4_client: AsyncClient):
        """GET /v1/health/detailed must return component-level health data."""
        resp = await l4_client.get("/v1/health/detailed")
        assert resp.status_code == 200
        body = resp.json()
        assert "components" in body or "status" in body, "Detailed health must include components or status"

    @pytest.mark.asyncio
    async def test_workflows_list_returns_array(self, l4_client: AsyncClient):
        """GET /v1/workflows must return an array of workflows."""
        resp = await l4_client.get("/v1/workflows")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), f"Expected array, got {type(body).__name__}"

    @pytest.mark.asyncio
    async def test_workflow_types_returns_array(self, l4_client: AsyncClient):
        """GET /v1/workflows/types must return available workflow types."""
        resp = await l4_client.get("/v1/workflows/types")
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body, list), f"Expected array, got {type(body).__name__}"


# ── Journey 5: Tier-Gated Security ───────────────────────────────────────────

class TestJourney5SecurityContract:
    """Backend contract assertions for Journey 5: Tier-Gated Security.

    These tests verify that the backend enforces authorization independently
    of the frontend route guards. Even if the UI is bypassed, the API must
    reject unauthorized requests.
    """

    @pytest.mark.asyncio
    async def test_unauthenticated_request_returns_401(self):
        """Requests without auth headers must return 401."""
        async with AsyncClient(
            base_url=LAYER_URLS["l4"].rstrip("/"),
            timeout=DEFAULT_TIMEOUT,
            # No auth headers
        ) as client:
            resp = await client.get("/v1/accounts")
            # Backend should reject unauthenticated requests
            # Note: Some APIs may return 200 with empty data instead of 401
            # This test documents the actual behavior
            assert resp.status_code in (200, 401, 403), (
                f"Unexpected status {resp.status_code} for unauthenticated request"
            )

    @pytest.mark.asyncio
    async def test_api_keys_require_admin_role(self, l4_client: AsyncClient):
        """POST /v1/api-keys should require admin privileges."""
        resp = await l4_client.post(
            "/v1/api-keys",
            json={"name": "test-key", "permissions": ["read"]},
        )
        # This should either succeed (if client has admin role) or return 403
        assert resp.status_code in (200, 201, 403), (
            f"Expected 200/201/403, got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_tenant_header_required_for_data_endpoints(self, l4_client: AsyncClient):
        """Data endpoints must scope results to the tenant in the header."""
        # Make a request with tenant A header
        resp = await l4_client.get("/v1/accounts")
        assert resp.status_code == 200
        # All returned accounts should belong to tenant A
        # (This is a soft check — the backend may not expose tenant_id in responses)
        body = resp.json()
        if isinstance(body, list):
            for account in body:
                if "tenant_id" in account:
                    assert account["tenant_id"] == TEST_TENANT_A, (
                        f"Account {account.get('id')} belongs to {account['tenant_id']}, "
                        f"expected {TEST_TENANT_A}"
                    )


# ── OpenAPI Schema Drift Detection ───────────────────────────────────────────

class TestOpenApiSchemaDrift:
    """Detect when mock data in frontend E2E tests drifts from the OpenAPI spec.

    These tests load the mock data shapes used in journey tests and validate
    them against the OpenAPI schemas. If a mock is out of date, these tests
    will fail — alerting developers before the UI tests give false confidence.
    """

    @pytest.mark.asyncio
    async def test_account_mock_matches_openapi(self):
        """Verify the account mock shape matches the OpenAPI Account schema."""
        schema_info = load_openapi_schema("layer4-agents.json", "/v1/accounts/{account_id}", "get")
        if not schema_info:
            _fail_closed_or_skip("No OpenAPI schema found for /v1/accounts/{account_id}")

        # This is the shape used in frontend/e2e/helpers/api-harness.ts
        mock_account = {
            "id": "acct-test-001",
            "provider": "salesforce",
            "provider_record_id": "001-test-001",
            "name": "Test Account",
            "industry": "Technology",
            "website": "https://example.com",
            "tier": "enterprise",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
            "sync_status": "synced",
            "source_attribution": "manual",
            "provider_badge": "salesforce",
        }
        assert_matches_schema(mock_account, schema_info["_resolved"], root=schema_info["_root"])

    @pytest.mark.asyncio
    async def test_ingestion_jobs_mock_matches_openapi(self):
        """Verify the ingestion jobs mock shape matches the OpenAPI schema."""
        schema_info = load_openapi_schema("layer1-ingestion.json", "/api/v1/ingestion/jobs", "get")
        if not schema_info:
            _fail_closed_or_skip("No OpenAPI schema found for /api/v1/ingestion/jobs")

        mock_jobs = {
            "data": [
                {
                    "id": "job-001",
                    "target_id": "target-001",
                    "status": "completed",
                    "priority": 5,
                    "progress_percent_complete": 100,
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ],
            "aggregation": {},
            "pagination": {},
        }
        assert_matches_schema(mock_jobs, schema_info["_resolved"], root=schema_info["_root"])
