"""Software Value Pack - Formula Execution Tests

Validates formula calculations with test cases and boundary values.
"""

import json
import pytest
from pathlib import Path
from typing import Tuple

PACK_DIR = Path(__file__).parent.parent


# ============================================================================
# Formula Library - Centralized calculation logic
# ============================================================================

def calculate_cac_roi(
    current_cac: float,
    target_cac: float,
    new_customers: float,
    investment: float
) -> float:
    """Calculate Customer Acquisition Efficiency ROI (sw-f-001)."""
    savings = (current_cac - target_cac) * new_customers
    return (savings - investment) / investment * 100


def calculate_nrr_value(
    beginning_arr: float,
    current_nrr: float,
    target_nrr: float,
    cost: float
) -> float:
    """Calculate Net Revenue Retention Improvement Value (sw-f-002)."""
    return beginning_arr * (target_nrr - current_nrr) / 100 - cost


def calculate_churn_value(
    customers: float,
    current_churn: float,
    target_churn: float,
    acv: float,
    lifespan: float,
    program_cost: float
) -> float:
    """Calculate Churn Reduction Value (sw-f-003)."""
    retained = customers * (current_churn - target_churn) / 100
    return retained * acv * lifespan - program_cost


def calculate_margin_value(
    arr: float,
    current_gm: float,
    target_gm: float,
    investment: float
) -> float:
    """Calculate Gross Margin Expansion Value (sw-f-004)."""
    return arr * (target_gm - current_gm) / 100 - investment


def calculate_platform_roi(
    hours_saved: float,
    hourly_rate: float,
    infra_savings: float,
    investment: float
) -> float:
    """Calculate Platform Engineering ROI (sw-f-005)."""
    total_value = hours_saved * hourly_rate + infra_savings
    return total_value / investment * 100


def calculate_ai_monetization(
    customers: float,
    upsell_rate: float,
    premium_price: float,
    ai_cost: float
) -> float:
    """Calculate AI Feature Monetization Value (sw-f-006)."""
    adopters = customers * upsell_rate / 100
    revenue = adopters * premium_price
    return revenue - ai_cost


def calculate_support_efficiency(
    current_tickets: float,
    target_tickets: float,
    customers: float,
    cost_per_ticket: float,
    investment: float
) -> float:
    """Calculate Support Efficiency Improvement Value (sw-f-007)."""
    ticket_reduction = current_tickets - target_tickets
    annual_savings = ticket_reduction * customers * cost_per_ticket
    return annual_savings - investment


class TestFormulaCACEfficiencyROI:
    """Test sw-f-001: Customer Acquisition Efficiency ROI"""

    @pytest.mark.parametrize(
        "current_cac,target_cac,new_customers,investment,expected_roi,description",
        [
            (25000, 20000, 500, 500000, 400.0, "typical scenario"),
            (30000, 15000, 400, 400000, 1400.0, "strong improvement"),
            (1000, 500, 1, 100, 400.0, "minimum values"),
            (25000, 20000, 0, 500000, -100.0, "zero customers"),
            (25000, 25000, 500, 500000, -100.0, "no improvement"),
        ],
    )
    def test_cac_roi_scenarios(
        self,
        current_cac: float,
        target_cac: float,
        new_customers: float,
        investment: float,
        expected_roi: float,
        description: str,
    ):
        """Parameterized CAC ROI test covering typical and edge cases."""
        roi = calculate_cac_roi(current_cac, target_cac, new_customers, investment)
        assert roi == expected_roi, f"Failed for {description}"


class TestFormulaNRRImprovement:
    """Test sw-f-002: Net Revenue Retention Improvement Value"""

    @pytest.mark.parametrize(
        "beginning_arr,current_nrr,target_nrr,cost,expected_value,description",
        [
            (10_000_000, 105, 115, 750_000, 250_000, "typical improvement"),
            (50_000_000, 105, 120, 1_000_000, 6_500_000, "strong improvement"),
            (20_000_000, 100, 125, 2_000_000, 3_000_000, "world-class NRR"),
            (0, 100, 120, 500_000, -500_000, "zero ARR"),
            (10_000_000, 95, 100, 1_000_000, -500_000, "NRR below 100%"),
        ],
    )
    def test_nrr_scenarios(
        self,
        beginning_arr: float,
        current_nrr: float,
        target_nrr: float,
        cost: float,
        expected_value: float,
        description: str,
    ):
        """Parameterized NRR improvement test covering typical and edge cases."""
        value = calculate_nrr_value(beginning_arr, current_nrr, target_nrr, cost)
        assert value == expected_value, f"Failed for {description}"


class TestFormulaChurnReduction:
    """Test sw-f-003: Churn Reduction Value"""

    @pytest.mark.parametrize(
        "customers,current_churn,target_churn,acv,lifespan,program_cost,expected_value,description",
        [
            (200, 10, 7, 50_000, 5, 400_000, 1_100_000, "typical reduction"),
            (500, 15, 5, 100_000, 10, 1_000_000, 49_000_000, "significant reduction"),
            (0, 10, 5, 50_000, 5, 100_000, -100_000, "zero customer base"),
            (200, 10, 10, 50_000, 5, 400_000, -400_000, "no improvement"),
        ],
    )
    def test_churn_scenarios(
        self,
        customers: float,
        current_churn: float,
        target_churn: float,
        acv: float,
        lifespan: float,
        program_cost: float,
        expected_value: float,
        description: str,
    ):
        """Parameterized churn reduction test covering typical and edge cases."""
        value = calculate_churn_value(customers, current_churn, target_churn, acv, lifespan, program_cost)
        assert value == expected_value, f"Failed for {description}"


