"""Agent Stream route for RightRail conversational assistant."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from opentelemetry import trace
from pydantic import BaseModel, ConfigDict, Field
from shared.error_handling.middleware import get_request_id
from shared.identity.context import RequestContext
from shared.identity.dependencies import require_authenticated

router = APIRouter()


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


class AgentStreamResponse(BaseModel):
    """Assistant response payload for RightRail."""

    content: str
    metadata: AgentGovernanceMetadata


def _build_response_content(active_tab: str, account_name: str, user_prompt: str) -> str:
    """Generate concise tab-aware response until full orchestration wiring is enabled."""
    lower_prompt = user_prompt.lower()
    if "summary" in lower_prompt or "summarize" in lower_prompt:
        return (
            f"Quick summary for {account_name} in {active_tab}: focus the top two signals by confidence, "
            "tie each to measurable impact, and capture one validation question for the next customer touchpoint."
        )

    if "next" in lower_prompt or "recommend" in lower_prompt or "suggest" in lower_prompt:
        return (
            f"For {account_name} in {active_tab}, recommended next steps are to validate the leading hypothesis, "
            "map it to one value driver, and add the evidence gap to your action plan."
        )

    return (
        f"Got it — for {account_name} in {active_tab}, I can help analyze findings, prioritize actions, "
        "or draft stakeholder-ready messaging. Tell me which direction you want."
    )


@router.post("/agent-stream/chat", response_model=AgentStreamResponse)
async def agent_stream_chat(
    payload: AgentStreamRequest,
    request: Request,
    ctx: RequestContext = Depends(require_authenticated),
) -> AgentStreamResponse:
    """Handle RightRail chat payload and emit governance metadata per interaction."""
    last_user_message = next(
        (msg.content for msg in reversed(payload.messages) if msg.role.lower() == "user"),
        payload.messages[-1].content,
    )

    account_name = (
        payload.account.account_name
        if payload.account and payload.account.account_name
        else "this account"
    )

    # Use request correlation ID for traceability; fall back to OpenTelemetry span trace id.
    request_trace_id = get_request_id(request)
    span = trace.get_current_span()
    span_context = span.get_span_context()
    otel_trace_id = (
        f"{span_context.trace_id:032x}"
        if span_context is not None and span_context.trace_id != 0
        else request_trace_id
    )

    workflow_id = str(uuid.uuid4())
    audit_event_id = f"audit_{uuid.uuid4().hex[:12]}"

    return AgentStreamResponse(
        content=_build_response_content(payload.active_tab, account_name, last_user_message),
        metadata=AgentGovernanceMetadata(
            trace_id=otel_trace_id,
            workflow_id=workflow_id,
            tenant_id=str(ctx.tenant_id) if ctx.tenant_id else "unknown",
            tool_name="right_rail_agent_stream",
            audit_event_id=audit_event_id,
            emitted_at=datetime.now(UTC).isoformat(),
        ),
    )
