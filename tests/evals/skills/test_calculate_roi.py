"""Golden-trace eval for calculate_roi skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "calculate_roi_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestCalculateRoiContract:
    """Validate calculate_roi fixture structure and invariants."""

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "investment" in trace["input"], (
                f"Trace {trace['id']} missing 'investment'"
            )

    def test_investment_is_non_negative(self) -> None:
        """Investment must be >= 0."""
        traces = load_traces()
        for trace in traces:
            investment = trace["input"]["investment"]
            assert investment >= 0, (
                f"Trace {trace['id']}: investment {investment} must be >= 0"
            )

    def test_discount_rate_in_range(self) -> None:
        """Discount rate must be between 0 and 1."""
        traces = load_traces()
        for trace in traces:
            rate = trace["input"].get("discount_rate", 0.1)
            assert 0 <= rate <= 1, (
                f"Trace {trace['id']}: discount_rate {rate} out of range"
            )

    def test_time_periods_positive(self) -> None:
        """Time periods must be >= 1."""
        traces = load_traces()
        for trace in traces:
            periods = trace["input"].get("time_periods", 3)
            assert periods >= 1, (
                f"Trace {trace['id']}: time_periods {periods} must be >= 1"
            )

    def test_returns_are_numeric(self) -> None:
        """Returns must be numeric values."""
        traces = load_traces()
        for trace in traces:
            returns = trace["input"].get("returns", [])
            for i, ret in enumerate(returns):
                assert isinstance(ret, (int, float)), (
                    f"Trace {trace['id']}: return[{i}] must be numeric"
                )
