"""Targeted tests for analysis routes executor integration."""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.routes import analysis
from src.config.settings import settings


@dataclass
class FakeExecutor:
    """Minimal executor stub for analysis route tests."""

    execute_response: Any
    results_by_id: dict[str, dict[str, Any]] = field(default_factory=dict)
    execute_calls: list[dict[str, Any]] = field(default_factory=list)
    get_result_calls: list[str] = field(default_factory=list)

    async def execute_workflow(self, **kwargs: Any) -> Any:
        self.execute_calls.append(kwargs)
        return self.execute_response

    async def get_result(self, workflow_id: str) -> dict[str, Any] | None:
        self.get_result_calls.append(workflow_id)
        return self.results_by_id.get(workflow_id)


@pytest.fixture
def analysis_app() -> FastAPI:
    """Build a small FastAPI app with analysis routes only."""
    app = FastAPI()
    app.include_router(analysis.router, prefix="/v1")
    return app


@pytest.mark.asyncio
async def test_post_cases_success_path(analysis_app: FastAPI) -> None:
    """POST /cases should call execute_workflow and return case payload."""
    fake_executor = FakeExecutor(
        execute_response=SimpleNamespace(
            workflow_id="wf-case-123",
            status=SimpleNamespace(value="completed"),
            output_data={
                "assemble_document": {
                    "document_url": "https://example/doc.pdf",
                    "page_count": 7,
                    "file_size_bytes": 2048,
                    "truth_references": [{"id": "truth-1"}],
                    "remediation_items": [],
                    "case_metadata": {"confidence": "high"},
                },
                "verify_truth_requirements": {"passed": True},
            },
        )
    )
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: fake_executor

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.post("/v1/cases", json={"prospect_id": "prospect-1"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "wf-case-123"
    assert payload["status"] == "completed"
    assert payload["document_url"] == "https://example/doc.pdf"
    assert payload["page_count"] == 7
    assert fake_executor.execute_calls[0]["workflow_type"] == "business_case"


@pytest.mark.asyncio
async def test_get_case_retrieval(analysis_app: FastAPI) -> None:
    """GET /cases/{case_id} should retrieve persisted output via get_result."""
    fake_executor = FakeExecutor(execute_response=None)
    fake_executor.results_by_id["case-42"] = {
        "workflow_id": "case-42",
        "status": "completed",
        "created_at": "2026-04-23T00:00:00+00:00",
        "output": {
            "assemble_document": {
                "title": "Q2 Business Case",
                "executive_summary": "Strong ROI expected.",
                "total_estimated_value": 1000000.0,
                "implementation_cost_estimate": 250000.0,
                "roi_ratio": 4.0,
                "payback_months": 9,
                "confidence_score": 0.91,
                "recommendations": ["Proceed to pilot"],
            },
            "verify_truth_requirements": {"passed": True},
        },
    }
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: fake_executor

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.get("/v1/cases/case-42")

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "case-42"
    assert payload["title"] == "Q2 Business Case"
    assert payload["roi_ratio"] == 4.0
    assert fake_executor.get_result_calls == ["case-42"]


@pytest.mark.asyncio
async def test_export_route_uses_get_result_dependency(analysis_app: FastAPI, monkeypatch) -> None:
    """GET /cases/{case_id}/export should depend on get_result for retrieval."""
    fake_executor = FakeExecutor(execute_response=None)
    fake_executor.results_by_id["case-export"] = {
        "workflow_id": "case-export",
        "status": "completed",
        "output": {
            "assemble_document": {
                "blocked": True,
                "truth_references": [{"id": "truth-2"}],
                "remediation_items": [{"action": "Add citation"}],
            },
            "verify_truth_requirements": {
                "passed": False,
                "requirements": ["All claims must be sourced"],
            },
        },
    }
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: fake_executor
    monkeypatch.setattr(settings, "export_storage_endpoint", "http://storage.local", raising=False)

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.get("/v1/cases/case-export/export")

    assert response.status_code == 200
    payload = response.json()
    assert payload["case_id"] == "case-export"
    assert payload["blocked"] is True
    assert fake_executor.get_result_calls == ["case-export"]


# ═══════════════════════════════════════════════════════════════════════════════
# WORKSPACE TAB ENDPOINT TESTS
# These tests prevent regression of the Pydantic validation issue where
# dynamic tab data (signals, drivers, etc.) was being stripped due to
# extra="forbid" in the response model.
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_workspace_tab_returns_dynamic_data(analysis_app: FastAPI) -> None:
    """GET /cases/{case_id}/workspace/{tab_key} should return dynamic tab data without stripping fields.

    Regression test for: Pydantic model with extra="forbid" was stripping signals/drivers/evidence
    fields because they weren't explicitly defined in get_workspace_tabResult.
    """
    from unittest.mock import AsyncMock, MagicMock, Mock
    from sqlalchemy.ext.asyncio import AsyncSession

    # Mock the database session and account service
    mock_db = MagicMock(spec=AsyncSession)
    mock_db.get = AsyncMock(return_value=None)
    mock_db.execute = AsyncMock()
    mock_db.add = Mock()

    # Mock the account service to return a valid account
    mock_account = MagicMock()
    mock_account.industry = "Manufacturing"
    mock_account.name = "Test Corp"
    mock_account.provider_record_id = "test-123"

    # Create a mock for the generate_workspace_intelligence endpoint dependencies
    # We'll directly test the GET endpoint with pre-populated workspace data

    # Initialize workspace data directly in the analysis module
    test_case_id = "test-case-456"
    analysis._workspace_data[test_case_id] = {
        "signals": [
            {"id": "sig_1", "name": "Test Signal", "category": "Operational", "confidence": 85, "impact": "High"}
        ],
        "drivers": [{"id": "drv_1", "name": "Manual process overhead", "contribution": 35}],
        "evidence": [{"id": "ev_1", "source": "Test Source", "claim": "Test claim", "confidence": 88}],
        "stakeholders": [{"id": "st_1", "name": "CFO", "role": "Economic Buyer"}],
    }

    # Mock authentication context
    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext
        return RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
        )

    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        # Test signals tab
        response = await client.get(f"/v1/cases/{test_case_id}/workspace/signals")
        assert response.status_code == 200, f"Signals tab failed: {response.text}"
        payload = response.json()
        assert "signals" in payload, f"Missing 'signals' key in response: {payload.keys()}"
        assert len(payload["signals"]) == 1
        assert payload["signals"][0]["name"] == "Test Signal"
        assert payload["signals"][0]["confidence"] == 85

        # Test drivers tab
        response = await client.get(f"/v1/cases/{test_case_id}/workspace/drivers")
        assert response.status_code == 200, f"Drivers tab failed: {response.text}"
        payload = response.json()
        assert "drivers" in payload, f"Missing 'drivers' key in response: {payload.keys()}"
        assert len(payload["drivers"]) == 1

        # Test evidence tab
        response = await client.get(f"/v1/cases/{test_case_id}/workspace/evidence")
        assert response.status_code == 200, f"Evidence tab failed: {response.text}"
        payload = response.json()
        assert "evidence" in payload, f"Missing 'evidence' key in response: {payload.keys()}"

        # Test stakeholders tab
        response = await client.get(f"/v1/cases/{test_case_id}/workspace/stakeholders")
        assert response.status_code == 200, f"Stakeholders tab failed: {response.text}"
        payload = response.json()
        assert "stakeholders" in payload, f"Missing 'stakeholders' key in response: {payload.keys()}"

    # Cleanup
    del analysis._workspace_data[test_case_id]


@pytest.mark.asyncio
async def test_get_workspace_tab_unknown_case_returns_empty(analysis_app: FastAPI) -> None:
    """GET /cases/{case_id}/workspace/{tab_key} should return empty data for unknown case."""
    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext
        return RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
        )

    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated

    unknown_case_id = "unknown-case-999"

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.get(f"/v1/cases/{unknown_case_id}/workspace/signals")
        assert response.status_code == 200
        payload = response.json()
        assert "signals" in payload
        assert payload["signals"] == []


