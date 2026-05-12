"""Security-focused tests for websocket auth error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from value_fabric.layer4.api.websocket.routes import (
    WebSocketAuthError,
    _extract_tenant_from_token,
    workflow_websocket,
)


@pytest.mark.asyncio
async def test_workflow_websocket_rejects_query_token_with_generic_reason(caplog):
    websocket = MagicMock()
    websocket.headers = {}
    websocket.close = AsyncMock()

    await workflow_websocket(websocket=websocket, workflow_id="wf-qp", token="secret.query.token")

    websocket.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert "AUTH_QUERY_TOKEN_FORBIDDEN" in caplog.text
    assert "secret.query.token" not in caplog.text


@pytest.mark.asyncio
async def test_workflow_websocket_rejects_missing_token_with_generic_reason(caplog):
    websocket = MagicMock()
    websocket.headers = {}
    websocket.close = AsyncMock()

    await workflow_websocket(websocket=websocket, workflow_id="wf-1", token=None)

    websocket.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert "Authentication failed" in caplog.text
    assert "AUTH_TOKEN_MISSING" in caplog.text


@pytest.mark.asyncio
async def test_workflow_websocket_rejects_invalid_token_without_leaking_details(monkeypatch, caplog):
    websocket = MagicMock()
    raw_token = "token,secret.jwt.token"
    websocket.headers = {"sec-websocket-protocol": raw_token}
    websocket.close = AsyncMock()

    def _raise_decode(_token: str | None):
        raise WebSocketAuthError("AUTH_TOKEN_DECODE_FAILED")

    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.routes._extract_tenant_from_token",
        _raise_decode,
    )

    await workflow_websocket(websocket=websocket, workflow_id="wf-2", token=None)

    websocket.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert raw_token not in caplog.text
    assert "secret.jwt.token" not in caplog.text
    assert "AUTH_TOKEN_DECODE_FAILED" in caplog.text


def test_extract_tenant_from_token_maps_decode_exceptions_to_stable_code(monkeypatch, caplog):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.routes.JWT_AVAILABLE", True)

    def _boom(_token: str):
        raise ValueError("sensitive parser message")

    monkeypatch.setattr("value_fabric.layer4.api.websocket.routes.decode_jwt", _boom)

    with pytest.raises(WebSocketAuthError) as exc_info:
        _extract_tenant_from_token("token-value")

    assert exc_info.value.code == "AUTH_TOKEN_DECODE_FAILED"
    assert "sensitive parser message" not in caplog.text
