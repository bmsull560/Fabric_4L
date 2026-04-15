"""Energy & Utilities Value Pack - Formula Execution Tests

Validates formula expressions and variable references.
"""

import json
import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestFormulaExpressions:
    """Verify formula expressions are valid."""

    @pytest.fixture(scope="class")
    def formulas_data(self):
        """Load formulas data."""
        with open(PACK_DIR / "formulas.json") as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def variables_data(self):
        """Load variables data."""
        with open(PACK_DIR / "variables.json") as f:
            return json.load(f)

    def test_all_formulas_have_expression(self, formulas_data):
        """Each formula must have an expression."""
        for formula in formulas_data["formulas"]:
            assert "expression" in formula, f"Formula {formula['formula_id']} missing expression"
            assert "string" in formula["expression"], f"Formula {formula['formula_id']} missing expression string"

    def test_formula_expressions_use_valid_variables(self, formulas_data, variables_data):
        """Formula expressions must reference valid variables."""
        valid_vars = {v["variable_name"] for v in variables_data["variables"]}
        
        for formula in formulas_data["formulas"]:
            expr = formula["expression"]
            if "variables" in expr:
                for var in expr["variables"]:
                    assert var in valid_vars, f"Formula {formula['formula_id']} references unknown variable: {var}"

    def test_formula_required_variables_exist(self, formulas_data, variables_data):
        """Formula required_variables must exist in variables.json."""
        valid_vars = {v["variable_name"] for v in variables_data["variables"]}
        
        for formula in formulas_data["formulas"]:
            if "required_variables" in formula:
                for req_var in formula["required_variables"]:
                    var_name = req_var.get("name")
                    assert var_name in valid_vars, f"Formula {formula['formula_id']} requires unknown variable: {var_name}"


class TestFormulaCalculations:
    """Verify formulas calculate correctly with default values."""

    def get_variable_defaults(self):
        """Build variable default value lookup."""
        with open(PACK_DIR / "variables.json") as f:
            data = json.load(f)
        return {v["variable_name"]: v.get("default_value", 0) for v in data["variables"]}

    def safe_evaluate(self, expression_str, variables):
        """Safely evaluate formula expression."""
        allowed_names = {
            "max": max, "min": min, "abs": abs,
            "sum": sum, "round": round, "pow": pow
        }
        allowed_names.update(variables)
        
        code = compile(expression_str, "<string>", "eval")
        for name in code.co_names:
            if name not in allowed_names:
                raise NameError(f"Use of {name} not allowed")
        return eval(code, {"__builtins__": {}}, allowed_names)

    def test_grid_modernization_roi_with_defaults(self):
        """Test grid modernization ROI with default values."""
        defaults = self.get_variable_defaults()
        
        # eu-f-001: (Outage_Cost_Savings + Operational_Savings + Deferred_Capex_Value - Annual_Smart_Grid_Cost) / Cumulative_Investment * 100
        total_benefit = (
            defaults.get("Outage_Cost_Savings", 0) +
            defaults.get("Operational_Savings", 0) +
            defaults.get("Deferred_Capex_Value", 0) -
            defaults.get("Annual_Smart_Grid_Cost", 0)
        )
        investment = defaults.get("Cumulative_Investment", 1)
        expected_roi = total_benefit / investment * 100
        
        variables = {
            "Outage_Cost_Savings": defaults.get("Outage_Cost_Savings", 0),
            "Operational_Savings": defaults.get("Operational_Savings", 0),
            "Deferred_Capex_Value": defaults.get("Deferred_Capex_Value", 0),
            "Annual_Smart_Grid_Cost": defaults.get("Annual_Smart_Grid_Cost", 0),
            "Cumulative_Investment": investment
        }
        
        result = self.safe_evaluate(
            "(Outage_Cost_Savings + Operational_Savings + Deferred_Capex_Value - Annual_Smart_Grid_Cost) / Cumulative_Investment * 100",
            variables
        )
        
        assert result == expected_roi
        assert result > 0  # Should be positive with default values

    def test_renewable_integration_value_with_defaults(self):
        """Test renewable integration value with default values."""
        defaults = self.get_variable_defaults()
        
        # eu-f-002: REC_Revenue + Carbon_Credit_Value + Fuel_Cost_Savings + Capacity_Payment_Avoidance - Integration_Costs
        total_revenue = (
            defaults.get("REC_Revenue", 0) +
            defaults.get("Carbon_Credit_Value", 0) +
            defaults.get("Fuel_Cost_Savings", 0) +
            defaults.get("Capacity_Payment_Avoidance", 0) -
            defaults.get("Integration_Costs", 0)
        )
        
        assert total_revenue > 0  # Should be positive with default values


class TestFormulaGovernance:
    """Verify formula governance metadata."""

    @pytest.fixture(scope="class")
    def formulas_data(self):
        """Load formulas data."""
        with open(PACK_DIR / "formulas.json") as f:
            return json.load(f)

    def test_all_formulas_have_governance(self, formulas_data):
        """Each formula should have governance info."""
        for formula in formulas_data["formulas"]:
            assert "governance" in formula, f"Formula {formula['formula_id']} missing governance"

    def test_governance_has_owner(self, formulas_data):
        """Governance should have an owner."""
        for formula in formulas_data["formulas"]:
            gov = formula.get("governance", {})
            assert "owner" in gov, f"Formula {formula['formula_id']} governance missing owner"

    def test_governance_has_approval_status(self, formulas_data):
        """Governance should have approval status."""
        valid_statuses = ["approved", "pending_review", "draft", "deprecated"]
        for formula in formulas_data["formulas"]:
            gov = formula.get("governance", {})
            assert "approval_status" in gov, f"Formula {formula['formula_id']} governance missing approval_status"
            assert gov["approval_status"] in valid_statuses, f"Invalid status: {gov['approval_status']}"

    def test_formula_versions_valid(self, formulas_data):
        """Formula versions must be valid semver."""
        import re
        semver_pattern = r'^\d+\.\d+\.\d+$'
        for formula in formulas_data["formulas"]:
            version = formula.get("version", "")
            assert re.match(semver_pattern, version), f"Invalid version: {version}"
