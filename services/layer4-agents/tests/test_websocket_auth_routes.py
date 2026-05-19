"""Security-focused tests for WebSocket auth (ARCH-L4-008).

Covers:
- Canonical Sec-WebSocket-Protocol bearer format
- Legacy query-parameter deprecation path
- Fail-closed behaviour on all auth error codes
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.websockets import WebSocketDisconnect

from value_fabric.layer4.api.websocket.auth import (
    WebSocketAuthError,
    decode_ws_token,
    extract_token_from_protocol_header,
    extract_token_from_query_param,
)
from value_fabric.layer4.api.websocket.routes import workflow_websocket


# ---------------------------------------------------------------------------
# extract_token_from_protocol_header
# ---------------------------------------------------------------------------


def test_canonical_header_extracts_token():
    header = "base64url.bearer.authorization, eyJhbGciOiJSUzI1NiJ9.payload.sig"
    token = extract_token_from_protocol_header(header)
    assert token == "eyJhbGciOiJSUzI1NiJ9.payload.sig"


def test_canonical_header_case_insensitive():
    header = "Base64url.Bearer.Authorization, mytoken"
    token = extract_token_from_protocol_header(header)
    assert token == "mytoken"


def test_canonical_header_missing_returns_none():
    assert extract_token_from_protocol_header("") is None
    assert extract_token_from_protocol_header("some-other-protocol") is None


def test_canonical_header_wrong_subprotocol_returns_none():
    # Old "token,<jwt>" format is not the canonical format
    assert extract_token_from_protocol_header("token, myjwt") is None


# ---------------------------------------------------------------------------
# extract_token_from_query_param (legacy / deprecation path)
# ---------------------------------------------------------------------------


def test_legacy_query_param_emits_deprecation_warning(caplog):
    import logging

    with caplog.at_level(logging.WARNING):
        token = extract_token_from_query_param("legacy.jwt.token", correlation_id="cid-123")

    assert token == "legacy.jwt.token"
    assert "DEPRECATION" in caplog.text
    assert "SEC-L3-012" in caplog.text
    assert "cid-123" in caplog.text
    # Token value must NOT appear in logs
    assert "legacy.jwt.token" not in caplog.text


def test_legacy_query_param_none_returns_none():
    assert extract_token_from_query_param(None) is None
    assert extract_token_from_query_param("") is None
    assert extract_token_from_query_param("   ") is None


# ---------------------------------------------------------------------------
# decode_ws_token
# ---------------------------------------------------------------------------


def test_decode_ws_token_missing_raises():
    with pytest.raises(WebSocketAuthError) as exc:
        decode_ws_token(None)
    assert exc.value.code == "AUTH_TOKEN_MISSING"


def test_decode_ws_token_jwt_unavailable_raises(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", False)
    with pytest.raises(WebSocketAuthError) as exc:
        decode_ws_token("some.token")
    assert exc.value.code == "AUTH_JWT_UNAVAILABLE"


def test_decode_ws_token_maps_decode_exceptions_to_stable_code(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)

    def _boom(_token):
        raise ValueError("sensitive parser message")

    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth.decode_jwt", _boom)

    with pytest.raises(WebSocketAuthError) as exc:
        decode_ws_token("token-value")

    assert exc.value.code == "AUTH_TOKEN_DECODE_FAILED"


def test_decode_ws_token_missing_tenant_claim_raises(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)
    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.auth.decode_jwt",
        lambda _t: {"sub": "user-1"},
    )
    with pytest.raises(WebSocketAuthError) as exc:
        decode_ws_token("token")
    assert exc.value.code == "AUTH_TENANT_CLAIM_INVALID"


def test_decode_ws_token_missing_user_claim_raises(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)
    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.auth.decode_jwt",
        lambda _t: {"tenant_id": "tenant-abc"},
    )
    with pytest.raises(WebSocketAuthError) as exc:
        decode_ws_token("token")
    assert exc.value.code == "AUTH_USER_CLAIM_INVALID"


def test_decode_ws_token_success(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)
    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.auth.decode_jwt",
        lambda _t: {"tenant_id": "tenant-abc", "sub": "user-xyz"},
    )
    tenant_id, user_id = decode_ws_token("valid.token")
    assert tenant_id == "tenant-abc"
    assert user_id == "user-xyz"


# ---------------------------------------------------------------------------
# workflow_websocket route — integration-level
# ---------------------------------------------------------------------------


def _make_websocket(protocol_header: str = "", request_id: str | None = None) -> MagicMock:
    ws = MagicMock()
    headers: dict[str, str] = {}
    if protocol_header:
        headers["sec-websocket-protocol"] = protocol_header
    if request_id:
        headers["x-request-id"] = request_id
    ws.headers = headers
    ws.close = AsyncMock()
    return ws


@pytest.mark.asyncio
async def test_route_rejects_missing_token(caplog):
    ws = _make_websocket()
    await workflow_websocket(websocket=ws, workflow_id="wf-1", token=None)
    ws.close.assert_awaited_once_with(code=1008, reason="Authentication failed")
    assert "AUTH_TOKEN_MISSING" in caplog.text


@pytest.mark.asyncio
async def test_route_accepts_canonical_header(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)
    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.auth.decode_jwt",
        lambda _t: {"tenant_id": "t-1", "sub": "u-1"},
    )

    ws = _make_websocket("base64url.bearer.authorization, valid.jwt.token")
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    ws.receive_json = AsyncMock(side_effect=WebSocketDisconnect())

    with patch("value_fabric.layer4.api.websocket.routes.get_ws_manager", return_value=mock_manager), \
         patch("value_fabric.layer4.api.websocket.routes._verify_workflow_ownership", return_value=(True, "AUTHZ_OK")):
        await workflow_websocket(websocket=ws, workflow_id="wf-2", token=None)

    mock_manager.connect.assert_awaited_once()
    call_kwargs = mock_manager.connect.call_args
    assert call_kwargs.kwargs["tenant_id"] == "t-1"
    assert call_kwargs.kwargs["user_id"] == "u-1"
    ws.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_route_legacy_query_param_emits_deprecation_and_connects(monkeypatch, caplog):
    import logging

    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)
    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.auth.decode_jwt",
        lambda _t: {"tenant_id": "t-2", "sub": "u-2"},
    )

    ws = _make_websocket()
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()
    ws.receive_json = AsyncMock(side_effect=WebSocketDisconnect())

    with caplog.at_level(logging.WARNING):
        with patch(
            "value_fabric.layer4.api.websocket.routes.get_ws_manager",
            return_value=mock_manager,
        ), patch(
            "value_fabric.layer4.api.websocket.routes._verify_workflow_ownership",
            return_value=(True, "AUTHZ_OK"),
        ):
            await workflow_websocket(websocket=ws, workflow_id="wf-3", token="legacy.jwt")

    assert "DEPRECATION" in caplog.text
    assert "SEC-L3-012" in caplog.text
    mock_manager.connect.assert_awaited_once()
    ws.close.assert_not_awaited()


@pytest.mark.asyncio
async def test_route_does_not_leak_token_in_logs(caplog):
    """Auth failure logs must not contain the raw token value."""
    import logging

    ws = _make_websocket("base64url.bearer.authorization, super.secret.jwt")

    with caplog.at_level(logging.WARNING):
        with patch(
            "value_fabric.layer4.api.websocket.routes.decode_ws_token",
            side_effect=WebSocketAuthError("AUTH_TOKEN_DECODE_FAILED"),
        ):
            await workflow_websocket(websocket=ws, workflow_id="wf-4", token=None)

    assert "super.secret.jwt" not in caplog.text
    assert "AUTH_TOKEN_DECODE_FAILED" in caplog.text
    ws.close.assert_awaited_once_with(code=1008, reason="Authentication failed")


@pytest.mark.asyncio
async def test_route_rejects_cross_tenant_workflow_subscription(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)
    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.auth.decode_jwt",
        lambda _t: {"tenant_id": "tenant-a", "sub": "user-a"},
    )
    ws = _make_websocket("base64url.bearer.authorization, valid.jwt.token", request_id="req-1")
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()

    with patch("value_fabric.layer4.api.websocket.routes.get_ws_manager", return_value=mock_manager), \
         patch("value_fabric.layer4.api.websocket.routes._load_workflow_metadata", return_value={"tenant_id": "tenant-b", "user_id": "user-b"}):
        await workflow_websocket(websocket=ws, workflow_id="wf-tenant-b", token=None)

    mock_manager.connect.assert_not_awaited()
    ws.close.assert_awaited_once()
    assert ws.close.await_args.kwargs["code"] == 1008
    assert "AUTH_WORKFLOW_TENANT_MISMATCH" in ws.close.await_args.kwargs["reason"]


@pytest.mark.asyncio
async def test_route_rejects_missing_workflow_fail_closed(monkeypatch):
    monkeypatch.setattr("value_fabric.layer4.api.websocket.auth._JWT_AVAILABLE", True)
    monkeypatch.setattr(
        "value_fabric.layer4.api.websocket.auth.decode_jwt",
        lambda _t: {"tenant_id": "tenant-a", "sub": "user-a"},
    )
    ws = _make_websocket("base64url.bearer.authorization, valid.jwt.token", request_id="req-2")
    mock_manager = MagicMock()
    mock_manager.connect = AsyncMock()
    mock_manager.disconnect = AsyncMock()

    with patch("value_fabric.layer4.api.websocket.routes.get_ws_manager", return_value=mock_manager), \
         patch("value_fabric.layer4.api.websocket.routes._load_workflow_metadata", return_value=None):
        await workflow_websocket(websocket=ws, workflow_id="wf-missing", token=None)

    mock_manager.connect.assert_not_awaited()
    ws.close.assert_awaited_once()
    assert ws.close.await_args.kwargs["code"] == 1008
    assert "AUTH_WORKFLOW_NOT_FOUND" in ws.close.await_args.kwargs["reason"]
