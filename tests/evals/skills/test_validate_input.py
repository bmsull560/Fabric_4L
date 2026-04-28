"""Golden-trace eval for validate_input skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "validate_input_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestValidateInputContract:
    """Validate validate_input fixture structure."""

    VALID_SCHEMAS = {"prospect_id", "value_drivers", "formula", "email"}

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "data" in trace["input"], f"Trace {trace['id']} missing 'data'"
            assert "schema_name" in trace["input"], (
                f"Trace {trace['id']} missing 'schema_name'"
            )

    def test_schema_name_is_valid(self) -> None:
        """Schema name must be a valid schema."""
        traces = load_traces()
        for trace in traces:
            schema = trace["input"]["schema_name"]
            assert schema in self.VALID_SCHEMAS, (
                f"Trace {trace['id']}: invalid schema_name '{schema}'"
            )

    def test_data_is_object(self) -> None:
        """Data must be a dict object."""
        traces = load_traces()
        for trace in traces:
            data = trace["input"]["data"]
            assert isinstance(data, dict), (
                f"Trace {trace['id']}: data must be a dict"
            )
