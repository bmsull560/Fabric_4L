"""Focused Layer 4 agent tenant-isolation tests."""

from __future__ import annotations

from typing import Any
from uuid import UUID

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from value_fabric.layer4.api.routes import agent_stream
from value_fabric.layer4.services.conversation import ConversationService
from value_fabric.layer4.tools.registry import TenantAwareTool, ToolResult
from value_fabric.shared.identity.context import RequestContext


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()
    app.include_router(agent_stream.router, prefix="/v1")
    return app


class CapturingService:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    async def handle_message(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(kwargs)
        return {
            "content": "tenant scoped response",
            "metadata": {
                "trace_id": kwargs["trace_id"],
                "workflow_id": "wf-tenant",
                "tenant_id": kwargs["tenant_id"],
                "tool_name": "valuepilot_conversation",
                "audit_event_id": "audit-tenant",
                "emitted_at": "2026-05-05T00:00:00+00:00",
                "intent": "general_question",
                "confidence": 0.5,
                "workflow_triggered": False,
            },
        }


@pytest.mark.asyncio
async def test_agent_missing_tenant_context_fails_closed(app: FastAPI) -> None:
    async def missing_tenant_context() -> RequestContext:
        return RequestContext(user_id="user-without-tenant")

    app.dependency_overrides[agent_stream.require_authenticated] = missing_tenant_context

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/agent-stream/chat",
            json={
                "messages": [{"role": "user", "content": "Summarize evidence."}],
                "activeTab": "evidence",
            },
        )

    assert response.status_code == 400
    assert "tenant context" in response.text.lower()


@pytest.mark.asyncio
async def test_agent_malformed_tenant_context_fails_closed() -> None:
    class Input(BaseModel):
        value: int

    class Tool(TenantAwareTool):
        name = "tenant_required_tool"
        input_schema = Input
        output_schema = BaseModel

        async def execute(self, input_data: Input) -> dict[str, Any]:
            return {"tenant_id": self.get_tenant_id()}

    result = await Tool(config={"tenant_id": ""}).run({"value": 1})

    assert result.status == "error"
    assert result.error["code"] == "TENANT_CONTEXT_MISSING"
    assert "requires tenant context" in result.error["message"]


@pytest.mark.asyncio
async def test_forged_tenant_header_cannot_override_validated_context(
    app: FastAPI,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service = CapturingService()
    validated_tenant = UUID("12345678-1234-1234-1234-123456789abc")

    async def valid_context() -> RequestContext:
        return RequestContext(tenant_id=validated_tenant, user_id="user-a")

    app.dependency_overrides[agent_stream.require_authenticated] = valid_context
    monkeypatch.setattr(agent_stream, "_get_conversation_service", lambda: service)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/v1/agent-stream/chat",
            headers={"X-Tenant-ID": "00000000-0000-0000-0000-000000000999"},
            json={
                "messages": [{"role": "user", "content": "Summarize evidence."}],
                "activeTab": "evidence",
                "account": {"accountId": "account-a", "accountName": "Acme"},
            },
        )

    assert response.status_code == 200, response.text
    assert service.calls[0]["tenant_id"] == str(validated_tenant)
    assert response.json()["metadata"]["tenant_id"] == str(validated_tenant)


@pytest.mark.asyncio
async def test_agent_tool_receives_validated_tenant_context() -> None:
    class Input(BaseModel):
        value: int

    class Tool(TenantAwareTool):
        name = "tenant_context_echo"
        input_schema = Input
        output_schema = BaseModel

        async def execute(self, input_data: Input) -> dict[str, Any]:
            return {"tenant_id": self.get_tenant_id(), "value": input_data.value}

    result = await Tool(config={"tenant_id": "tenant-a"}).run(
        {"value": 7, "trace_id": "trace-tenant"}
    )

    assert isinstance(result, ToolResult)
    assert result.status == "success"
    assert result.data["tenant_id"] == "tenant-a"
    assert result.metadata["tenant_id"] == "tenant-a"


@pytest.mark.asyncio
async def test_agent_retrieval_excludes_foreign_tenant_evidence() -> None:
    service = ConversationService(
        conversation_agent=None,
    )
    result = await service._generate_response(
        user_message="Cite evidence for this value claim.",
        messages=[{"role": "user", "content": "Cite evidence for this value claim."}],
        active_tab="evidence",
        intent="value_analysis",
        context_data={
            "tenant_id": "tenant-a",
            "evidence_records": [
                {"id": "ev-a", "tenant_id": "tenant-a"},
                {"id": "ev-b", "tenant_id": "tenant-b"},
            ],
        },
        workflow_result=None,
        account_name="Acme",
        gate_context={},
    )

    assert "ev-a" in result
    assert "ev-b" not in result


@pytest.mark.asyncio
async def test_agent_output_contains_no_foreign_tenant_data() -> None:
    service = ConversationService()
    result = await service._generate_response(
        user_message="Cite evidence for this value claim.",
        messages=[{"role": "user", "content": "Cite evidence for this value claim."}],
        active_tab="evidence",
        intent="value_analysis",
        context_data={
            "tenant_id": "tenant-a",
            "evidence_records": [
                {"id": "foreign-account-secret", "tenant_id": "tenant-b"},
            ],
        },
        workflow_result=None,
        account_name="Acme",
        gate_context={},
    )

    assert "foreign-account-secret" not in result
    assert "cannot present it as verified" in result.lower()
