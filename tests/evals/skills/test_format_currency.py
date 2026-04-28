"""Golden-trace eval for format_currency skill."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "fixtures"


def load_traces() -> list[dict[str, Any]]:
    path = FIXTURES_DIR / "format_currency_traces.json"
    with open(path) as f:
        data = json.load(f)
    return data["traces"]


class TestFormatCurrencyContract:
    """Validate format_currency fixture structure."""

    VALID_CURRENCIES = {"USD", "EUR", "GBP", "JPY", "CAD", "AUD"}

    def test_fixture_has_required_fields(self) -> None:
        traces = load_traces()
        assert traces, "Fixture must have at least one trace"
        for trace in traces:
            assert "id" in trace
            assert "input" in trace
            assert "amount" in trace["input"], (
                f"Trace {trace['id']} missing 'amount'"
            )

    def test_amount_is_numeric(self) -> None:
        """Amount must be a number."""
        traces = load_traces()
        for trace in traces:
            amount = trace["input"]["amount"]
            assert isinstance(amount, (int, float)), (
                f"Trace {trace['id']}: amount must be numeric"
            )

    def test_currency_is_valid(self) -> None:
        """Currency must be a valid code."""
        traces = load_traces()
        for trace in traces:
            currency = trace["input"].get("currency", "USD").upper()
            assert currency in self.VALID_CURRENCIES, (
                f"Trace {trace['id']}: invalid currency '{currency}'"
            )

    def test_decimals_non_negative(self) -> None:
        """Decimals must be >= 0."""
        traces = load_traces()
        for trace in traces:
            decimals = trace["input"].get("decimals", 0)
            assert decimals >= 0, (
                f"Trace {trace['id']}: decimals {decimals} must be >= 0"
            )
