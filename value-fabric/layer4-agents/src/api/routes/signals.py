"""Signal API routes for operational pain signal management.

Provides REST API endpoints for:
- Prospect setup and signal detection triggering
- Signal retrieval for accounts
- WebSocket streaming for real-time signal discovery
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field
from shared.audit import AuditAction, AuditEmitter, AuditOutcome
from shared.identity.context import RequestContext
from shared.identity.dependencies import require_authenticated

from ...agents.signal_detection import SignalDetectionAgent
from ...messaging.signal_events import (
    SignalCompletedEvent,
    SignalDiscoveredEvent,
    SignalFailedEvent,
    SignalStreamCompleteEvent,
)
from ...models.pain_signal import PainSignal, SignalCategory

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================


class ProspectData(BaseModel):
    """Prospect setup input data."""

    account_id: str = Field(..., description="Account identifier")
    company_name: str = Field(..., description="Company name")
    industry: str | None = Field(default=None, description="Industry vertical")
    business_pains: list[str] = Field(default_factory=list, description="Reported business pains")
    friction_points: list[str] = Field(default_factory=list, description="Current friction points")
    desired_outcomes: list[str] = Field(default_factory=list, description="Desired outcomes")
    prompt_text: str = Field(..., description="Freeform prompt text")
    prompt_id: str | None = Field(default=None, description="Optional prompt identifier")
    attachments: list[dict[str, Any]] = Field(default_factory=list, description="Attached documents")


class ProspectSetupRequest(BaseModel):
    """Request to set up a prospect and detect signals."""

    prospect_data: ProspectData = Field(..., description="Prospect information")
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Detection options (include_evidence, quantify_impact)"
    )


class ProcessingMetadata(BaseModel):
    """Metadata about signal processing."""

    extraction_duration_ms: int = Field(default=0)
    enrichment_duration_ms: int = Field(default=0)
    persistence_duration_ms: int = Field(default=0)
    signals_found: int = Field(default=0)
    signals_with_evidence: int = Field(default=0)
    signals_quantified: int = Field(default=0)
    trace_id: str = Field(default="")


class ProspectSetupResponse(BaseModel):
    """Response from prospect setup with detected signals."""

    success: bool = Field(..., description="Whether detection succeeded")
    signals: list[dict[str, Any]] = Field(default_factory=list, description="Detected signals")
    processing_metadata: ProcessingMetadata = Field(default_factory=dict)
    message: str | None = Field(default=None, description="Status message")


class SignalListResponse(BaseModel):
    """Response with list of signals for an account."""

    account_id: str = Field(..., description="Account identifier")
    signals: list[dict[str, Any]] = Field(default_factory=list, description="Signals")
    total_count: int = Field(..., description="Total number of signals")
    category_filter: str | None = Field(default=None, description="Applied category filter")


class SignalStreamEvent(BaseModel):
    """WebSocket event for signal streaming."""

    event_type: str = Field(..., description="Event type (discovered, completed, failed, complete)")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    prospect_id: str = Field(..., description="Associated prospect/account ID")
    payload: dict[str, Any] = Field(default_factory=dict, description="Event payload")


# ============================================================================
# API Endpoints
# ============================================================================


def get_signal_agent() -> SignalDetectionAgent:
    """Get or create signal detection agent instance."""
    # In production, this would be a dependency injection or singleton
    # For now, create fresh instance per request
    return SignalDetectionAgent(
        config={
            "max_signals_per_request": 3,
            "evidence_match_limit": 5,
        }
    )


@router.post("/prospects/setup", response_model=ProspectSetupResponse)
async def setup_prospect(
    request: ProspectSetupRequest,
    ctx: RequestContext = Depends(require_authenticated),
    audit: AuditEmitter = Depends(AuditEmitter),
) -> ProspectSetupResponse:
    """Submit prospect setup data and detect operational signals.

    This endpoint triggers the complete signal detection pipeline:
    1. Layer 2: LLM extraction of operational signals
    2. Layer 3: Evidence matching and impact quantification
    3. Layer 3: Persistence to knowledge graph

    Args:
        request: Prospect setup data with options
        ctx: Request context with tenant_id and user info
        audit: Audit emitter for compliance logging

    Returns:
        ProspectSetupResponse with detected signals and metadata
    """
    start_time = datetime.now(UTC)

    try:
        # Initialize agent
        agent = get_signal_agent()
        await agent.initialize()

        # Set default options
        options = request.options or {}
        options.setdefault("include_evidence", True)
        options.setdefault("quantify_impact", True)
        options.setdefault("stream_results", False)

        # Prepare task
        task = {
            "capability": "detect_operational_signals",
            "parameters": {
                "prospect_data": request.prospect_data.model_dump(),
                "options": options,
            },
        }

        # Prepare context
        context = {
            "tenant_id": ctx.tenant_id,
            "user_id": ctx.user_id,
            "trace_id": ctx.trace_id,
        }

        # Execute detection
        result = await agent.execute(task, context)

        # Emit audit event
        await audit.emit(
            AuditAction.CREATE,
            resource_type="signals",
            resource_id=request.prospect_data.account_id,
            outcome=AuditOutcome.SUCCESS,
            metadata={
                "signals_found": result.get("processing_metadata", {}).get("signals_found", 0),
                "trace_id": ctx.trace_id,
            },
        )

        # Calculate total duration
        processing_metadata = result.get("processing_metadata", {})

        return ProspectSetupResponse(
            success=True,
            signals=result.get("signals", []),
            processing_metadata=ProcessingMetadata(
                extraction_duration_ms=processing_metadata.get("extraction_duration_ms", 0),
                enrichment_duration_ms=processing_metadata.get("enrichment_duration_ms", 0),
                persistence_duration_ms=processing_metadata.get("persistence_duration_ms", 0),
                signals_found=processing_metadata.get("signals_found", 0),
                signals_with_evidence=processing_metadata.get("signals_with_evidence", 0),
                signals_quantified=processing_metadata.get("signals_quantified", 0),
                trace_id=ctx.trace_id or "",
            ),
            message=f"Detected {processing_metadata.get('signals_found', 0)} operational signals",
        )

    except Exception as e:
        logger.error(
            f"Prospect setup failed: {e}",
            extra={"tenant_id": ctx.tenant_id, "trace_id": ctx.trace_id},
        )

        # Emit audit event for failure
        await audit.emit(
            AuditAction.CREATE,
            resource_type="signals",
            resource_id=request.prospect_data.account_id,
            outcome=AuditOutcome.FAILURE,
            metadata={"error": str(e), "trace_id": ctx.trace_id},
        )

        raise HTTPException(
            status_code=500,
            detail=f"Signal detection failed: {str(e)}",
        )


@router.get("/accounts/{account_id}/signals", response_model=SignalListResponse)
async def get_account_signals(
    account_id: str,
    category: str | None = None,
    ctx: RequestContext = Depends(require_authenticated),
) -> SignalListResponse:
    """Get signals for an account.

    Retrieves persisted pain signals with optional category filtering.

    Args:
        account_id: Account identifier
        category: Optional category filter (e.g., "Operational")
        ctx: Request context with tenant_id

    Returns:
        SignalListResponse with signals for the account
    """
    try:
        agent = get_signal_agent()
        await agent.initialize()

        signals = await agent.get_account_signals(
            account_id=account_id,
            tenant_id=ctx.tenant_id,
            category=category,
        )

        return SignalListResponse(
            account_id=account_id,
            signals=[s.model_dump() for s in signals],
            total_count=len(signals),
            category_filter=category,
        )

    except Exception as e:
        logger.error(
            f"Failed to retrieve account signals: {e}",
            extra={"tenant_id": ctx.tenant_id, "account_id": account_id},
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve signals: {str(e)}",
        )


@router.get("/signals/{signal_id}")
async def get_signal_by_id(
    signal_id: str,
    ctx: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    """Get a specific signal by ID.

    Args:
        signal_id: Signal identifier
        ctx: Request context with tenant_id

    Returns:
        Signal data
    """
    # This would typically call Layer 3 to fetch the signal
    # For now, return a placeholder that Layer 3 will implement
    raise HTTPException(
        status_code=501,
        detail="Signal retrieval by ID - implement in Layer 3 integration",
    )


# ============================================================================
# WebSocket Streaming
# ============================================================================


@router.websocket("/signals/stream/{prospect_id}")
async def signal_stream_websocket(
    websocket: WebSocket,
    prospect_id: str,
) -> None:
    """WebSocket endpoint for real-time signal streaming.

    Streams signal discovery events as they are detected:
    - signal_discovered: New signal found during extraction
    - signal_completed: Signal fully processed with evidence
    - signal_failed: Processing error for a signal
    - stream_complete: All signals processed

    Args:
        websocket: WebSocket connection
        prospect_id: Prospect/account ID to stream signals for
    """
    # P0-9 FIX: Authenticate WebSocket before accepting
    from shared.identity.jwt import decode_jwt
    import os

    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    try:
        jwt_secret = os.getenv("JWT_SECRET", "")
        payload = decode_jwt(token, jwt_secret)
        if not payload or not payload.get("tenant_id"):
            await websocket.close(code=1008, reason="Invalid token")
            return
    except Exception:
        await websocket.close(code=1008, reason="Authentication failed")
        return

    await websocket.accept()
    active = True

    try:
        # Send connection confirmation
        await websocket.send_json({
            "event_type": "connected",
            "prospect_id": prospect_id,
            "timestamp": datetime.now(UTC).isoformat(),
        })

        # Keep connection alive and wait for client messages
        while active:
            try:
                # Receive messages from client (ping/keepalive or configuration)
                data = await websocket.receive_text()
                # Echo or process client messages
                if data == "ping":
                    await websocket.send_json({
                        "event_type": "pong",
                        "timestamp": datetime.now(UTC).isoformat(),
                    })
                else:
                    # Handle configuration updates if needed
                    await websocket.send_json({
                        "event_type": "ack",
                        "received": data,
                        "timestamp": datetime.now(UTC).isoformat(),
                    })

            except WebSocketDisconnect:
                active = False
                logger.info(f"Signal stream disconnected for prospect {prospect_id}")

    except Exception as e:
        logger.error(f"Signal stream error for {prospect_id}: {e}")
        await websocket.close(code=1011, reason=f"Server error: {str(e)}")


async def stream_signals_to_websocket(
    websocket: WebSocket,
    prospect_data: ProspectData,
    tenant_id: str,
    trace_id: str,
) -> None:
    """Stream signal detection results to WebSocket.

    This is the actual streaming implementation called by the prospect setup endpoint
    when stream_results=True.

    Args:
        websocket: Active WebSocket connection
        prospect_data: Prospect setup data
        tenant_id: Tenant identifier
        trace_id: Trace ID for observability
    """
    agent = get_signal_agent()
    await agent.initialize()

    # Set up streaming callback
    async def emit_event(event_data: dict[str, Any]) -> None:
        try:
            await websocket.send_json(event_data)
        except Exception as e:
            logger.warning(f"Failed to send WebSocket event: {e}")

    # Configure task with streaming
    task = {
        "capability": "stream_signal_detection",
        "parameters": {
            "prospect_data": prospect_data.model_dump(),
            "stream_callback": emit_event,
            "options": {"include_evidence": True, "quantify_impact": True},
        },
    }

    context = {
        "tenant_id": tenant_id,
        "trace_id": trace_id,
    }

    # Execute with streaming
    await agent.execute(task, context)
