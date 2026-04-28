"""Golden-trace eval for schedule_meeting skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "schedule_meeting_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestScheduleMeetingContract:
    """Validate schedule_meeting fixture structure."""

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "title" in trace["input"], f"Trace {trace['id']} missing 'title'"
            assert "attendees" in trace["input"], (
                f"Trace {trace['id']} missing 'attendees'"
            )

    def test_attendees_not_empty(self) -> None:
        """Attendees must not be empty."""
        traces = load_traces()
        for trace in traces:
            attendees = trace["input"]["attendees"]
            assert isinstance(attendees, list) and len(attendees) > 0, (
                f"Trace {trace['id']}: attendees must be non-empty list"
            )

    def test_duration_in_range(self) -> None:
        """Duration must be between 15 and 240 minutes."""
        traces = load_traces()
        for trace in traces:
            duration = trace["input"].get("duration_minutes", 30)
            assert 15 <= duration <= 240, (
                f"Trace {trace['id']}: duration {duration} out of range"
            )
