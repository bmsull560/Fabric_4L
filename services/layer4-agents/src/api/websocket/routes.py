"""WebSocket routes for real-time workflow streaming.

Provides WebSocket endpoint for subscribing to workflow events with
automatic reconnection support and event replay.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect
from value_fabric.shared.observability.trace_context import resolve_trace_context

from .manager import get_ws_manager

if TYPE_CHECKING:
    from ...engine.executor import OrchestrationController

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


async def _verify_workflow_ownership(workflow_id: str, tenant_id: str) -> bool:
    """Verify that a workflow belongs to the given tenant.

    Queries the executor's in-memory + persisted metadata. Returns True when
    the workflow exists and its tenant matches. Returns False when the workflow
    is not found (treat as denied to avoid enumeration). Raises on unexpected
    errors so the caller can fail closed.

    Args:
        workflow_id: Workflow instance ID from the WebSocket path.
        tenant_id: Tenant extracted from the authenticated JWT.

    Returns:
        True if the workflow is owned by the tenant, False otherwise.
    """
    try:
        from ...api.routes.workflows import get_executor  # local import — avoids circular dep at module load
        executor = get_executor()
        status = await executor.get_workflow_status(workflow_id)
        if not status:
            # Workflow not found — deny to prevent enumeration
            logger.warning(
                "Workflow ownership check: workflow not found",
                extra={"workflow_id": workflow_id, "tenant_id": tenant_id},
            )
            return False
        workflow_tenant = status.get("tenant_id")
        if not workflow_tenant:
            # No tenant recorded — deny; this should not happen in production
            logger.warning(
                "Workflow ownership check: workflow has no tenant_id",
                extra={"workflow_id": workflow_id},
            )
            return False
        return str(workflow_tenant) == str(tenant_id)
    except Exception:
        logger.exception(
            "Workflow ownership check raised unexpectedly — denying connection",
            extra={"workflow_id": workflow_id},
        )
        return False


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
    # OBS-L4-004: Resolve correlation ID at the HTTP upgrade stage.
    # Inherits X-Request-ID / X-Correlation-ID from the client if present,
    # otherwise generates a new one. All subsequent log calls in this session
    # include this ID so WebSocket events are traceable end-to-end.
    trace_ctx = resolve_trace_context(websocket.headers)
    correlation_id = trace_ctx.trace_id
    _log = {"workflow_id": workflow_id, "correlation_id": correlation_id}

    # P1-13 FIX: Reject JWT in query parameter (prevents logging by proxies)
    if token:
        logger.warning(
            "WebSocket authentication failed: AUTH_QUERY_TOKEN_FORBIDDEN",
            extra={"auth_code": "AUTH_QUERY_TOKEN_FORBIDDEN", **_log},
        )
        await websocket.close(
            code=1008,
            reason="Authentication via query param is forbidden; use Sec-WebSocket-Protocol header",
        )
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
            extra={"auth_code": e.code, **_log},
        )
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Bind tenant context to the log dict now that we have it
    _log["tenant_id"] = tenant_id

    # SEC-L4-WS-001: Verify the requested workflow belongs to the authenticated tenant.
    owned = await _verify_workflow_ownership(workflow_id, tenant_id)
    if not owned:
        logger.warning("WebSocket workflow ownership check failed", extra=_log)
        await websocket.close(code=1008, reason="Workflow not found or access denied")
        return

    logger.info("WebSocket workflow session started", extra=_log)

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
                logger.info("WebSocket client disconnected", extra=_log)
                break
            except Exception as e:
                logger.warning(
                    "WebSocket client message error",
                    extra={**_log, "error": str(e)},
                )
                # Continue rather than break to keep connection alive

    except Exception as e:
        logger.error("WebSocket session error", extra={**_log, "error": str(e)})
    finally:
        logger.info("WebSocket workflow session ended", extra=_log)
        await ws_manager.disconnect(websocket, workflow_id)
