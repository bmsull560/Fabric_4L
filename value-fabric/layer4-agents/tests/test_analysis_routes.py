"""Targeted tests for analysis routes executor integration."""

from dataclasses import dataclass, field
from types import SimpleNamespace
from typing import Any

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
