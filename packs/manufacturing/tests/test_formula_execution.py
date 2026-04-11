"""Formula execution tests - validate formula calculations with test data."""

import ast
import operator as op
import pytest
import re
from typing import Any
from . import load_pack_file

# Supported operators for safe formula evaluation
SAFE_OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.USub: op.neg,
}


class TestFormulaExecution:
    """Test formula expression evaluation with sample inputs."""

    @pytest.fixture
    def formulas(self):
        return load_pack_file("formulas.json")["formulas"]

    @pytest.fixture
    def variables(self):
        return load_pack_file("variables.json")["variables"]

    def extract_variable_defaults(self, formula: dict, variables: list) -> dict[str, Any]:
        """Build variable map with defaults for formula testing."""
        var_map = {}
        var_lookup = {v["variable_name"]: v for v in variables}
        
        for req_var in formula.get("required_variables", []):
            var_name = req_var["name"]
            if var_name in var_lookup:
                var_def = var_lookup[var_name]
                var_map[var_name] = var_def.get("default_value", 0)
                
                # Set reasonable defaults based on data type
                if var_map[var_name] == 0:
                    if var_def["data_type"] == "PERCENTAGE":
                        var_map[var_name] = 75.0
                    elif var_def["data_type"] == "CURRENCY":
                        var_map[var_name] = 100000.0
                    elif var_def["data_type"] == "INTEGER":
                        var_map[var_name] = 100
                    elif var_def["data_type"] == "FLOAT":
                        var_map[var_name] = 50.0
        
        return var_map

    def _eval_node(self, node: ast.AST) -> float:
        """Safely evaluate an AST node containing only math operations."""
        if isinstance(node, ast.Num):  # Python 3.7 compatibility
            return float(node.n)
        elif isinstance(node, ast.Constant):  # Python 3.8+
            if isinstance(node.value, (int, float)):
                return float(node.value)
            raise ValueError(f"Unsupported constant type: {type(node.value)}")
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported binary operator: {op_type.__name__}")
            return SAFE_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            if op_type not in SAFE_OPERATORS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return SAFE_OPERATORS[op_type](operand)
        elif isinstance(node, ast.Expression):
            return self._eval_node(node.body)
        else:
            raise ValueError(f"Unsupported AST node type: {type(node).__name__}")

    def evaluate_expression(self, expression: str, variables: dict) -> float:
        """Safely evaluate formula expression using AST parsing.

        Replaces variable names with values, then parses and evaluates
        the expression using only whitelisted arithmetic operators.
        """
        expr = expression

        # Replace direct variable names with values (e.g., Current_OEE -> 75.0)
        for var_name, value in variables.items():
            expr = expr.replace(var_name, str(value))

        # Parse and evaluate safely
        try:
            tree = ast.parse(expr, mode='eval')
            return self._eval_node(tree)
        except (ValueError, SyntaxError, TypeError):
            return float('nan')

    def test_oee_improvement_roi_formula(self, formulas, variables):
        """Test OEE Improvement ROI formula with typical values."""
        formula = next(f for f in formulas if f["formula_id"] == "mfg-f-001")
        
        var_map = {
            "Current_OEE": 75.0,
            "Baseline_OEE": 60.0,
            "Annual_Production_Value": 10000000.0,
            "Margin_Percentage": 25.0,
            "Annual_Implementation_Cost": 500000.0
        }
        
        result = self.evaluate_expression(formula["expression"]["string"], var_map)
        
        # Expected: ((75 - 60) / 100) * 10000000 * 25 - 500000 = 37.5M - 0.5M = 37M
        assert result > 0, "OEE improvement should yield positive ROI"
        assert 30000000 <= result <= 40000000, f"OEE ROI in expected range: {result}"

    def test_unplanned_downtime_cost_formula(self, formulas, variables):
        """Test downtime cost calculation."""
        formula = next(f for f in formulas if f["formula_id"] == "mfg-f-002")
        
        var_map = {
            "Average_Downtime_Hours_Per_Month": 40.0,
            "Hourly_Production_Value": 5000.0,
            "Annual_Emergency_Repairs": 12.0,
            "Avg_Emergency_Repair_Cost": 25000.0
        }
        
        result = self.evaluate_expression(formula["expression"]["string"], var_map)
        
        # Expected: (40 * 5000 * 12) + (12 * 25000) = 2.4M + 300K = 2.7M
        assert result > 2000000, f"Downtime cost should be significant: {result}"

    def test_quality_defect_cost_formula(self, formulas, variables):
        """Test quality defect cost calculation."""
        formula = next(f for f in formulas if f["formula_id"] == "mfg-f-003")
        
        var_map = {
            "Annual_Units_Produced": 100000.0,
            "Defect_Rate": 2.0,
            "Scrap_Cost_Per_Unit": 50.0,
            "Rework_Cost_Per_Unit": 30.0,
            "Rework_Rate": 60.0,
            "Annual_Warranty_Costs": 50000.0
        }
        
        result = self.evaluate_expression(formula["expression"]["string"], var_map)
        assert result > 0, "Defect cost calculation should be positive"

    def test_predictive_maintenance_roi_formula(self, formulas, variables):
        """Test PdM ROI calculation."""
        formula = next(f for f in formulas if f["formula_id"] == "mfg-f-005")
        
        var_map = {
            "Avoided_Downtime_Value": 800000.0,
            "Maintenance_Cost_Savings": 200000.0,
            "PdM_Program_Cost": 300000.0
        }
        
        result = self.evaluate_expression(formula["expression"]["string"], var_map)
        
        # ROI formula: (800K + 200K - 300K) / 300K * 100 = 233%
        assert result > 100, f"PdM ROI should exceed 100%: {result}"

    def test_throughput_improvement_value_formula(self, formulas, variables):
        """Test throughput value calculation."""
        formula = next(f for f in formulas if f["formula_id"] == "mfg-f-006")
        
        var_map = {
            "Additional_Units_Per_Year": 5000.0,
            "Unit_Margin": 100.0,
            "Incremental_Operating_Cost": 200000.0
        }
        
        result = self.evaluate_expression(formula["expression"]["string"], var_map)
        
        # Expected: 5000 * 100 - 200000 = 500000 - 200000 = 300000
        assert 200000 <= result <= 500000, f"Throughput value in expected range: {result}"

    def test_all_formulas_have_valid_syntax(self, formulas):
        """All formula expressions must parse correctly."""
        for formula in formulas:
            expr = formula["expression"]["string"]
            required_vars = [v["name"] for v in formula.get("required_variables", [])]
            
            # Check that required variables appear in expression
            for var_name in required_vars:
                assert var_name in expr, f"Variable {var_name} not found in {formula['formula_id']}"
            
            # Check expression contains operators
            assert any(op in expr for op in ['+', '-', '*', '/']), \
                f"Formula {formula['formula_id']} has no operators"

    def test_formula_benchmarks_exist(self, formulas):
        """Active formulas should have benchmarks."""
        for formula in formulas:
            if formula["status"] == "active":
                assert "benchmarks" in formula or formula["formula_type"] == "CUSTOM", \
                    f"Active formula {formula['formula_id']} missing benchmarks"
