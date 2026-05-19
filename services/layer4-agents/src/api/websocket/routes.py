"""WebSocket routes for real-time workflow streaming.

Provides a WebSocket endpoint for subscribing to workflow events with
automatic reconnection support and event replay.

Authentication contract (SEC-L3-012 — Sprint 3 cutover):
  The ONLY accepted authentication vector is the ``Sec-WebSocket-Protocol``
  header carrying a JWT bearer token in the format ``token,<jwt>``.
  Query-parameter authentication (?token= / ?auth=) has been removed.
  Any connection attempt that omits or malforms the header is rejected
  immediately with WebSocket close code 1008 (Policy Violation).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .manager import get_ws_manager

try:
    from value_fabric.shared.identity.jwt import decode_jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    decode_jwt = None  # type: ignore

logger = logging.getLogger(__name__)
websocket_router = APIRouter()


_TOKEN_EXCEPTION_CODE_MAP = {
    "ExpiredSignatureError": "AUTH_TOKEN_EXPIRED",
    "InvalidTokenError": "AUTH_TOKEN_INVALID",
    "DecodeError": "AUTH_TOKEN_DECODE_FAILED",
    "InvalidSignatureError": "AUTH_TOKEN_SIGNATURE_INVALID",
}


class WebSocketAuthError(Exception):
    """Raised when WebSocket authentication fails."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def _extract_tenant_from_token(token: str | None) -> tuple[str, str]:
    """Extract tenant_id and user_id from a JWT bearer token.

    Args:
        token: JWT bearer token parsed from the Sec-WebSocket-Protocol header.

    Returns:
        Tuple of (tenant_id, user_id).

    Raises:
        WebSocketAuthError: If the token is missing, invalid, or expired.
    """
    if token is None or not token.strip():
        raise WebSocketAuthError("AUTH_TOKEN_MISSING")

    if not JWT_AVAILABLE:
        raise WebSocketAuthError("AUTH_JWT_UNAVAILABLE")

    try:
        payload = decode_jwt(token)
        if not payload:
            raise WebSocketAuthError("AUTH_INVALID_PAYLOAD")

        if isinstance(payload, dict):
            tenant_id = payload.get("tenant_id")
            user_id = payload.get("sub") or payload.get("user_id")
        else:
            tenant_id = getattr(payload, "tenant_id", None)
            user_id = getattr(payload, "sub", None) or getattr(payload, "user_id", None)

        if not tenant_id or not isinstance(tenant_id, str):
            raise WebSocketAuthError("AUTH_TENANT_CLAIM_INVALID")
        if not user_id or not isinstance(user_id, str):
            raise WebSocketAuthError("AUTH_USER_CLAIM_INVALID")

        return tenant_id, user_id

    except WebSocketAuthError:
        raise
    except Exception as exc:
        error_code = _TOKEN_EXCEPTION_CODE_MAP.get(
            exc.__class__.__name__,
            "AUTH_TOKEN_DECODE_FAILED",
        )
        logger.warning("WebSocket JWT decode failed", extra={"auth_code": error_code})
        raise WebSocketAuthError(error_code)


@websocket_router.websocket("/ws/workflows/{workflow_id}")
async def workflow_websocket(
    websocket: WebSocket,
    workflow_id: str,
    last_event_id: str | None = Query(
        None, description="Last seen event ID for replay on reconnect"
    ),
) -> None:
    """WebSocket endpoint for real-time workflow streaming.

    **Authentication**

    Pass the JWT bearer token exclusively via the ``Sec-WebSocket-Protocol``
    header in the format ``token,<jwt>``:

    ```javascript
    const ws = new WebSocket(
        'ws://localhost:8000/v1/ws/workflows/wf-123',
        ['token', '<jwt>']
    );
    ```

    Connections that omit the header, or that attempt to pass credentials via
    query parameters, are rejected immediately with close code 1008.

    **Event Types**
    - ``connection_established``: Initial confirmation with replay count
    - ``state_update``: Workflow status, progress, current node
    - ``node_transition``: Moving from one node to another
    - ``pause_point``: Human-in-the-loop pause with required actions
    - ``workflow_complete``: Final completion/failure event
    - ``ping``: Server heartbeat (respond with ``pong``)

    **Reconnection**
    Store the last ``event_id`` received. On reconnect, pass it as
    ``last_event_id`` to receive all missed events.
    """
    # Strict enforcement: Sec-WebSocket-Protocol is the only auth vector.
    # Query-parameter auth (?token= / ?auth=) was removed in SEC-L3-012.
    # Only accept the explicit "token,<jwt>" format.
    # A bare single-value header (e.g. a subprotocol name) is NOT treated as
    # a token — that path was removed to prevent accidental decode attempts on
    # non-JWT subprotocol strings and to enforce a single unambiguous contract.
    protocol_header = websocket.headers.get("sec-websocket-protocol", "")
    ws_token: str | None = None
    if protocol_header:
        parts = protocol_header.split(",")
        if len(parts) >= 2 and parts[0].strip().lower() == "token":
            ws_token = parts[1].strip()

    ws_manager = get_ws_manager()

    try:
        tenant_id, user_id = _extract_tenant_from_token(ws_token)
    except WebSocketAuthError as e:
        logger.warning(
            "WebSocket authentication failed: %s",
            e.code,
            extra={"auth_code": e.code, "workflow_id": workflow_id},
        )
        await websocket.close(code=1008, reason="Authentication failed")
        return

    try:
        await ws_manager.connect(
            websocket,
            workflow_id,
            last_event_id,
            tenant_id=tenant_id,
            user_id=user_id,
        )

        while True:
            try:
                message = await websocket.receive_json()
                await ws_manager.handle_client_message(websocket, workflow_id, message)
            except WebSocketDisconnect:
                logger.info("Client disconnected from workflow %s", workflow_id)
                break
            except Exception as e:
                logger.warning(
                    "Error handling client message for workflow %s: %s", workflow_id, e
                )

    except Exception as e:
        logger.error("WebSocket error for workflow %s: %s", workflow_id, e)
    finally:
        await ws_manager.disconnect(websocket, workflow_id)