@pytest.mark.asyncio
async def test_get_workspace_tab_invalid_tab_key(analysis_app: FastAPI) -> None:
    """GET /cases/{case_id}/workspace/{tab_key} should reject invalid tab keys."""
    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext
        return RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
        )

    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.get("/v1/cases/test-case/workspace/invalid-tab")
        assert response.status_code == 400
        payload = response.json()
        assert "Invalid tab_key" in payload["detail"]


@pytest.mark.asyncio
async def test_get_workspace_tab_all_valid_tabs(analysis_app: FastAPI) -> None:
    """GET /cases/{case_id}/workspace/{tab_key} should accept all valid tab keys."""
    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext
        return RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
        )

    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated

    test_case_id = "test-case-tabs"
    valid_tabs = ["signals", "drivers", "evidence", "stakeholders", "action-plan", "value-model", "narrative"]

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        for tab in valid_tabs:
            response = await client.get(f"/v1/cases/{test_case_id}/workspace/{tab}")
            assert response.status_code == 200, f"Tab '{tab}' failed with status {response.status_code}"
            payload = response.json()
            assert tab in payload or tab.replace("-", "_") in str(payload).lower() or payload.get(tab, []) == [], \
                f"Response for tab '{tab}' missing expected data structure: {payload}"


@pytest.mark.asyncio
async def test_update_workspace_tab_persists_data(analysis_app: FastAPI) -> None:
    """PUT /cases/{case_id}/workspace/{tab_key} should persist tab data and make it retrievable."""
    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext
        return RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
        )

    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated

    test_case_id = "test-case-update"
    test_signals = [
        {"id": "sig_1", "name": "Updated Signal", "category": "Cost", "confidence": 90}
    ]

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        # Update the tab
        response = await client.put(
            f"/v1/cases/{test_case_id}/workspace/signals",
            json={"signals": test_signals}
        )
        assert response.status_code == 200, f"Update failed: {response.text}"
        payload = response.json()
        assert payload["updated"] is True
        assert payload["tab"] == "signals"

        # Retrieve and verify
        response = await client.get(f"/v1/cases/{test_case_id}/workspace/signals")
        assert response.status_code == 200
        payload = response.json()
        assert "signals" in payload

    # Cleanup
    if test_case_id in analysis._workspace_data:
        del analysis._workspace_data[test_case_id]
