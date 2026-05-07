from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from value_fabric.shared.identity.context import RequestContext

from src.api.routes import signals


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(signals.router, prefix="/v1")
    app.dependency_overrides[signals.require_authenticated] = lambda: RequestContext(
        tenant_id=UUID("12345678-1234-1234-1234-123456789abc"),
        user_id="reviewer-123",
    )
    return app


@pytest.mark.asyncio
async def test_signal_review_approve_reject_roundtrip_and_persistence_reload(app: FastAPI, monkeypatch: pytest.MonkeyPatch) -> None:
    persisted: dict[str, dict] = {}

    class FakeLayer3Client:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def review_signal(self, signal_id: str, account_id: str, review_status: str, reviewer_id: str, decision_note=None, tenant_id=None):
            persisted[signal_id] = {
                "signal_id": signal_id,
                "account_id": account_id,
                "review_status": review_status,
                "reviewed_by": reviewer_id,
                "reviewed_at": "2026-05-07T00:00:00Z",
                "decision_note": decision_note,
                "tenant_id": str(tenant_id),
            }
            return persisted[signal_id]

    monkeypatch.setattr("src.integration.layer3_client.Layer3Client", FakeLayer3Client)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        approve = await client.patch("/v1/signals/sig-1/review", json={"account_id": "acct-1", "review_status": "approved"})
        assert approve.status_code == 200
        assert approve.json()["review_status"] == "approved"

        reject = await client.patch("/v1/signals/sig-1/review", json={"account_id": "acct-1", "review_status": "rejected", "decision_note": "insufficient evidence"})
        assert reject.status_code == 200
        assert reject.json()["review_status"] == "rejected"
        assert persisted["sig-1"]["decision_note"] == "insufficient evidence"
