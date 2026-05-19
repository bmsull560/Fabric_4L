"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Scenario Engine for What-If Analysis
Handles sensitivity analysis and scenario comparison for business cases.
"""

import logging
from dataclasses import dataclass
from typing import Any

from value_fabric.shared.models.typed_dict import TypedDictModel


class ScenarioEngine_compare_scenariosResult(TypedDictModel):
    base_payback: Any
    base_roi: Any
    base_value: Any
    best_scenario: Any
    comparison: Any
    worst_scenario: Any

logger = logging.getLogger(__name__)


@dataclass
class VariableAdjustment:
    """Single variable adjustment for scenario analysis."""

    name: str
    value: float
    original_value: float


@dataclass
class ScenarioResult:
    """Result of scenario calculation."""

    scenario_id: str
    original_value: float
    adjusted_value: float
    delta_percentage: float
    new_roi: float
    new_payback_months: float
    formula_used: str
    calculation_steps: list[dict[str, Any]]


@dataclass
class SavedScenario:
    """Stored scenario for comparison."""

    id: str
    name: str
    base_case_id: str
    adjustments: list[VariableAdjustment]
    created_at: str
    calculated_metrics: dict[str, float] | None = None


class ScenarioEngine:
    """Engine for calculating what-if scenarios on business cases."""

    # Formula expressions for key metrics
    ROI_FORMULA = "(total_value - implementation_cost) / implementation_cost"
    PAYBACK_FORMULA = "implementation_cost / (total_value / 12)"  # months

    # Adjustment calculation constants
    TIMELINE_COST_PER_MONTH = 10_000  # $10k/month overhead assumption
    ANNUAL_SAVINGS_HORIZON_YEARS = 3  # 3-year horizon for savings calculations
    MAX_PAYBACK_MONTHS = 999.0  # Represents "never pays back"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def calculate_scenario(
        self,
        base_case_data: dict[str, Any],
        adjustments: list[VariableAdjustment],
        scenario_id: str | None = None,
    ) -> ScenarioResult:
        """Calculate new metrics based on variable adjustments.

        Args:
            base_case_data: Original business case data including
                total_value, implementation_cost, roi_ratio, payback_months
            adjustments: List of variable adjustments to apply
            scenario_id: Optional identifier for the scenario

        Returns:
            ScenarioResult with calculated deltas and new metrics
        """
        # Extract base values (roi_ratio and payback_months are derived, not needed for calculation)
        original_value = base_case_data.get("total_value", 0.0)
        impl_cost = base_case_data.get("implementation_cost", 0.0)

        # Apply adjustments to calculate new value
        adjusted_value = self._apply_adjustments(original_value, impl_cost, adjustments)

        # Calculate new metrics
        new_roi = self._calculate_roi(adjusted_value, impl_cost)
        new_payback = self._calculate_payback(adjusted_value, impl_cost)

        # Calculate deltas
        value_delta = adjusted_value - original_value
        delta_percentage = (
            (value_delta / original_value * 100) if original_value else 0.0
        )

        # Build calculation steps for transparency
        steps = self._build_calculation_steps(
            original_value, adjusted_value, impl_cost, adjustments
        )

        # Generate deterministic scenario ID if not provided
        if not scenario_id:
            # Create hash from sorted adjustments for determinism
            adjustment_key = "|".join(
                f"{adj.name}:{adj.value}:{adj.original_value}"
                for adj in sorted(adjustments, key=lambda x: x.name)
            )
            scenario_id = f"scenario_{hash(adjustment_key) & 0xFFFFFFFF:08x}"

        return ScenarioResult(
            scenario_id=scenario_id,
            original_value=original_value,
            adjusted_value=adjusted_value,
            delta_percentage=delta_percentage,
            new_roi=new_roi,
            new_payback_months=new_payback,
            formula_used=self.ROI_FORMULA,
            calculation_steps=steps,
        )

    def compare_scenarios(
        self,
        base_case_data: dict[str, Any],
        scenarios: list[SavedScenario],
    ) -> dict[str, Any]:
        """Compare multiple scenarios side-by-side.

        Args:
            base_case_data: Original business case data
            scenarios: List of saved scenarios to compare

        Returns:
            Comparison data with deltas and rankings
        """
        results = []

        for scenario in scenarios:
            result = self.calculate_scenario(
                base_case_data,
                scenario.adjustments,
                scenario.id,
            )
            results.append(
                {
                    "scenario_id": result.scenario_id,
                    "name": scenario.name,
                    "adjusted_value": result.adjusted_value,
                    "delta_percentage": result.delta_percentage,
                    "new_roi": result.new_roi,
                    "new_payback_months": result.new_payback_months,
                }
            )

        # Sort by adjusted value (descending)
        results.sort(key=lambda x: x["adjusted_value"], reverse=True)

        return ScenarioEngine_compare_scenariosResult.model_validate({
            "comparison": results,
            "base_value": base_case_data.get("total_value", 0.0),
            "base_roi": base_case_data.get("roi_ratio", 0.0),
            "base_payback": base_case_data.get("payback_months", 0.0),
            "best_scenario": results[0] if results else None,
            "worst_scenario": results[-1] if len(results) > 1 else None,
        })


    def sensitivity_analysis(
        self,
        base_case_data: dict[str, Any],
        variable_name: str,
        range_percentages: list[float],
    ) -> list[ScenarioResult]:
        """Run sensitivity analysis on a single variable.

        Args:
            base_case_data: Original business case data
            variable_name: Variable to test (e.g., 'implementation_cost')
            range_percentages: List of percentage adjustments (e.g., [-20, -10, 0, 10, 20])

        Returns:
            List of scenario results for each percentage point
        """
        original_value = base_case_data.get("total_value", 0.0)
        results = []

        for pct in range_percentages:
            # Calculate adjusted value based on percentage
            adjusted_value = original_value * (1 + pct / 100)

            adjustment = VariableAdjustment(
                name=variable_name,
                value=adjusted_value,
                original_value=original_value,
            )

            result = self.calculate_scenario(
                base_case_data,
                [adjustment],
                f"sensitivity_{variable_name}_{pct}",
            )
            results.append(result)

        return results

    def _apply_adjustments(
        self,
        original_value: float,
        impl_cost: float,
        adjustments: list[VariableAdjustment],
    ) -> float:
        """Apply variable adjustments to calculate new total value."""
        adjusted_value = original_value

        for adj in adjustments:
            if adj.name == "total_value":
                adjusted_value = adj.value
            elif adj.name == "implementation_cost":
                # Adjusting cost affects value calculation
                cost_delta = adj.value - impl_cost
                adjusted_value -= cost_delta  # Higher cost = lower net value
            elif adj.name == "annual_savings":
                # Annual savings flows into total value over defined horizon
                savings_delta = (
                    adj.value - adj.original_value
                ) * self.ANNUAL_SAVINGS_HORIZON_YEARS
                adjusted_value += savings_delta
            elif adj.name == "timeline_months":
                # Timeline affects cost based on per-month overhead assumption
                month_delta = adj.value - adj.original_value
                cost_impact = month_delta * self.TIMELINE_COST_PER_MONTH
                adjusted_value -= cost_impact
            else:
                # Generic percentage adjustment
                if adj.original_value != 0:
                    pct_change = (adj.value - adj.original_value) / adj.original_value
                    adjusted_value *= 1 + pct_change

        return max(0.0, adjusted_value)  # Value can't be negative

    def _calculate_roi(self, total_value: float, impl_cost: float) -> float:
        """Calculate ROI ratio."""
        if impl_cost <= 0:
            return 0.0
        return (total_value - impl_cost) / impl_cost

    def _calculate_payback(self, total_value: float, impl_cost: float) -> float:
        """Calculate payback period in months."""
        if total_value <= 0:
            return self.MAX_PAYBACK_MONTHS  # Never pays back
        monthly_benefit = total_value / 12  # Assuming annual value
        if monthly_benefit <= 0:
            return self.MAX_PAYBACK_MONTHS
        return impl_cost / monthly_benefit

    def _build_calculation_steps(
        self,
        original_value: float,
        adjusted_value: float,
        impl_cost: float,
        adjustments: list[VariableAdjustment],
    ) -> list[dict[str, Any]]:
        """Build human-readable calculation steps."""
        steps = []

        # Step 1: Show base values
        steps.append(
            {
                "step": 1,
                "operation": "Base case values",
                "details": {
                    "total_value": original_value,
                    "implementation_cost": impl_cost,
                },
            }
        )

        # Step 2: Show adjustments
        for i, adj in enumerate(adjustments, start=2):
            steps.append(
                {
                    "step": i,
                    "operation": f"Adjust {adj.name}",
                    "details": {
                        "from": adj.original_value,
                        "to": adj.value,
                        "change": adj.value - adj.original_value,
                    },
                }
            )

        # Final step: Show result
        steps.append(
            {
                "step": len(adjustments) + 2,
                "operation": "Calculate new metrics",
                "details": {
                    "adjusted_total_value": adjusted_value,
                    "new_roi": self._calculate_roi(adjusted_value, impl_cost),
                    "new_payback_months": self._calculate_payback(
                        adjusted_value, impl_cost
                    ),
                },
            }
        )

        return steps


# Singleton instance
scenario_engine = ScenarioEngine()
