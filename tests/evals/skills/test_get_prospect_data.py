"""Golden-trace eval for get_prospect_data skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "get_prospect_data_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestGetProspectDataContract:
    """Validate get_prospect_data fixture structure."""

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "prospect_id" in trace["input"], (
                f"Trace {trace['id']} missing 'prospect_id'"
            )

    def test_prospect_id_not_empty(self) -> None:
        """Prospect ID must not be empty."""
        traces = load_traces()
        for trace in traces:
            pid = trace["input"]["prospect_id"]
            assert pid and isinstance(pid, str), (
                f"Trace {trace['id']}: prospect_id must be non-empty string"
            )

    def test_data_types_valid(self) -> None:
        """Data types must be valid."""
        valid_types = {"profile", "interactions", "opportunities"}
        traces = load_traces()
        for trace in traces:
            types = trace["input"].get("data_types", [])
            invalid = set(types) - valid_types
            assert not invalid, (
                f"Trace {trace['id']}: invalid data_types {invalid}"
            )
