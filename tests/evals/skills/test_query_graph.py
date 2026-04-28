"""Golden-trace eval for query_graph skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "query_graph_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestQueryGraphContract:
    """Validate query_graph fixture structure and invariants."""

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "cypher_query" in trace["input"], (
                f"Trace {trace['id']} missing 'cypher_query'"
            )

    def test_cypher_query_is_read_only(self) -> None:
        """Cypher queries must not contain write operations."""
        forbidden = {"CREATE", "DELETE", "DETACH", "SET", "MERGE", "REMOVE", "DROP", "CALL"}
        traces = load_traces()
        for trace in traces:
            query = trace["input"]["cypher_query"].upper()
            for keyword in forbidden:
                assert keyword not in query, (
                    f"Trace {trace['id']}: query contains forbidden keyword '{keyword}'"
                )

    def test_parameters_is_object(self) -> None:
        """Parameters must be a dict object."""
        traces = load_traces()
        for trace in traces:
            params = trace["input"].get("parameters", {})
            assert isinstance(params, dict), (
                f"Trace {trace['id']}: parameters must be a dict"
            )

    def test_output_has_required_fields(self) -> None:
        """Output assertions must contain required fields."""
        traces = load_traces()
        for trace in traces:
            if "assertions" in trace:
                output = trace["assertions"]
                assert "results" in output or "row_count" in output, (
                    f"Trace {trace['id']}: output must have 'results' or 'row_count'"
                )
