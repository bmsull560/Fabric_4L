"""Agent Stream route for RightRail conversational assistant (ValuePilot).

Wires the frontend RightRail chat to the ConversationService, which
orchestrates:
  1. Intent classification via ConversationAgent (GATE-governed)
  2. Context gathering via ConversationAgent (GATE-governed)
  3. Workflow delegation via OrchestrationController (when applicable)
  4. Response generation via C1 proxy (LLM) or heuristic fallback

The response contract is unchanged from the original stub:
  { content: str, metadata: AgentGovernanceMetadata }
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from opentelemetry import trace
from pydantic import BaseModel, ConfigDict, Field
from shared.error_handling.middleware import get_request_id
from shared.identity.context import RequestContext
from shared.identity.dependencies import require_authenticated

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response models (unchanged from original contract)
# ---------------------------------------------------------------------------


class AgentStreamMessage(BaseModel):
    """Single chat message compatible with frontend request shape."""

    role: str = Field(..., description="Message role (system|user|assistant)")
    content: str = Field(..., min_length=1, description="Message text")


class AgentStreamAccountContext(BaseModel):
    """Account/workspace context from frontend."""

    account_name: str | None = Field(
        default=None, alias="accountName", description="Selected account display name"
    )
    account_id: str | None = Field(
        default=None, alias="accountId", description="Selected account identifier"
    )
    account_tier: str | None = Field(
        default=None, alias="accountTier", description="Optional account segment/tier"
    )

    model_config = ConfigDict(populate_by_name=True)


class AgentStreamRequest(BaseModel):
    """Request payload expected by RightRail frontend."""

    messages: list[AgentStreamMessage] = Field(..., min_length=1)
    active_tab: str = Field(..., alias="activeTab", min_length=1, description="Active UI tab key")
    account: AgentStreamAccountContext | None = Field(default=None)

    model_config = ConfigDict(populate_by_name=True)


class AgentGovernanceMetadata(BaseModel):
    """Governance metadata surfaced to RightRail and trace/audit views."""

    trace_id: str
    workflow_id: str
    tenant_id: str
    tool_name: str
    audit_event_id: str
    emitted_at: str
    # New fields surfaced from ConversationService
    intent: str | None = None
    confidence: float | None = None
    workflow_triggered: bool | None = None


class AgentStreamResponse(BaseModel):
    """Assistant response payload for RightRail."""

    content: str
    metadata: AgentGovernanceMetadata


# ---------------------------------------------------------------------------
# Singleton ConversationService (lazy-initialized)
# ---------------------------------------------------------------------------

_conversation_service = None


def _get_conversation_service():
    """Lazy-initialize the ConversationService singleton.

    The service is created once and reused across requests. Agent
    instances are optional — the service degrades gracefully when
    they are not available (e.g., during early startup or testing).
    """
    global _conversation_service
    if _conversation_service is not None:
        return _conversation_service

    from ..services.conversation import ConversationService

    # Attempt to instantiate agents — fail gracefully
    conversation_agent = None
    orchestration_controller = None

    try:
        from ..agents.taxonomy import ConversationAgent

        conversation_agent = ConversationAgent(
            config={"manifest_path": "value-fabric/layer4-agents/manifests/conversation_agent.abom.json"},
        )
    except Exception:
        logger.info("ConversationAgent not available — using heuristic mode")

    try:
        from ..agents.taxonomy import OrchestrationController

        orchestration_controller = OrchestrationController(
            config={"manifest_path": "value-fabric/layer4-agents/manifests/orchestration_controller.abom.json"},
        )
    except Exception:
        logger.info("OrchestrationController not available — no workflow delegation")

    c1_enabled = bool(os.getenv("THESYS_API_KEY"))

    _conversation_service = ConversationService(
        conversation_agent=conversation_agent,
        orchestration_controller=orchestration_controller,
        c1_enabled=c1_enabled,
    )

    logger.info(
        "ConversationService initialized: agent=%s, orchestrator=%s, c1=%s",
        conversation_agent is not None,
        orchestration_controller is not None,
        c1_enabled,
    )

    return _conversation_service


# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------


@router.post("/agent-stream/chat", response_model=AgentStreamResponse)
async def agent_stream_chat(
    payload: AgentStreamRequest,
    request: Request,
    ctx: RequestContext = Depends(require_authenticated),
) -> AgentStreamResponse:
    """Handle RightRail chat payload through the ConversationService pipeline.

    The pipeline:
    1. Extract user message and account context from payload
    2. Resolve trace ID from request correlation or OpenTelemetry
    3. Delegate to ConversationService.handle_message()
    4. Return response with governance metadata
    """
    # Extract the last user message
    last_user_message = next(
        (msg.content for msg in reversed(payload.messages) if msg.role.lower() == "user"),
        payload.messages[-1].content,
    )

    # Extract account context
    account_name = (
        payload.account.account_name
        if payload.account and payload.account.account_name
        else "this account"
    )
    account_id = (
        payload.account.account_id
        if payload.account and payload.account.account_id
        else None
    )
    account_tier = (
        payload.account.account_tier
        if payload.account and payload.account.account_tier
        else None
    )

    # Resolve trace ID
    request_trace_id = get_request_id(request)
    span = trace.get_current_span()
    span_context = span.get_span_context()
    trace_id = (
        f"{span_context.trace_id:032x}"
        if span_context is not None and span_context.trace_id != 0
        else request_trace_id
    )

    tenant_id = str(ctx.tenant_id) if ctx.tenant_id else "unknown"

    # Build message list for context
    messages = [{"role": m.role, "content": m.content} for m in payload.messages]

    # Delegate to ConversationService
    service = _get_conversation_service()
    result = await service.handle_message(
        user_message=last_user_message,
        messages=messages,
        active_tab=payload.active_tab,
        account_id=account_id,
        account_name=account_name,
        account_tier=account_tier,
        tenant_id=tenant_id,
        trace_id=trace_id,
    )

    # Map result to response contract
    metadata = result.get("metadata", {})
    return AgentStreamResponse(
        content=result["content"],
        metadata=AgentGovernanceMetadata(
            trace_id=metadata.get("trace_id", trace_id),
            workflow_id=metadata.get("workflow_id", str(uuid.uuid4())),
            tenant_id=metadata.get("tenant_id", tenant_id),
            tool_name=metadata.get("tool_name", "valuepilot_conversation"),
            audit_event_id=metadata.get("audit_event_id", f"audit_{uuid.uuid4().hex[:12]}"),
            emitted_at=metadata.get("emitted_at", datetime.now(UTC).isoformat()),
            intent=metadata.get("intent"),
            confidence=metadata.get("confidence"),
            workflow_triggered=metadata.get("workflow_triggered"),
        ),
    )
