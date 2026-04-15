"""Retail & Consumer Value Pack - Formula Execution Tests"""

from typing import Any

import pytest


class TestFormulaExpressions:
    """Verify formula expressions are valid."""

    def test_all_formulas_have_expression(self, formulas_data: dict[str, Any]) -> None:
        for formula in formulas_data["formulas"]:
            assert "expression" in formula, f"Formula {formula.get('formula_id', 'unknown')} missing expression"
            assert "string" in formula["expression"], f"Formula {formula.get('formula_id', 'unknown')} missing expression.string"

    def test_formula_expressions_use_valid_variables(
        self, formulas_data: dict[str, Any], variables_data: dict[str, Any]
    ) -> None:
        valid_vars = {v["variable_name"] for v in variables_data["variables"]}

        for formula in formulas_data["formulas"]:
            expr = formula["expression"]
            if "variables" in expr:
                for var in expr["variables"]:
                    assert var in valid_vars, f"Formula {formula.get('formula_id', 'unknown')} uses unknown variable: {var}"


class TestFormulaCalculations:
    """Verify formulas calculate correctly with default values."""

    @pytest.fixture
    def variable_defaults(self, variables_data: dict[str, Any]) -> dict[str, Any]:
        """Return variable default values as a dictionary."""
        return {v["variable_name"]: v.get("default_value", 0) for v in variables_data["variables"]}

    def test_omnichannel_roi_positive(self, variable_defaults: dict[str, Any]) -> None:
        """Omnichannel ROI should be positive with defaults."""
        net_benefit = (
            variable_defaults.get("Incremental_Revenue", 0) +
            variable_defaults.get("Cost_Avoidance", 0) -
            variable_defaults.get("Fulfillment_Cost_Inflation", 0)
        )
        investment = variable_defaults.get("Omnichannel_Investment", 1)
        roi = net_benefit / investment * 100

        assert roi > 0, f"Omnichannel ROI is not positive: {roi}"


class TestFormulaGovernance:
    """Verify formula governance metadata."""

    def test_all_formulas_have_governance(self, formulas_data: dict[str, Any]) -> None:
        for formula in formulas_data["formulas"]:
            assert "governance" in formula, f"Formula {formula.get('formula_id', 'unknown')} missing governance"

    def test_governance_has_owner(self, formulas_data: dict[str, Any]) -> None:
        for formula in formulas_data["formulas"]:
            gov = formula.get("governance", {})
            assert "owner" in gov, f"Formula {formula.get('formula_id', 'unknown')} governance missing owner"
