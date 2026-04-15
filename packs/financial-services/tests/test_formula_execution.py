"""Financial Services Value Pack - Formula Execution Tests

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
        # Simple evaluation for basic arithmetic
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

    def test_roi_formula_calculation(self):
        """Test basic ROI calculation."""
        # ROI = (benefit - cost) / cost * 100
        benefit = 1000000
        cost = 500000
        expected_roi = (benefit - cost) / cost * 100
        
        variables = {"annual_benefit": benefit, "annual_cost": 0, "implementation_cost": cost}
        result = self.safe_evaluate("(annual_benefit - annual_cost) / implementation_cost * 100", variables)
        assert result == expected_roi

    def test_fraud_detection_roi_with_defaults(self):
        """Test fraud detection ROI with default values."""
        defaults = self.get_variable_defaults()
        
        # fs-f-001: (Avoided_Fraud_Losses + False_Positive_Savings + Operational_Savings - AI_Platform_Cost) / AI_Platform_Cost * 100
        total_benefit = (
            defaults.get("Avoided_Fraud_Losses", 0) +
            defaults.get("False_Positive_Savings", 0) +
            defaults.get("Operational_Savings", 0)
        )
        investment = defaults.get("AI_Platform_Cost", 1)
        
        expected_roi = (total_benefit - investment) / investment * 100
        
        variables = {
            "Avoided_Fraud_Losses": defaults.get("Avoided_Fraud_Losses", 0),
            "False_Positive_Savings": defaults.get("False_Positive_Savings", 0),
            "Operational_Savings": defaults.get("Operational_Savings", 0),
            "AI_Platform_Cost": investment
        }
        
        result = self.safe_evaluate(
            "(Avoided_Fraud_Losses + False_Positive_Savings + Operational_Savings - AI_Platform_Cost) / AI_Platform_Cost * 100",
            variables
        )
        
        assert result == expected_roi
        assert result > 0  # Should be positive with default values

    def test_digital_onboarding_value_with_defaults(self):
        """Test digital onboarding value with default values."""
        defaults = self.get_variable_defaults()
        
        # fs-f-002: Additional_Customers_Acquired * First_Year_Revenue_Per_Customer + Operational_Savings - Digital_Onboarding_Investment
        revenue_value = (
            defaults.get("Additional_Customers_Acquired", 0) *
            defaults.get("First_Year_Revenue_Per_Customer", 0)
        )
        net_value = revenue_value + defaults.get("Operational_Savings", 0) - defaults.get("Digital_Onboarding_Investment", 0)
        
        assert net_value > 0  # Should be positive with default values


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
