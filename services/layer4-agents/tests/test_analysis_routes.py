"""Targeted tests for analysis routes executor integration."""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from value_fabric.layer4.api.routes import analysis
from value_fabric.layer4.config.settings import settings


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
# These endpoints fail closed with 501 until a real persisted storage
# integration replaces the previous in-memory stub (H-01).
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_get_workspace_tab_returns_501(analysis_app: FastAPI) -> None:
    """GET /cases/{case_id}/workspace/{tab_key} must fail closed with 501."""
    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext
        return RequestContext(
            tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
            user_id="test-user",
        )

    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated

    test_case_id = "test-case-456"

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.get(f"/v1/cases/{test_case_id}/workspace/signals")
        assert response.status_code == 501, f"Expected 501, got {response.status_code}: {response.text}"
        detail = response.json()["detail"]
        assert "persisted storage integration" in detail


@pytest.mark.asyncio
async def test_get_workspace_tab_invalid_tab_key(analysis_app: FastAPI) -> None:
    """GET /cases/{case_id}/workspace/{tab_key} should reject invalid tab keys before 501."""
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
async def test_get_workspace_tab_all_valid_tabs_return_501(analysis_app: FastAPI) -> None:
    """All valid workspace tab keys must return 501 until persistence is implemented."""
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
            assert response.status_code == 501, f"Tab '{tab}' should return 501, got {response.status_code}"


@pytest.mark.asyncio
async def test_update_workspace_tab_returns_501(analysis_app: FastAPI) -> None:
    """PUT /cases/{case_id}/workspace/{tab_key} must fail closed with 501."""
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
        response = await client.put(
            f"/v1/cases/{test_case_id}/workspace/signals",
            json={"signals": test_signals}
        )
        assert response.status_code == 501, f"Expected 501, got {response.status_code}: {response.text}"
        detail = response.json()["detail"]
        assert "persisted storage integration" in detail


@pytest.mark.asyncio
async def test_generate_workspace_intelligence_fails_closed_without_production_workflow(
    analysis_app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /workspace/generate must not return fabricated sample intelligence."""

    tenant_id = UUID("12345678-1234-1234-1234-123456789abc")

    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext

        return RequestContext(tenant_id=tenant_id, user_id="analyst-user")

    class FakeDb:
        async def get(self, model: Any, key: str) -> Any:
            return SimpleNamespace(id=key, account_id="account-1")

    class FakeAccountService:
        def __init__(self, db: Any) -> None:
            self.db = db

        async def get_account(self, account_id: str, tenant_id: str | None = None) -> Any:
            return SimpleNamespace(id=account_id, name="Acme")

    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated
    analysis_app.dependency_overrides[analysis.get_db_from_context] = lambda: FakeDb()
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: FakeExecutor(execute_response=None)
    monkeypatch.setattr(analysis, "AccountService", FakeAccountService)

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.post("/v1/cases/case-501/workspace/generate")

    assert response.status_code == 501
    detail = response.json()["detail"]
    assert "production AI workflow" in detail
    assert "sample" in detail
