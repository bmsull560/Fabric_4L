from pathlib import Path
from types import SimpleNamespace
from typing import Any
from uuid import UUID, uuid4
import sys

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

SERVICE_ROOT = Path(__file__).resolve().parents[1]
if str(SERVICE_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVICE_ROOT))
for module_name in list(sys.modules):
    if module_name == "src" or module_name.startswith("src."):
        sys.modules.pop(module_name, None)

from src.api.routes import analysis
from src.config.settings import settings


@pytest.fixture
def analysis_app() -> FastAPI:
    """Build a small FastAPI app with the Docker service-source analysis routes only."""
    app = FastAPI()
    app.include_router(analysis.router, prefix="/v1")
    return app


@pytest.mark.asyncio
async def test_smoke_mode_roi_returns_deterministic_response_without_executor(
    analysis_app: FastAPI,
    monkeypatch,
) -> None:
    """Explicit smoke-mode ROI calls should validate account ownership and avoid slow workflow execution."""
    tenant_id = UUID("12345678-1234-1234-1234-123456789abc")
    account_id = uuid4()

    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext

        return RequestContext(tenant_id=tenant_id, user_id="smoke-user")

    class RaisingExecutor:
        async def run(self, **kwargs: Any) -> Any:
            raise AssertionError("smoke-mode ROI must not invoke the workflow executor")

    class FakeAccountService:
        def __init__(self, db: Any) -> None:
            self.db = db

        async def get_account(self, requested_account_id: UUID, *, tenant_id: str | None = None) -> Any:
            assert requested_account_id == account_id
            assert tenant_id == str(tenant_id_context)
            return SimpleNamespace(id=account_id, provider_record_id="crm-account-1")

    tenant_id_context = tenant_id
    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: RaisingExecutor()
    analysis_app.dependency_overrides[analysis.get_db_from_context] = lambda: object()
    monkeypatch.setattr(analysis, "AccountService", FakeAccountService)

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.post(
            "/v1/analysis/roi",
            headers={"X-Validation-Mode": "smoke", "X-Validation-Run-ID": "route-test-1"},
            json={
                "account_id": str(account_id),
                "variables": {"annual_benefit": 500000, "implementation_cost": 125000},
                "formula_id": "formula-smoke",
            },
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["prospect_id"] == str(account_id)
    assert payload["aggregated_roi"]["mode"] == "smoke"
    assert payload["aggregated_roi"]["requires_full_analysis"] is True
    assert payload["aggregated_roi"]["trace_id"] == "route-test-1"
    assert payload["aggregated_roi"]["account_id"] == str(account_id)


@pytest.mark.asyncio
async def test_smoke_mode_business_case_persists_draft_and_skips_executor(
    analysis_app: FastAPI,
    monkeypatch,
) -> None:
    """Explicit smoke-mode case creation should persist a draft record without running the slow generator."""
    tenant_id = UUID("12345678-1234-1234-1234-123456789abc")
    account_id = uuid4()
    persisted: dict[str, Any] = {}

    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext

        return RequestContext(tenant_id=tenant_id, user_id="smoke-user")

    class RaisingExecutor:
        async def run(self, **kwargs: Any) -> Any:
            raise AssertionError("smoke-mode case creation must not invoke the workflow executor")

    class FakeAccountService:
        def __init__(self, db: Any) -> None:
            self.db = db

        async def get_account(self, requested_account_id: UUID, *, tenant_id: str | None = None) -> Any:
            assert requested_account_id == account_id
            assert tenant_id == str(tenant_id_context)
            return SimpleNamespace(id=account_id, provider_record_id="crm-account-1")

    class FakeBusinessCaseService:
        def __init__(self, db: Any) -> None:
            self.db = db

        async def upsert_case_record(self, **kwargs: Any) -> Any:
            persisted.update(kwargs)
            return SimpleNamespace(**kwargs)

    tenant_id_context = tenant_id
    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: RaisingExecutor()
    analysis_app.dependency_overrides[analysis.get_db_from_context] = lambda: object()
    monkeypatch.setattr(analysis, "AccountService", FakeAccountService)
    monkeypatch.setattr(analysis, "BusinessCaseService", FakeBusinessCaseService)

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.post(
            "/v1/cases",
            headers={"X-Fabric-Smoke-Test": "true", "X-Validation-Run-ID": "route-test-2"},
            json={"account_id": str(account_id), "custom_inputs": {"mode": "smoke"}},
        )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["status"] == "draft"
    assert payload["case_metadata"]["mode"] == "smoke"
    assert payload["case_metadata"]["export_allowed"] is False
    assert payload["case_metadata"]["requires_full_generation"] is True
    assert persisted["case_id"] == payload["case_id"]
    assert persisted["workflow_id"] == payload["case_id"]
    assert persisted["account_id"] == account_id
    assert persisted["status"] == "draft"


@pytest.mark.asyncio
async def test_normal_business_case_request_preserves_full_workflow(
    analysis_app: FastAPI,
    monkeypatch,
) -> None:
    """Without explicit smoke headers, case creation must still run the full workflow executor."""
    tenant_id = UUID("12345678-1234-1234-1234-123456789abc")
    account_id = uuid4()
    run_calls: list[dict[str, Any]] = []

    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext

        return RequestContext(tenant_id=tenant_id, user_id="workflow-user")

    class FakeExecutor:
        async def run(self, **kwargs: Any) -> Any:
            run_calls.append(kwargs)
            return SimpleNamespace(
                workflow_id="wf-full-123",
                status=SimpleNamespace(value="completed"),
                output_data={
                    "assemble_document": {
                        "document_url": "https://example/full.pdf",
                        "page_count": 3,
                        "file_size_bytes": 1024,
                        "case_metadata": {},
                    },
                    "verify_truth_requirements": {"passed": True},
                    "generate_sdes": {},
                },
            )

    class FakeAccountService:
        def __init__(self, db: Any) -> None:
            self.db = db

        async def get_account(self, requested_account_id: UUID, *, tenant_id: str | None = None) -> Any:
            assert requested_account_id == account_id
            assert tenant_id == str(tenant_id_context)
            return SimpleNamespace(id=account_id, provider_record_id="crm-account-1")

    class FakeBusinessCaseService:
        def __init__(self, db: Any) -> None:
            self.db = db

        async def upsert_case_record(self, **kwargs: Any) -> Any:
            return SimpleNamespace(**kwargs)

    tenant_id_context = tenant_id
    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: FakeExecutor()
    analysis_app.dependency_overrides[analysis.get_db_from_context] = lambda: object()
    monkeypatch.setattr(analysis, "AccountService", FakeAccountService)
    monkeypatch.setattr(analysis, "BusinessCaseService", FakeBusinessCaseService)

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.post("/v1/cases", json={"account_id": str(account_id)})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["case_id"] == "wf-full-123"
    assert payload["status"] == "completed"
    assert payload["document_url"] == "https://example/full.pdf"
    assert len(run_calls) == 1
    assert run_calls[0]["workflow_type"] == "business_case"
    assert run_calls[0]["tenant_id"] == str(tenant_id)


@pytest.mark.asyncio
async def test_export_gate_rejects_smoke_draft_record_without_executor_result(
    analysis_app: FastAPI,
    monkeypatch,
) -> None:
    """Draft records created without document bytes must be blocked by the export gate."""
    tenant_id = UUID("12345678-1234-1234-1234-123456789abc")
    account_id = uuid4()
    case_id = "smoke-case-draft"

    async def mock_require_authenticated():
        from value_fabric.shared.identity.context import RequestContext

        return RequestContext(tenant_id=tenant_id, user_id="smoke-user")

    class FakeExecutor:
        async def get_result(self, requested_case_id: str) -> Any:
            assert requested_case_id == case_id
            return None

    class FakeDB:
        async def get(self, model: Any, key: str) -> Any:
            assert key == case_id
            return SimpleNamespace(account_id=account_id)

    class FakeAccountService:
        def __init__(self, db: Any) -> None:
            self.db = db

        async def get_account(self, requested_account_id: UUID, *, tenant_id: str | None = None) -> Any:
            assert requested_account_id == account_id
            assert tenant_id == str(tenant_id_context)
            return SimpleNamespace(id=account_id, provider_record_id="crm-account-1")

    tenant_id_context = tenant_id
    analysis_app.dependency_overrides[analysis.require_authenticated] = mock_require_authenticated
    analysis_app.dependency_overrides[analysis.get_executor] = lambda: FakeExecutor()
    analysis_app.dependency_overrides[analysis.get_db_from_context] = lambda: FakeDB()
    monkeypatch.setattr(analysis, "AccountService", FakeAccountService)
    monkeypatch.setattr(settings, "export_storage_endpoint", None, raising=False)

    async with AsyncClient(transport=ASGITransport(app=analysis_app), base_url="http://test") as client:
        response = await client.get(f"/v1/cases/{case_id}/export")

    assert response.status_code == 409, response.text
    assert "draft" in response.text.lower() or "document bytes" in response.text.lower()
