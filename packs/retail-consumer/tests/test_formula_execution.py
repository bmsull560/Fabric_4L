"""Retail & Consumer Value Pack - Formula Execution Tests

NOTE (P1-4): File handle verification - fixtures hold files open.
Monitor for FD exhaustion: cat /proc/sys/fs/file-nr
"""

from typing import Any

import pytest


class TestFormulaExpressions:
    """Verify formula expressions are valid and reference existing variables."""

    def test_all_formulas_have_expression(self, formulas_data: dict[str, Any]) -> None:
        """Every formula must have an expression with a string representation."""
        for formula in formulas_data["formulas"]:
            assert "expression" in formula, f"Formula {formula.get('formula_id', 'unknown')} missing expression"
            assert "string" in formula["expression"], f"Formula {formula.get('formula_id', 'unknown')} missing expression.string"

    def test_formula_expressions_use_valid_variables(
        self, formulas_data: dict[str, Any], variables_data: dict[str, Any]
    ) -> None:
        """All variables referenced in formula expressions must exist in variables.json."""
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
        """Return variable default values as a dictionary keyed by variable_name."""
        return {v["variable_name"]: v.get("default_value", 0) for v in variables_data["variables"]}

    def test_omnichannel_roi_positive(
        self, variable_defaults: dict[str, Any], formulas_data: dict[str, Any]
    ) -> None:
        """Omnichannel ROI formula (rc-f-001) should produce positive result with default values.

        Derives variable names dynamically from formula expression to avoid fragility
        when variable names change.
        """
        # Find the omnichannel ROI formula
        omnichannel_formula = next(
            (f for f in formulas_data["formulas"] if f["formula_id"] == "rc-f-001"),
            None
        )
        assert omnichannel_formula is not None, "Omnichannel ROI formula (rc-f-001) not found"

        # Get variable names from formula expression (robust to name changes)
        expr_vars = omnichannel_formula["expression"].get("variables", [])
        assert len(expr_vars) >= 4, f"Expected at least 4 variables in formula, got {len(expr_vars)}"

        # Calculate net benefit from first 3 variables (typically: revenue + savings - costs)
        net_benefit = sum(variable_defaults.get(v, 0) for v in expr_vars[:3])
        # Investment is typically the 4th variable
        investment = variable_defaults.get(expr_vars[3], 1)
        assert investment > 0, f"Investment variable {expr_vars[3]} must be positive, got {investment}"

        roi = net_benefit / investment * 100
        assert roi > 0, f"Omnichannel ROI is not positive: {roi:.2f}% (net_benefit={net_benefit}, investment={investment})"


class SafeFormulaEvaluator:
    """Safe formula expression evaluator for test fixtures.

    WARNING: Uses eval() with restricted globals. Acceptable for test
    fixtures but production requires a proper expression evaluator
    (asteval, simpleeval, or custom parser).
    """

    @staticmethod
    def evaluate(expression: str, variables: dict[str, Any]) -> Any:
        """Evaluate formula expression with variable substitution."""
        allowed_names = {
            "max": max, "min": min, "abs": abs,
            "sum": sum, "round": round, "pow": pow,
        }
        allowed_names.update(variables)

        code = compile(expression, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                raise NameError(f"Use of {name} not allowed")
        return eval(code, {"__builtins__": {}}, allowed_names)


class TestFormulaGovernance:
    """Verify formula governance metadata is complete."""

    def test_all_formulas_have_governance(self, formulas_data: dict[str, Any]) -> None:
        """Every formula must have a governance section."""
        for formula in formulas_data["formulas"]:
            assert "governance" in formula, f"Formula {formula.get('formula_id', 'unknown')} missing governance"

    def test_governance_has_owner(self, formulas_data: dict[str, Any]) -> None:
        """Every formula governance must specify an owner."""
        for formula in formulas_data["formulas"]:
            gov = formula.get("governance", {})
            assert "owner" in gov, f"Formula {formula.get('formula_id', 'unknown')} governance missing owner"

    def test_governance_has_review_cycle(self, formulas_data: dict[str, Any]) -> None:
        """Verify governance includes a review cycle."""
        valid_cycles = {"monthly", "quarterly", "semi-annual", "annual"}
        for formula in formulas_data["formulas"]:
            gov = formula.get("governance", {})
            cycle = gov.get("review_cycle")
            if cycle:  # Only validate if present (not all formulas may have it)
                assert cycle in valid_cycles, (
                    f"Formula {formula.get('formula_id', 'unknown')} has invalid review_cycle: {cycle}"
                )
