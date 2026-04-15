"""AI & Technology Value Pack - Formula Execution Tests"""

import json
import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestFormulaExpressions:
    """Verify formula expressions are valid."""

    @pytest.fixture(scope="class")
    def formulas_data(self):
        with open(PACK_DIR / "formulas.json") as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def variables_data(self):
        with open(PACK_DIR / "variables.json") as f:
            return json.load(f)

    def test_all_formulas_have_expression(self, formulas_data):
        for formula in formulas_data["formulas"]:
            assert "expression" in formula
            assert "string" in formula["expression"]

    def test_formula_expressions_use_valid_variables(self, formulas_data, variables_data):
        valid_vars = {v["variable_name"] for v in variables_data["variables"]}
        
        for formula in formulas_data["formulas"]:
            expr = formula["expression"]
            if "variables" in expr:
                for var in expr["variables"]:
                    assert var in valid_vars


class TestFormulaCalculations:
    """Verify formulas calculate correctly with default values."""

    def get_variable_defaults(self):
        with open(PACK_DIR / "variables.json") as f:
            data = json.load(f)
        return {v["variable_name"]: v.get("default_value", 0) for v in data["variables"]}

    def test_mlops_roi_positive(self):
        """MLOps ROI should be positive with defaults."""
        defaults = self.get_variable_defaults()
        
        total_benefit = (
            defaults.get("Inference_Cost_Savings", 0) +
            defaults.get("Drift_Reduction_Value", 0) +
            defaults.get("Velocity_Value", 0)
        )
        investment = defaults.get("MLOps_Investment", 1)
        roi = (total_benefit - investment) / investment * 100
        
        assert roi > 0


class TestFormulaGovernance:
    """Verify formula governance metadata."""

    @pytest.fixture(scope="class")
    def formulas_data(self):
        with open(PACK_DIR / "formulas.json") as f:
            return json.load(f)

    def test_all_formulas_have_governance(self, formulas_data):
        for formula in formulas_data["formulas"]:
            assert "governance" in formula

    def test_governance_has_owner(self, formulas_data):
        for formula in formulas_data["formulas"]:
            gov = formula.get("governance", {})
            assert "owner" in gov
