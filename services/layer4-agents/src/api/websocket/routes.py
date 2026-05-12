"""WebSocket routes for real-time workflow streaming.

Provides WebSocket endpoint for subscribing to workflow events with
automatic reconnection support and event replay.
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
    """Extract tenant_id and user_id from JWT token (Task 2.2).

    Args:
        token: JWT bearer token from Sec-WebSocket-Protocol header

    Returns:
        Tuple of (tenant_id, user_id)

    Raises:
        WebSocketAuthError: If token is missing, invalid, or expired
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
    # P1-13 FIX: Reject token in query param (logged by proxies)
    token: str | None = Query(
        None, description="DEPRECATED: Use Sec-WebSocket-Protocol header instead"
    ),
):
    """WebSocket endpoint for real-time workflow streaming.

    Connect to this endpoint to receive live updates about workflow progress,
    state transitions, and pause points.

    **Connection**
    ```javascript
    const ws = new WebSocket(
        'ws://localhost:8000/v1/ws/workflows/wf-123?last_event_id=evt-123456'
    );
    ```

    **Event Types**
    - `connection_established`: Initial connection confirmation with replay count
    - `state_update`: Workflow status, progress, current node
    - `node_transition`: Moving from one node to another
    - `pause_point`: Human-in-the-loop pause with required actions
    - `workflow_complete`: Final completion/failure event
    - `ping`: Server heartbeat (respond with `pong`)

    **Client Messages**
    ```javascript
    // Acknowledge receipt
    ws.send(JSON.stringify({type: 'ack', event_id: 'evt-123'}));

    // Respond to ping
    ws.send(JSON.stringify({type: 'pong'}));

    // Request history replay
    ws.send(JSON.stringify({type: 'subscribe_history'}));
    ```

    **Reconnection Strategy**
    Store the last `event_id` received. On reconnect, pass it as `last_event_id`
    query parameter to receive all missed events.

    Args:
        workflow_id: Workflow instance ID to subscribe to
        last_event_id: Optional last seen event for replay on reconnect
    """
    # P1-13 FIX: Reject JWT in query parameter (prevents logging by proxies)
    if token:
        logger.warning(
            "WebSocket authentication failed",
            extra={"auth_code": "AUTH_QUERY_TOKEN_FORBIDDEN", "workflow_id": workflow_id},
        )
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # P1-13 FIX: Accept JWT from Sec-WebSocket-Protocol header instead
    protocol_header = websocket.headers.get("sec-websocket-protocol", "")
    ws_token = None
    if protocol_header:
        # Protocol header format: "token,<jwt>" or just "<jwt>"
        parts = protocol_header.split(",")
        if len(parts) >= 2 and parts[0].strip().lower() == "token":
            ws_token = parts[1].strip()
        elif len(parts) == 1:
            ws_token = parts[0].strip()

    ws_manager = get_ws_manager()

    # Task 2.2: Extract tenant context from JWT token (now from header)
    # P0 SECURITY FIX: Fail closed - any auth error rejects connection
    try:
        tenant_id, user_id = _extract_tenant_from_token(ws_token)
    except WebSocketAuthError as e:
        logger.warning(
            "WebSocket authentication failed",
            extra={"auth_code": e.code, "workflow_id": workflow_id},
        )
        await websocket.close(code=1008, reason="Authentication failed")
        return

    try:
        # Accept connection and send replay if reconnecting (with tenant context)
        await ws_manager.connect(
            websocket, workflow_id, last_event_id,
            tenant_id=tenant_id, user_id=user_id
        )

        # Keep connection alive and handle client messages
        while True:
            try:
                # Wait for messages from client (acks, pong responses)
                message = await websocket.receive_json()
                await ws_manager.handle_client_message(websocket, workflow_id, message)

            except WebSocketDisconnect:
                logger.info(f"Client disconnected from workflow {workflow_id}")
                break
            except Exception as e:
                logger.warning(f"Error handling client message for workflow {workflow_id}: {e}")
                # Continue rather than break to keep connection alive

    except Exception as e:
        logger.error(f"WebSocket error for workflow {workflow_id}: {e}")
    finally:
        # Cleanup connection
        await ws_manager.disconnect(websocket, workflow_id)
