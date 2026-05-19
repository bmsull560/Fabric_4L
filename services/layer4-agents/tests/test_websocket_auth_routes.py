"""Security-focused tests for WebSocket authentication (SEC-L3-012).

Sprint 3 removed query-parameter auth (?token= / ?auth=) entirely.
The ONLY accepted auth vector is the Sec-WebSocket-Protocol header.
These tests assert that:
  - Missing header → 1008 rejection
  - Malformed/invalid JWT in header → 1008 rejection
  - Legacy query-param signature is absent from the endpoint
  - Valid header path reaches the auth logic
"""

from __future__ import annotations

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from value_fabric.layer4.api.websocket.routes import (
    WebSocketAuthError,
    _extract_tenant_from_token,
    workflow_websocket,
)


# ---------------------------------------------------------------------------
# Verify the query-parameter has been removed from the endpoint signature
# ---------------------------------------------------------------------------


def test_workflow_websocket_has_no_token_query_param():
    """The 'token' query parameter must not exist on workflow_websocket (SEC-L3-012)."""
    sig = inspect.signature(workflow_websocket)
    assert "token" not in sig.parameters, (
        "Legacy 'token' query parameter still present in workflow_websocket. "
        "SEC-L3-012 requires its removal."
    )


def test_workflow_websocket_has_no_auth_query_param():
    """The 'auth' query parameter must not exist on workflow_websocket (SEC-L3-012)."""
    sig = inspect.signature(workflow_websocket)
    assert "auth" not in sig.parameters, (
        "Legacy 'auth' query parameter still present in workflow_websocket."
    )


# ---------------------------------------------------------------------------
# Missing / empty Sec-WebSocket-Protocol header → 1008
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workflow_websocket_rejects_missing_header(caplog):
    """No Sec-WebSocket-Protocol header → AUTH_TOKEN_MISSING → 1008."""
    websocket = MagicMock()
    websocket.headers = {}
    websocket.close = AsyncMock()

    await workflow_websocket(websocket=websocket, workflow_id="wf-1")

    websocket.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert "AUTH_TOKEN_MISSING" in caplog.text


@pytest.mark.asyncio
async def test_workflow_websocket_rejects_empty_protocol_header(caplog):
    """Empty Sec-WebSocket-Protocol header → AUTH_TOKEN_MISSING → 1008."""
    websocket = MagicMock()
    websocket.headers = {"sec-websocket-protocol": ""}
    websocket.close = AsyncMock()

    await workflow_websocket(websocket=websocket, workflow_id="wf-2")

    websocket.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert "AUTH_TOKEN_MISSING" in caplog.text


# ---------------------------------------------------------------------------
# Invalid JWT in header → 1008, no token leakage
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workflow_websocket_rejects_invalid_token_without_leaking_details(
    monkeypatch, caplog
):
    """Invalid JWT in header → 1008; raw token must not appear in logs."""
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

    await workflow_websocket(websocket=websocket, workflow_id="wf-3")

    websocket.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert raw_token not in caplog.text
    assert "secret.jwt.token" not in caplog.text
    assert "AUTH_TOKEN_DECODE_FAILED" in caplog.text


# ---------------------------------------------------------------------------
# _extract_tenant_from_token unit tests
# ---------------------------------------------------------------------------


def test_extract_tenant_from_token_maps_decode_exceptions_to_stable_code(
    monkeypatch, caplog
):
    """Unexpected decode exceptions must map to AUTH_TOKEN_DECODE_FAILED."""
    monkeypatch.setattr("value_fabric.layer4.api.websocket.routes.JWT_AVAILABLE", True)

    def _boom(_token: str):
        raise ValueError("sensitive parser message")

    monkeypatch.setattr("value_fabric.layer4.api.websocket.routes.decode_jwt", _boom)

    with pytest.raises(WebSocketAuthError) as exc_info:
        _extract_tenant_from_token("token-value")

    assert exc_info.value.code == "AUTH_TOKEN_DECODE_FAILED"
    assert "sensitive parser message" not in caplog.text


def test_extract_tenant_from_token_raises_on_none():
    """None token → AUTH_TOKEN_MISSING."""
    with pytest.raises(WebSocketAuthError) as exc_info:
        _extract_tenant_from_token(None)
    assert exc_info.value.code == "AUTH_TOKEN_MISSING"


def test_extract_tenant_from_token_raises_on_empty_string():
    """Empty string token → AUTH_TOKEN_MISSING."""
    with pytest.raises(WebSocketAuthError) as exc_info:
        _extract_tenant_from_token("   ")
    assert exc_info.value.code == "AUTH_TOKEN_MISSING"


def test_extract_tenant_from_token_raises_when_jwt_unavailable(monkeypatch):
    """JWT library unavailable → AUTH_JWT_UNAVAILABLE."""
    monkeypatch.setattr("value_fabric.layer4.api.websocket.routes.JWT_AVAILABLE", False)

    with pytest.raises(WebSocketAuthError) as exc_info:
        _extract_tenant_from_token("some.jwt.token")

    assert exc_info.value.code == "AUTH_JWT_UNAVAILABLE"


# ---------------------------------------------------------------------------
# Valid JWT success path — ws_manager.connect receives correct claims
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_workflow_websocket_valid_token_calls_connect_with_correct_claims(
    monkeypatch,
):
    """Valid token → ws_manager.connect called with extracted tenant_id and user_id."""
    websocket = MagicMock()
    websocket.headers = {"sec-websocket-protocol": "token,valid.jwt.token"}
    websocket.close = AsyncMock()
    websocket.receive_json = AsyncMock(
        side_effect=Exception("stop loop")  # exit the receive loop immediately
    )

    # Stub _extract_tenant_from_token to return known claims
    def _valid_token(token: str | None) -> tuple[str, str]:
        assert token == "valid.jwt.token"
        return ("tenant-abc", "user-xyz")

    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.routes._extract_tenant_from_token",
        _valid_token,
    )

    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    mock_manager.handle_client_message = AsyncMock()

    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.routes.get_ws_manager",
        lambda: mock_manager,
    )

    await workflow_websocket(
        websocket=websocket,
        workflow_id="wf-success",
        last_event_id="evt-001",
    )

    # Must NOT have closed with 1008
    websocket.close.assert_not_called()

    # Must have called connect with the correct extracted claims
    mock_manager.connect.assert_awaited_once_with(
        websocket,
        "wf-success",
        "evt-001",
        tenant_id="tenant-abc",
        user_id="user-xyz",
    )

    # Must have called disconnect in the finally block
    mock_manager.disconnect.assert_awaited_once_with(websocket, "wf-success")


@pytest.mark.asyncio
async def test_workflow_websocket_bare_subprotocol_name_rejected(caplog):
    """A bare subprotocol name (no 'token,' prefix) must be rejected with 1008."""
    websocket = MagicMock()
    # Single-part header that is NOT in "token,<jwt>" format
    websocket.headers = {"sec-websocket-protocol": "graphql-ws"}
    websocket.close = AsyncMock()

    await workflow_websocket(websocket=websocket, workflow_id="wf-bare")

    websocket.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert "AUTH_TOKEN_MISSING" in caplog.text
