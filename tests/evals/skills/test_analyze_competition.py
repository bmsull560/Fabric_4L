"""Golden-trace eval for analyze_competition skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "analyze_competition_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestAnalyzeCompetitionContract:
    """Validate analyze_competition fixture structure."""

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            required = ["context_artifact_id", "tenant_id", "workspace_id"]
            for field in required:
                assert field in trace["input"], (
                    f"Trace {trace['id']} missing '{field}'"
                )

    def test_ids_are_non_empty_strings(self) -> None:
        """Required IDs must be non-empty strings."""
        traces = load_traces()
        for trace in traces:
            for field in ["context_artifact_id", "tenant_id", "workspace_id"]:
                value = trace["input"][field]
                assert value and isinstance(value, str), (
                    f"Trace {trace['id']}: {field} must be non-empty string"
                )

    def test_known_competitors_is_list(self) -> None:
        """Known competitors must be a list."""
        traces = load_traces()
        for trace in traces:
            competitors = trace["input"].get("known_competitors", [])
            assert isinstance(competitors, list), (
                f"Trace {trace['id']}: known_competitors must be a list"
            )
