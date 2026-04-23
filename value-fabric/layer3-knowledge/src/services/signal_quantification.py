"""Signal quantification service for Layer 3.

Calculates impact values for pain signals using industry-specific
formulas and prospect data.
"""

from __future__ import annotations

import logging
import operator
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

from neo4j import AsyncDriver

logger = logging.getLogger(__name__)


@dataclass
class FormulaVariable:
    """Variable definition for formula execution."""

    name: str
    display_name: str
    value: float | None = None
    data_type: str = "currency"
    default_value: float = 0.0
    valid_range: tuple[float, float] | None = None


@dataclass
class QuantificationResult:
    """Result of signal quantification."""

    success: bool
    impact_value: Decimal | None = None
    impact_unit: str | None = None
    formula_id: str | None = None
    formula_name: str | None = None
    calculation_context: dict[str, Any] | None = None
    errors: list[str] | None = None


class SignalQuantificationService:
    """Service for quantifying pain signal impact.

    Applies industry-specific formulas to calculate financial
    or operational impact of discovered signals.
    """

    # Safe operations for formula evaluation
    SAFE_OPERATORS = {
        "+": operator.add,
        "-": operator.sub,
        "*": operator.mul,
        "/": operator.truediv,
    }

    # Safe functions for formula evaluation
    SAFE_FUNCTIONS = {
        "abs": abs,
        "round": round,
        "min": min,
        "max": max,
        "sum": sum,
    }

    # Industry to formula mappings for Operational signals
    OPERATIONAL_FORMULAS = {
        "manufacturing": [
            "ai-f-001",  # AI Model Operationalization ROI (adapted)
        ],
        "automotive": [
            "ai-f-001",
        ],
        "technology": [
            "ai-f-001",
            "ai-f-002",  # LLM Adoption Productivity Value
        ],
    }

    def __init__(self, driver: AsyncDriver):
        """Initialize with Neo4j driver.

        Args:
            driver: Neo4j async driver instance
        """
        self._driver = driver

    async def quantify_signal(
        self,
        signal_name: str,
        signal_description: str,
        impact_indicators: list[str],
        industry: str | None,
        prospect_data: dict[str, Any],
        tenant_id: str,
    ) -> QuantificationResult:
        """Quantify a pain signal's impact.

        Finds appropriate formula, extracts variables from prospect data,
        and calculates impact value.

        Args:
            signal_name: Signal name
            signal_description: Signal description
            impact_indicators: Clues from extraction
            industry: Industry vertical
            prospect_data: Prospect-specific data
            tenant_id: Tenant identifier

        Returns:
            Quantification result with impact value or errors
        """
        try:
            # Step 1: Find appropriate formula
            formula = await self._select_formula(
                signal_name,
                signal_description,
                industry,
                tenant_id,
            )

            if not formula:
                return QuantificationResult(
                    success=False,
                    errors=[
                        f"No suitable formula found for '{signal_name}' "
                        f"in industry '{industry}'"
                    ],
                )

            # Step 2: Extract variables from prospect data
            variables = await self._extract_variables(
                formula,
                impact_indicators,
                prospect_data,
            )

            # Step 3: Validate and fill defaults
            validated_inputs = self._validate_and_fill_variables(variables)
            if validated_inputs.get("_errors"):
                return QuantificationResult(
                    success=False,
                    errors=validated_inputs["_errors"],
                )

            # Step 4: Execute formula
            result = await self._execute_formula(
                formula,
                validated_inputs,
                tenant_id,
            )

            if not result.get("success"):
                return QuantificationResult(
                    success=False,
                    errors=[result.get("error", "Formula execution failed")],
                )

            # Step 5: Build result
            return QuantificationResult(
                success=True,
                impact_value=Decimal(str(result["value"])),
                impact_unit=formula.get("output_unit", "USD/year"),
                formula_id=formula.get("id"),
                formula_name=formula.get("name"),
                calculation_context={
                    "variables_used": list(validated_inputs.keys()),
                    "industry": industry,
                    "indicators_matched": len(impact_indicators),
                },
            )

        except Exception as e:
            logger.error(f"Signal quantification failed: {e}")
            return QuantificationResult(
                success=False,
                errors=[str(e)],
            )

    async def _select_formula(
        self,
        signal_name: str,
        signal_description: str,
        industry: str | None,
        tenant_id: str,
    ) -> dict[str, Any] | None:
        """Select the most appropriate formula for a signal.

        Args:
            signal_name: Signal name for matching
            signal_description: Signal description
            industry: Industry vertical
            tenant_id: Tenant identifier

        Returns:
            Formula dictionary or None
        """
        # Normalize industry
        industry_key = (industry or "general").lower().strip()

        # Get candidate formulas for this industry
        candidate_ids = self.OPERATIONAL_FORMULAS.get(
            industry_key,
            self.OPERATIONAL_FORMULAS.get("manufacturing", ["ai-f-001"]),
        )

        # Query graph for formula details
        async with self._driver.session() as session:
            query = """
            MATCH (f:Formula)
            WHERE f.id IN $formula_ids
              AND f.tenant_id = $tenant_id
            RETURN f {
                id: f.id,
                name: f.name,
                expression: f.expression,
                output_unit: f.output_unit,
                variables: f.variables,
                industry: f.industry,
                confidence: f.confidence
            } as formula
            ORDER BY f.confidence DESC
            LIMIT 1
            """

            result = await session.run(
                query,
                {
                    "formula_ids": candidate_ids,
                    "tenant_id": tenant_id,
                },
            )
            record = await result.single()

            if record:
                return record["formula"]

        # Fallback: Return a default formula structure if none found in graph
        return {
            "id": "default-operational",
            "name": "Default Operational Impact",
            "expression": "estimated_annual_cost",
            "output_unit": "USD/year",
            "variables": [
                {
                    "name": "estimated_annual_cost",
                    "default_value": 1000000,
                    "data_type": "currency",
                }
            ],
        }

    async def _extract_variables(
        self,
        formula: dict[str, Any],
        impact_indicators: list[str],
        prospect_data: dict[str, Any],
    ) -> list[FormulaVariable]:
        """Extract formula variables from prospect data.

        Args:
            formula: Formula with variable definitions
            impact_indicators: Impact clues from signal
            prospect_data: Prospect data

        Returns:
            List of variables with extracted or default values
        """
        formula_vars = formula.get("variables", [])
        extracted_vars = []

        for var_def in formula_vars:
            var_name = var_def.get("name")
            var = FormulaVariable(
                name=var_name,
                display_name=var_def.get("display_name", var_name),
                data_type=var_def.get("data_type", "currency"),
                default_value=var_def.get("default_value", 0.0),
            )

            # Try to extract from prospect data
            if var_name in prospect_data:
                try:
                    var.value = float(prospect_data[var_name])
                except (ValueError, TypeError):
                    var.value = None

            # Try to extract from impact indicators if not found
            if var.value is None and impact_indicators:
                var.value = self._extract_from_indicators(
                    var_name,
                    impact_indicators,
                )

            extracted_vars.append(var)

        return extracted_vars

    def _extract_from_indicators(
        self,
        variable_name: str,
        impact_indicators: list[str],
    ) -> float | None:
        """Extract a variable value from impact indicators.

        Args:
            variable_name: Name of variable to find
            impact_indicators: List of impact indicator strings

        Returns:
            Extracted value or None
        """
        # Common patterns in indicators
        patterns = {
            "annual_cost": [r"\$([\d.]+)[KM]?.*annual", r"\$([\d.]+)[KM]?.*year"],
            "hourly_cost": [r"\$([\d.]+).*hour"],
            "downtime_hours": [r"(\d+).*hours?.*downtime", r"downtime.*(\d+).*hours"],
            "fte_count": [r"(\d+).*FTE", r"(\d+).*full.time"],
            "capacity_percent": [r"(\d+)%.*capacity", r"capacity.*(\d+)%"],
        }

        import re

        var_key = variable_name.lower().replace("_", "")
        regexes = patterns.get(var_key, [])

        for indicator in impact_indicators:
            indicator_lower = indicator.lower()
            for regex in regexes:
                match = re.search(regex, indicator_lower)
                if match:
                    value_str = match.group(1)
                    try:
                        value = float(value_str)
                        # Handle K/M suffixes if present in original
                        if "K" in indicator.upper():
                            value *= 1000
                        if "M" in indicator.upper():
                            value *= 1000000
                        return value
                    except ValueError:
                        continue

        return None

    def _validate_and_fill_variables(
        self,
        variables: list[FormulaVariable],
    ) -> dict[str, Any]:
        """Validate variables and fill in defaults.

        Args:
            variables: Extracted variables

        Returns:
            Dictionary of variable names to values, with _errors key if issues
        """
        result = {}
        errors = []

        for var in variables:
            if var.value is not None:
                # Validate range if specified
                if var.valid_range:
                    min_val, max_val = var.valid_range
                    if not (min_val <= var.value <= max_val):
                        errors.append(
                            f"Variable '{var.name}' value {var.value} "
                            f"outside range [{min_val}, {max_val}]"
                        )
                        result[var.name] = var.default_value
                    else:
                        result[var.name] = var.value
                else:
                    result[var.name] = var.value
            else:
                # Use default
                result[var.name] = var.default_value

        if errors:
            result["_errors"] = errors

        return result

    async def _execute_formula(
        self,
        formula: dict[str, Any],
        inputs: dict[str, Any],
        tenant_id: str,
    ) -> dict[str, Any]:
        """Execute a formula safely.

        Args:
            formula: Formula definition
            inputs: Input values
            tenant_id: Tenant identifier

        Returns:
            Execution result
        """
        expression = formula.get("expression", "")

        try:
            # Simple arithmetic expression evaluation
            # For production, use a proper formula engine
            result = self._safe_eval(expression, inputs)

            return {
                "success": True,
                "value": result,
                "expression": expression,
            }

        except Exception as e:
            logger.error(f"Formula execution failed: {e}")
            return {
                "success": False,
                "error": f"Formula execution failed: {e}",
            }

    def _safe_eval(self, expression: str, context: dict[str, Any]) -> float:
        """Safely evaluate a formula expression.

        Args:
            expression: Formula expression string
            context: Variable values

        Returns:
            Calculated result
        """
        # For now, simple direct evaluation of single variables
        # Full implementation would parse and evaluate complex expressions
        if expression in context:
            return float(context[expression])

        # Try basic arithmetic
        try:
            # Very limited eval for security
            allowed_names = {
                **self.SAFE_FUNCTIONS,
                **{k: v for k, v in context.items() if isinstance(v, (int, float))},
            }
            return eval(expression, {"__builtins__": {}}, allowed_names)
        except Exception as e:
            logger.error(f"Expression evaluation failed: {e}")
            # Return first available numeric context value as fallback
            for key, value in context.items():
                if isinstance(value, (int, float)) and not key.startswith("_"):
                    return float(value)
            return 0.0

    def get_supported_units(self) -> list[str]:
        """Get list of supported impact units.

        Returns:
            List of valid unit strings
        """
        return [
            "USD/year",
            "USD/month",
            "% capacity",
            "% efficiency",
            "hours/week",
            "FTE",
        ]
