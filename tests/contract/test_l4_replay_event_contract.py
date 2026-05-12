"""Contract tests for Layer 4 replay event envelope and compatibility guarantees."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "contracts" / "jsonschema" / "layer4-workflow-replay-event-envelope-v1.schema.json"


def _validator() -> jsonschema.Draft202012Validator:
    with SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = json.load(f)
    return jsonschema.Draft202012Validator(schema)


def test_replay_event_v1_accepts_minimal_historical_event() -> None:
    validator = _validator()
    historical_event = {
        "event_id": "evt-2025-0001",
        "tenant_id": "tenant-1",
        "actor": "system:workflow-engine",
        "timestamp": "2025-11-10T08:30:00Z",
        "correlation_id": "corr-xyz",
        "schema_version": "1.0",
        "domain": "layer4.workflow_state",
        "event_type": "workflow.started",
        "payload_pointer": "s3://replay/evt-2025-0001.json",
        "payload_checksum": "sha256:1234",
        "payload_redacted": {"current_node": "start"},
    }

    jsonschema.validate(historical_event, validator.schema)


def test_replay_event_schema_version_is_backward_compatible_with_1x() -> None:
    validator = _validator()
    event_v11 = {
        "event_id": "evt-2026-0001",
        "tenant_id": "tenant-1",
        "actor": "user:auditor",
        "timestamp": "2026-02-01T12:00:00Z",
        "correlation_id": "corr-abc",
        "schema_version": "1.1",
        "domain": "layer5.truth_object",
        "event_type": "truth_object.validated",
        "payload_pointer": "vault://replay/evt-2026-0001",
        "payload_checksum": "sha256:abcd",
        "payload_redacted": {"truth_object_id": "to-123", "status": "valid"},
    }

    errors = sorted(validator.iter_errors(event_v11), key=lambda e: e.path)
    assert not errors, f"Expected v1.1 event to be backward compatible, got: {[e.message for e in errors]}"
