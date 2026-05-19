"""WebSocket routes for real-time workflow streaming.

Authentication transport (canonical):
    Sec-WebSocket-Protocol: base64url.bearer.authorization, <jwt>

Legacy query-parameter auth is accepted with a deprecation warning and
will be removed in v2.0 (SEC-L3-012).

Reconnection:
    Pass ``last_event_id`` query parameter to replay missed events.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .auth import (
    WebSocketAuthError,
    decode_ws_token,
    extract_token_from_protocol_header,
    extract_token_from_query_param,
)
from .manager import get_ws_manager

logger = logging.getLogger(__name__)
websocket_router = APIRouter()


@websocket_router.websocket("/ws/workflows/{workflow_id}")
async def workflow_websocket(
    websocket: WebSocket,
    workflow_id: str,
    last_event_id: str | None = Query(
        None, description="Last seen event ID for replay on reconnect"
    ),
    # DEPRECATED (v2.0 removal: SEC-L3-012): use Sec-WebSocket-Protocol header.
    token: str | None = Query(
        None,
        include_in_schema=False,
        description="DEPRECATED: use Sec-WebSocket-Protocol header",
    ),
) -> None:
    """WebSocket endpoint for real-time workflow streaming.

    **Authentication**

    Preferred (canonical):
    ```
    Sec-WebSocket-Protocol: base64url.bearer.authorization, <jwt>
    ```

    Legacy (deprecated, removed in v2.0):
    ```
    ws://host/v1/ws/workflows/<id>?token=<jwt>
    ```

    **Event Types**
    - `connection_established`: Initial confirmation with replay count
    - `state_update`: Workflow status, progress, current node
    - `node_transition`: Node-to-node transition
    - `pause_point`: Human-in-the-loop pause with required actions
    - `workflow_complete`: Final completion/failure event
    - `ping`: Server heartbeat (respond with `pong`)

    **Client Messages**
    ```json
    {"type": "ack",               "event_id": "evt-123"}
    {"type": "pong"}
    {"type": "subscribe_history"}
    ```

    **Reconnection**
    Store the last `event_id` received. On reconnect pass it as
    `last_event_id` to receive all missed events.
    """
    correlation_id: str | None = websocket.headers.get("x-request-id")

    # --- Token extraction (canonical header first, legacy fallback) ----------
    protocol_header = websocket.headers.get("sec-websocket-protocol", "")
    ws_token = extract_token_from_protocol_header(protocol_header)

    if ws_token is None and token:
        # Legacy path: query-parameter token.  Emits deprecation warning.
        ws_token = extract_token_from_query_param(token, correlation_id=correlation_id)

    # --- Authentication (fail-closed) ----------------------------------------
    try:
        tenant_id, user_id = decode_ws_token(ws_token)
    except WebSocketAuthError as exc:
        logger.warning(
            "WebSocket auth failed: %s workflow_id=%s correlation_id=%s",
            exc.code,
            workflow_id,
            correlation_id,
            extra={
                "auth_code": exc.code,
                "workflow_id": workflow_id,
                "correlation_id": correlation_id,
            },
        )
        await websocket.close(code=1008, reason="Authentication failed")
        return

    ws_manager = get_ws_manager()

    try:
        await ws_manager.connect(
            websocket,
            workflow_id,
            last_event_id,
            tenant_id=tenant_id,
            user_id=user_id,
            correlation_id=correlation_id,
        )

        while True:
            try:
                message = await websocket.receive_json()
                await ws_manager.handle_client_message(websocket, workflow_id, message)
            except WebSocketDisconnect:
                logger.info(
                    "Client disconnected workflow_id=%s tenant_id=%s",
                    workflow_id,
                    tenant_id,
                )
                break
            except Exception as exc:
                logger.warning(
                    "Error handling client message workflow_id=%s: %s",
                    workflow_id,
                    exc,
                )

    except Exception as exc:
        logger.error("WebSocket error workflow_id=%s: %s", workflow_id, exc)
    finally:
        await ws_manager.disconnect(websocket, workflow_id)
