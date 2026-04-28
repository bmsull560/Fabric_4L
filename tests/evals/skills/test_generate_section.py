"""Golden-trace eval for generate_section skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "generate_section_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestGenerateSectionContract:
    """Validate generate_section fixture structure."""

    VALID_SECTION_TYPES = {
        "executive_summary", "current_state", "proposed_solution",
        "roi_analysis", "implementation", "next_steps"
    }

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "section_type" in trace["input"], (
                f"Trace {trace['id']} missing 'section_type'"
            )

    def test_section_type_is_valid(self) -> None:
        """Section type must be a valid type."""
        traces = load_traces()
        for trace in traces:
            section_type = trace["input"]["section_type"]
            assert section_type in self.VALID_SECTION_TYPES, (
                f"Trace {trace['id']}: invalid section_type '{section_type}'"
            )

    def test_max_length_in_range(self) -> None:
        """Max length must be between 100 and 2000."""
        traces = load_traces()
        for trace in traces:
            max_len = trace["input"].get("max_length", 500)
            assert 100 <= max_len <= 2000, (
                f"Trace {trace['id']}: max_length {max_len} out of range"
            )

    def test_tone_is_valid(self) -> None:
        """Tone should be a string."""
        traces = load_traces()
        for trace in traces:
            tone = trace["input"].get("tone", "professional")
            assert isinstance(tone, str), (
                f"Trace {trace['id']}: tone must be a string"
            )