class TestFormulaGrossMarginExpansion:
    """Test sw-f-004: Gross Margin Expansion Value"""

    @pytest.mark.parametrize(
        "arr,current_gm,target_gm,investment,expected_value,description",
        [
            (10_000_000, 75, 76, 500_000, -400_000, "one point improvement"),
            (50_000_000, 70, 75, 2_000_000, 500_000, "typical improvement"),
            (100_000_000, 75, 85, 5_000_000, 5_000_000, "world-class margin"),
            (0, 70, 80, 1_000_000, -1_000_000, "zero ARR"),
            (50_000_000, 80, 75, 2_000_000, -4_500_000, "negative margin change"),
        ],
    )
    def test_margin_scenarios(
        self,
        arr: float,
        current_gm: float,
        target_gm: float,
        investment: float,
        expected_value: float,
        description: str,
    ):
        """Parameterized gross margin expansion test covering typical and edge cases."""
        value = calculate_margin_value(arr, current_gm, target_gm, investment)
        assert value == expected_value, f"Failed for {description}"


class TestFormulaPlatformEngineeringROI:
    """Test sw-f-005: Platform Engineering ROI"""

    @pytest.mark.parametrize(
        "hours_saved,hourly_rate,infra_savings,investment,expected_roi,tolerance,description",
        [
            (10_000, 100, 500_000, 2_000_000, 75.0, 0, "typical investment"),
            (50_000, 120, 1_000_000, 3_000_000, 233.33, 0.1, "strong ROI"),
            (0, 100, 0, 2_000_000, 0.0, 0, "zero hours saved"),
        ],
    )
    def test_platform_roi_scenarios(
        self,
        hours_saved: float,
        hourly_rate: float,
        infra_savings: float,
        investment: float,
        expected_roi: float,
        tolerance: float,
        description: str,
    ):
        """Parameterized platform engineering ROI test."""
        roi = calculate_platform_roi(hours_saved, hourly_rate, infra_savings, investment)
        if tolerance:
            assert abs(roi - expected_roi) < tolerance, f"Failed for {description}"
        else:
            assert roi == expected_roi, f"Failed for {description}"

    def test_break_even_analysis(self):
        """Calculate break-even hours needed."""
        investment = 2_000_000
        hourly_rate = 100
        infra_savings = 400_000

        hours_needed = (investment - infra_savings) / hourly_rate
        assert hours_needed == 16_000


class TestFormulaAIFeatureMonetization:
    """Test sw-f-006: AI Feature Monetization Value"""

    @pytest.mark.parametrize(
        "customers,upsell_rate,premium_price,ai_cost,expected_value,description",
        [
            (1000, 20, 100, 1_000_000, -980_000, "conservative adoption"),
            (2000, 40, 200, 1_500_000, -1_340_000, "strong adoption"),
            (1000, 0, 200, 1_000_000, -1_000_000, "zero adoption"),
        ],
    )
    def test_ai_monetization_scenarios(
        self,
        customers: float,
        upsell_rate: float,
        premium_price: float,
        ai_cost: float,
        expected_value: float,
        description: str,
    ):
        """Parameterized AI monetization test covering adoption scenarios."""
        value = calculate_ai_monetization(customers, upsell_rate, premium_price, ai_cost)
        assert value == expected_value, f"Failed for {description}"


class TestFormulaSupportEfficiency:
    """Test sw-f-007: Support Efficiency Improvement"""

    @pytest.mark.parametrize(
        "current_tickets,target_tickets,customers,cost_per_ticket,investment,expected_value,description",
        [
            (5, 3, 500, 25, 300_000, -275_000, "typical reduction"),
            (5, 5, 500, 25, 300_000, -300_000, "no improvement"),
        ],
    )
    def test_support_efficiency_scenarios(
        self,
        current_tickets: float,
        target_tickets: float,
        customers: float,
        cost_per_ticket: float,
        investment: float,
        expected_value: float,
        description: str,
    ):
        """Parameterized support efficiency test."""
        value = calculate_support_efficiency(current_tickets, target_tickets, customers, cost_per_ticket, investment)
        assert value == expected_value, f"Failed for {description}"

    def test_year_two_value(self):
        """Value after initial investment (no additional investment)."""
        current_tickets = 6
        target_tickets = 2
        customers = 1000
        cost_per_ticket = 30

        ticket_reduction = current_tickets - target_tickets
        annual_savings = ticket_reduction * customers * cost_per_ticket
        assert annual_savings == 120_000


class TestFormulaBoundaries:
    """Test formula boundary conditions using centralized formula functions."""

    def test_no_cac_improvement(self):
        """CAC stays the same - should show negative ROI due to investment."""
        roi = calculate_cac_roi(20000, 20000, 500, 500000)
        assert roi == -100.0

    def test_zero_churn_scenario(self):
        """Already at 0% churn - no value from reduction."""
        value = calculate_churn_value(200, 0, 0, 50000, 5, 400000)
        assert value == -400000

    def test_negative_margin_improvement(self):
        """Target GM lower than current - negative value."""
        value = calculate_margin_value(10_000_000, 80, 75, 500000)
        assert value == -1_000_000

    def test_division_by_zero_protection(self):
        """Verify formulas handle zero investment gracefully (raises exception)."""
        with pytest.raises(ZeroDivisionError):
            calculate_cac_roi(25000, 20000, 500, 0)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
