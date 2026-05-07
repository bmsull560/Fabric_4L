from fastapi import HTTPException

import pytest
from types import SimpleNamespace

from src.api.common import audit as audit_helpers
from src.api.common.errors import normalize_exception, raise_normalized


def test_normalize_exception_passthrough_http_exception() -> None:
    original = HTTPException(status_code=422, detail="account_id is required for smoke-mode ROI validation")

    normalized = normalize_exception(
        original,
        status_code=500,
        detail="unused",
    )

    assert normalized is original
    assert normalized.status_code == 422
    assert normalized.detail == "account_id is required for smoke-mode ROI validation"


def test_normalize_exception_wraps_non_http_exception() -> None:
    normalized = normalize_exception(
        RuntimeError("boom"),
        status_code=500,
        detail="ROI analysis failed: boom",
    )

    assert isinstance(normalized, HTTPException)
    assert normalized.status_code == 500
    assert normalized.detail == "ROI analysis failed: boom"


def test_raise_normalized_preserves_http_exception_payload() -> None:
    original = HTTPException(status_code=400, detail="tenant_id is required")

    with pytest.raises(HTTPException) as raised:
        raise_normalized(original, status_code=500, detail="unused")

    assert raised.value.status_code == 400
    assert raised.value.detail == "tenant_id is required"


@pytest.mark.asyncio
async def test_emit_route_audit_delegates_to_emit_and_persist(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    async def _fake_emit_and_persist_audit(**kwargs):
        captured.update(kwargs)

    monkeypatch.setattr(audit_helpers, "emit_and_persist_audit", _fake_emit_and_persist_audit)

    ctx = SimpleNamespace(tenant_id="tenant-a", user_id="user-a", api_key_id=None)
    await audit_helpers.emit_route_audit(
        action="update",
        context=ctx,
        resource_type="Workflow",
        resource_id="wf-123",
        details={"archived_at": "2026-05-07T00:00:00Z"},
    )

    assert captured["action"] == "update"
    assert captured["context"] is ctx
    assert captured["resource_type"] == "Workflow"
    assert captured["resource_id"] == "wf-123"
    assert captured["details"] == {"archived_at": "2026-05-07T00:00:00Z"}
