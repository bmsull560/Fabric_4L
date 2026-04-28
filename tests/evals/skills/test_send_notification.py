"""Golden-trace eval for send_notification skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "send_notification_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestSendNotificationContract:
    """Validate send_notification fixture structure."""

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            required = ["channel", "recipients", "subject", "message"]
            for field in required:
                assert field in trace["input"], (
                    f"Trace {trace['id']} missing '{field}'"
                )

    def test_channel_is_valid(self) -> None:
        """Channel must be email, slack, or teams."""
        valid = {"email", "slack", "teams"}
        traces = load_traces()
        for trace in traces:
            channel = trace["input"]["channel"]
            assert channel in valid, (
                f"Trace {trace['id']}: invalid channel '{channel}'"
            )

    def test_recipients_not_empty(self) -> None:
        """Recipients must not be empty."""
        traces = load_traces()
        for trace in traces:
            recipients = trace["input"]["recipients"]
            assert isinstance(recipients, list) and len(recipients) > 0, (
                f"Trace {trace['id']}: recipients must be non-empty list"
            )

    def test_subject_and_message_not_empty(self) -> None:
        """Subject and message must not be empty."""
        traces = load_traces()
        for trace in traces:
            assert trace["input"]["subject"], (
                f"Trace {trace['id']}: subject must not be empty"
            )
            assert trace["input"]["message"], (
                f"Trace {trace['id']}: message must not be empty"
            )
