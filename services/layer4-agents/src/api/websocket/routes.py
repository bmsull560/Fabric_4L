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
from value_fabric.shared.observability.trace_context import resolve_trace_context

from .auth import (
    WebSocketAuthError,
    decode_ws_token,
    extract_token_from_protocol_header,
    extract_token_from_query_param,
)
from .manager import get_ws_manager

logger = logging.getLogger(__name__)
websocket_router = APIRouter()


def _auth_close_reason(code: str, detail: str) -> str:
    """Build a compact, structured auth close reason for code 1008."""
    return f"auth_error:{code}:{detail}"


async def _load_workflow_metadata(workflow_id: str) -> dict | None:
    """Load workflow metadata using the same source as HTTP workflow status routes."""
    # Local import — avoids circular dependency at module load time.
    from ...api.routes.workflows import get_executor

    executor = get_executor()
    return await executor.get_workflow_status(workflow_id)


async def _verify_workflow_ownership(workflow_id: str, tenant_id: str, user_id: str) -> tuple[bool, str]:
    """Verify that a workflow belongs to the given authenticated principal.

    Queries the executor's in-memory + persisted metadata. Returns True when
    the workflow exists and its tenant matches. Returns False when the workflow
    is not found (treat as denied to avoid enumeration). Raises on unexpected
    errors so the caller can fail closed.

    Args:
        workflow_id: Workflow instance ID from the WebSocket path.
        tenant_id: Tenant extracted from the authenticated JWT.

    Returns:
        Tuple[allowed, auth_code]
    """
    try:
        status = await _load_workflow_metadata(workflow_id)
        if not status:
            return False, "AUTH_WORKFLOW_NOT_FOUND"
        workflow_tenant = status.get("tenant_id")
        if not workflow_tenant:
            return False, "AUTH_WORKFLOW_TENANT_MISSING"
        if str(workflow_tenant) != str(tenant_id):
            return False, "AUTH_WORKFLOW_TENANT_MISMATCH"

        workflow_user = status.get("user_id")
        if workflow_user and str(workflow_user) != str(user_id):
            return False, "AUTH_WORKFLOW_USER_MISMATCH"

        return True, "AUTHZ_OK"
    except Exception:
        logger.exception(
            "Workflow ownership check raised unexpectedly — denying connection",
            extra={"workflow_id": workflow_id},
        )
        return False, "AUTH_WORKFLOW_LOOKUP_ERROR"


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
    # OBS-L4-004: Resolve correlation ID at the HTTP upgrade stage.
    # Inherits X-Request-ID / X-Correlation-ID from the client if present,
    # otherwise generates a new one so all log calls in this session are traceable.
    trace_ctx = resolve_trace_context(websocket.headers)
    correlation_id = trace_ctx.trace_id
    _log: dict = {"workflow_id": workflow_id, "correlation_id": correlation_id}

    # --- Token extraction (canonical header first, legacy fallback) ----------
    protocol_header = websocket.headers.get("sec-websocket-protocol", "")
    ws_token = extract_token_from_protocol_header(protocol_header)

    if ws_token is None and token:
        # Legacy path: query-parameter token.  Emits DEPRECATION [SEC-L3-012] warning.
        ws_token = extract_token_from_query_param(token, correlation_id=correlation_id)

    # --- Authentication (fail-closed) ----------------------------------------
    try:
        tenant_id, user_id = decode_ws_token(ws_token)
    except WebSocketAuthError as exc:
        logger.warning(
            "WebSocket authentication failed: %s",
            exc.code,
            extra={"auth_code": exc.code, **_log},
        )
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Bind tenant context to the log dict now that we have it.
    _log["tenant_id"] = tenant_id

    # SEC-L4-WS-001: Verify the requested workflow belongs to the authenticated tenant.
    owned, auth_code = await _verify_workflow_ownership(workflow_id, tenant_id, user_id)
    if not owned:
        logger.warning(
            "WebSocket workflow ownership check failed",
            extra={**_log, "auth_code": auth_code, "trace_id": correlation_id},
        )
        await websocket.close(
            code=1008,
            reason=_auth_close_reason(auth_code, "workflow access denied"),
        )
        return

    logger.info("WebSocket workflow session started", extra=_log)

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
                logger.info("WebSocket client disconnected", extra=_log)
                break
            except Exception as exc:
                logger.warning(
                    "WebSocket client message error",
                    extra={**_log, "error": str(exc)},
                )
                # Continue rather than break to keep connection alive

    except Exception as exc:
        logger.error("WebSocket session error", extra={**_log, "error": str(exc)})
    finally:
        logger.info("WebSocket workflow session ended", extra=_log)
        await ws_manager.disconnect(websocket, workflow_id)
