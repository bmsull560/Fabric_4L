from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.models.agent_state import WorkflowStatus, WorkflowType
from src.workflows.replay import (
    Layer4WorkflowReplayHarness,
    ReplayAuthorizationContext,
    ReplayEventEnvelopeV1,
)


class _AuditSink:
    def __init__(self) -> None:
        self.records: list[tuple[str, dict]] = []

    def record(self, action: str, details: dict) -> None:
        self.records.append((action, details))


def _evt(event_id: str, event_type: str, ts: int, payload: dict | None = None) -> ReplayEventEnvelopeV1:
    return ReplayEventEnvelopeV1(
        event_id=event_id,
        tenant_id="tenant-a",
        actor="user:alice",
        timestamp=datetime(2026, 1, 1, 0, 0, ts, tzinfo=UTC),
        correlation_id="corr-1",
        schema_version="1.0",
        domain="layer4.workflow_state",
        event_type=event_type,
        payload_pointer=f"s3://replay/{event_id}.json",
        payload_checksum="sha256:abc",
        payload_redacted=payload or {},
    )


def test_replay_is_deterministic_for_historical_events() -> None:
    sink = _AuditSink()
    harness = Layer4WorkflowReplayHarness(sink)
    authz = ReplayAuthorizationContext(
        tenant_id="tenant-a", actor="replay-bot", roles=("replay:execute",), environment="test"
    )
    events = [
        _evt("e2", "workflow.started", 2),
        _evt("e1", "workflow.created", 1),
        _evt("e3", "workflow.node_transition", 3, {"current_node": "roi_compute"}),
        _evt("e4", "workflow.completed", 4, {"roi": 12.3}),
    ]

    result_a = harness.replay(workflow_id="wf-1", workflow_type=WorkflowType.ROI_CALCULATOR, events=events, authz=authz)
    result_b = harness.replay(workflow_id="wf-1", workflow_type=WorkflowType.ROI_CALCULATOR, events=list(reversed(events)), authz=authz)

    assert result_a.applied_event_ids == ["e1", "e2", "e3", "e4"]
    assert result_a.applied_event_ids == result_b.applied_event_ids
    assert result_a.state.status == WorkflowStatus.COMPLETED
    assert result_a.state.current_node == "roi_compute"
    assert result_a.state.output_data == {"roi": 12.3}
    assert result_a.state.model_dump() == result_b.state.model_dump()


def test_replay_rejects_cross_tenant_events() -> None:
    sink = _AuditSink()
    harness = Layer4WorkflowReplayHarness(sink)
    authz = ReplayAuthorizationContext(
        tenant_id="tenant-a", actor="replay-bot", roles=("replay:execute",), environment="test"
    )
    bad = _evt("e1", "workflow.created", 1)
    bad = bad.model_copy(update={"tenant_id": "tenant-b"})

    with pytest.raises(PermissionError, match="Cross-tenant replay"):
        harness.replay(workflow_id="wf-1", workflow_type=WorkflowType.ROI_CALCULATOR, events=[bad], authz=authz)
