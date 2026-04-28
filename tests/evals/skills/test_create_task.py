"""Golden-trace eval for create_task skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "create_task_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestCreateTaskContract:
    """Validate create_task fixture structure."""

    VALID_PRIORITIES = {"low", "medium", "high"}

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "title" in trace["input"], f"Trace {trace['id']} missing 'title'"
            assert "description" in trace["input"], (
                f"Trace {trace['id']} missing 'description'"
            )

    def test_title_not_empty(self) -> None:
        """Title must not be empty."""
        traces = load_traces()
        for trace in traces:
            assert trace["input"]["title"], (
                f"Trace {trace['id']}: title must not be empty"
            )

    def test_priority_valid(self) -> None:
        """Priority must be low, medium, or high."""
        traces = load_traces()
        for trace in traces:
            priority = trace["input"].get("priority", "medium")
            assert priority in self.VALID_PRIORITIES, (
                f"Trace {trace['id']}: invalid priority '{priority}'"
            )
