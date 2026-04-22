"""WebSocket routes for real-time workflow streaming.

Provides WebSocket endpoint for subscribing to workflow events with
automatic reconnection support and event replay.
"""

import logging
import os

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from .manager import get_ws_manager

try:
    from shared.identity.jwt import decode_jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False
    decode_jwt = None  # type: ignore

logger = logging.getLogger(__name__)
websocket_router = APIRouter()


def _extract_tenant_from_token(token: str | None) -> tuple[str | None, str | None]:
    """Extract tenant_id and user_id from JWT token (Task 2.2).

    Args:
        token: JWT bearer token

    Returns:
        Tuple of (tenant_id, user_id) or (None, None) if invalid
    """
    if not token or not JWT_AVAILABLE:
        return None, None

    jwt_secret = os.environ.get("JWT_SECRET")

    try:
        payload = decode_jwt(token, jwt_secret)
        if payload:
            tenant_id = payload.get("tenant_id")
            user_id = payload.get("sub")
            return tenant_id, user_id
    except Exception as e:
        logger.warning(f"Failed to decode JWT for WebSocket: {e}")

    return None, None


@websocket_router.websocket("/ws/workflows/{workflow_id}")
async def workflow_websocket(
    websocket: WebSocket,
    workflow_id: str,
    last_event_id: str | None = Query(
        None, description="Last seen event ID for replay on reconnect"
    ),
    token: str | None = Query(
        None, description="JWT token for tenant context (Task 2.2)"
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
    ws_manager = get_ws_manager()

    # Task 2.2: Extract tenant context from JWT token
    tenant_id, user_id = _extract_tenant_from_token(token)

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
