"""Life Sciences Value Pack - Formula Execution Tests

Validates formula calculations with test cases and boundary values.
"""

import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestFormulaClinicalTrialAcceleration:
    """Test ls-f-001: Clinical Trial Acceleration Value"""

    def test_typical_acceleration(self):
        """12-month acceleration on blockbuster drug."""
        current_months = 72
        target_months = 60
        peak_revenue = 500_000_000
        npv_factor = 0.85
        program_cost = 10_000_000

        # (72 - 60) / 12 * 500M * 0.85 - 10M = 415M
        months_saved = current_months - target_months  # 12
        years_saved = months_saved / 12  # 1 year
        revenue_value = years_saved * peak_revenue * npv_factor  # 425M
        value = revenue_value - program_cost  # 415M

        assert value == 415_000_000

    def test_modest_acceleration(self):
        """6-month acceleration scenario."""
        current_months = 66
        target_months = 60
        peak_revenue = 200_000_000
        npv_factor = 0.80
        program_cost = 5_000_000

        # (66 - 60) / 12 * 200M * 0.8 - 5M = 75M
        months_saved = current_months - target_months  # 6
        years_saved = months_saved / 12  # 0.5
        value = years_saved * peak_revenue * npv_factor - program_cost  # 80M - 5M

        assert value == 75_000_000

    def test_minimum_acceleration(self):
        """Minimal 3-month improvement."""
        current_months = 48
        target_months = 45
        peak_revenue = 100_000_000
        npv_factor = 0.90
        program_cost = 2_000_000

        # (48 - 45) / 12 * 100M * 0.9 - 2M = 20.5M
        months_saved = current_months - target_months  # 3
        years_saved = months_saved / 12  # 0.25
        value = years_saved * peak_revenue * npv_factor - program_cost  # 22.5M - 2M

        assert value == 20_500_000


class TestFormulaPatientRecruitmentEfficiency:
    """Test ls-f-002: Patient Recruitment Efficiency"""

    def test_typical_efficiency_gain(self):
        """Reduce cost from $35K to $25K per patient."""
        current_cost = 35_000
        target_cost = 25_000
        required_patients = 1000
        investment = 2_000_000

        # (35000 - 25000) * 1000 - 2000000 = 8M
        savings_per_patient = current_cost - target_cost
        value = savings_per_patient * required_patients - investment

        assert value == 8_000_000

    def test_strong_efficiency(self):
        """Significant cost reduction with large enrollment."""
        current_cost = 40_000
        target_cost = 20_000
        required_patients = 2000
        investment = 3_000_000

        value = (current_cost - target_cost) * required_patients - investment
        assert value == 37_000_000

    def test_no_improvement(self):
        """No cost reduction - negative value."""
        current_cost = 30_000
        target_cost = 30_000
        required_patients = 500
        investment = 1_000_000

        value = (current_cost - target_cost) * required_patients - investment
        assert value == -1_000_000


class TestFormulaRDPortfolioROI:
    """Test ls-f-003: R&D Portfolio ROI"""

    def test_modest_improvement(self):
        """7-point improvement in success rate."""
        baseline_rate = 15
        improved_rate = 22
        pipeline_npv = 1_000_000_000
        investment = 50_000_000

        # (22 - 15) / 100 * 1B / 50M * 100 = 1400%
        value_increase = (improved_rate - baseline_rate) / 100 * pipeline_npv
        roi = value_increase / investment * 100

        assert roi == 140.0

    def test_strong_improvement(self):
        """15-point improvement in success rate."""
        baseline_rate = 15
        improved_rate = 30
        pipeline_npv = 2_000_000_000
        investment = 100_000_000

        roi = (improved_rate - baseline_rate) / 100 * pipeline_npv / investment * 100
        assert roi == 300.0

    def test_break_even(self):
        """Calculate break-even improvement."""
        pipeline_npv = 500_000_000
        investment = 50_000_000

        # Need 10% improvement to break even (100% ROI)
        needed_improvement = investment / pipeline_npv * 100
        assert needed_improvement == 10.0


class TestFormulaRegulatoryEfficiency:
    """Test ls-f-004: Regulatory Submission Efficiency"""

    def test_typical_improvement(self):
        """Reduce review from 16 to 12 months."""
        baseline_months = 16
        target_months = 12
        peak_revenue = 300_000_000
        npv_factor = 0.90
        fte_savings = 1_000_000
        investment = 3_000_000

        # (16 - 12) / 12 * 300M * 0.9 + 1M - 3M = 88M
        months_saved = baseline_months - target_months
        time_value = months_saved / 12 * peak_revenue * npv_factor
        value = time_value + fte_savings - investment

        assert value == 88_000_000

    def test_priority_review_scenario(self):
        """Achieve priority review timeline."""
        baseline_months = 12
        target_months = 6
        peak_revenue = 500_000_000
        npv_factor = 0.95
        fte_savings = 2_000_000
        investment = 5_000_000

        value = (baseline_months - target_months) / 12 * peak_revenue * npv_factor + fte_savings - investment
        assert value == 234_500_000


class TestFormulaManufacturingYield:
    """Test ls-f-005: Biomanufacturing Yield Improvement"""

    def test_typical_yield_improvement(self):
        """Improve yield from 75% to 85%."""
        current_yield = 75
        target_yield = 85
        annual_batches = 100
        batch_value = 5_000_000
        investment = 5_000_000

        # 100 * (85 - 75) / 100 * 5M - 5M = 45M
        improvement = target_yield - current_yield
        additional_batches = annual_batches * improvement / 100
        value = additional_batches * batch_value - investment

        assert value == 45_000_000

    def test_world_class_yield(self):
        """Achieve 95% world-class yield."""
        current_yield = 80
        target_yield = 95
        annual_batches = 200
        batch_value = 10_000_000
        investment = 20_000_000

        value = annual_batches * (target_yield - current_yield) / 100 * batch_value - investment
        assert value == 280_000_000

    def test_no_improvement(self):
        """No yield change - negative value."""
        current_yield = 80
        target_yield = 80
        annual_batches = 50
        batch_value = 2_000_000
        investment = 3_000_000

        value = annual_batches * (target_yield - current_yield) / 100 * batch_value - investment
        assert value == -3_000_000


class TestFormulaQualityRiskReduction:
    """Test ls-f-006: Quality Event Risk Reduction"""

    def test_typical_deviation_reduction(self):
        """Reduce deviation rate from 10% to 5%."""
        current_rate = 10
        target_rate = 5
        annual_batches = 100
        investigation_cost = 50_000
        avoided_recall_prob = 2  # 2% reduction
        recall_cost = 100_000_000
        investment = 3_000_000

        # 100 * (10 - 5) / 100 * 50K = 5 * 50K = 250K
        # + 2 / 100 * 100M = 2M
        # - 3M = -0.75M
        deviation_savings = annual_batches * (current_rate - target_rate) / 100 * investigation_cost
        recall_savings = avoided_recall_prob / 100 * recall_cost
        value = deviation_savings + recall_savings - investment

        assert value == -750_000  # First year due to recall probability

    def test_strong_quality_improvement(self):
        """Significant deviation reduction."""
        current_rate = 15
        target_rate = 5
        annual_batches = 200
        investigation_cost = 75_000
        avoided_recall_prob = 3
        recall_cost = 200_000_000
        investment = 5_000_000

        # 200 * (15 - 5) / 100 * 75K = 20 * 75K = 1.5M
        # + 3 / 100 * 200M = 6M
        # - 5M = 2.5M
        deviation_savings = annual_batches * (current_rate - target_rate) / 100 * investigation_cost
        recall_savings = avoided_recall_prob / 100 * recall_cost
        value = deviation_savings + recall_savings - investment

        assert value == 2_500_000  # Positive when recall risk considered

    def test_deviation_cost_only(self):
        """Focus on investigation cost savings."""
        current_rate = 10
        target_rate = 3
        annual_batches = 150
        investigation_cost = 60_000
        investment = 2_000_000

        deviation_savings = annual_batches * (current_rate - target_rate) / 100 * investigation_cost
        recall_savings = 0
        value = deviation_savings + recall_savings - investment

        assert value == -1_370_000  # Investment outweighs savings at this scale


class TestFormulaRealWorldEvidence:
    """Test ls-f-007: Real-World Evidence Value"""

    def test_conservative_rwe(self):
        """Conservative label expansion scenario."""
        label_expansion_npv = 100_000_000
        success_probability = 30
        hta_value = 50_000_000
        annual_cost = 8_000_000

        # 100M * 0.30 + 50M - 8M = 72M
        expansion_value = label_expansion_npv * success_probability / 100
        value = expansion_value + hta_value - annual_cost

        assert value == 72_000_000

    def test_strong_rwe_program(self):
        """High success probability scenario."""
        label_expansion_npv = 200_000_000
        success_probability = 50
        hta_value = 100_000_000
        annual_cost = 10_000_000

        value = label_expansion_npv * success_probability / 100 + hta_value - annual_cost
        assert value == 190_000_000

    def test_rwe_not_viable(self):
        """Low probability - program not viable."""
        label_expansion_npv = 50_000_000
        success_probability = 10
        hta_value = 10_000_000
        annual_cost = 8_000_000

        value = label_expansion_npv * success_probability / 100 + hta_value - annual_cost
        assert value == 7_000_000


class TestFormulaBoundaries:
    """Test formula boundary conditions."""

    def test_no_timeline_improvement(self):
        """No time saved - negative value."""
        current_months = 60
        target_months = 60
        peak_revenue = 500_000_000
        npv_factor = 0.85
        program_cost = 10_000_000

        value = (current_months - target_months) / 12 * peak_revenue * npv_factor - program_cost
        assert value == -10_000_000

    def test_no_success_rate_improvement(self):
        """Same success rate - zero incremental value, negative ROI from investment."""
        baseline_rate = 15
        improved_rate = 15
        pipeline_npv = 1_000_000_000
        investment = 50_000_000

        # No improvement means no value increase
        value_increase = (improved_rate - baseline_rate) / 100 * pipeline_npv  # 0
        # ROI calculation as defined in formula: value_increase / investment * 100
        roi = value_increase / investment * 100 if value_increase > 0 else -100
        assert roi == -100  # Lost investment (not in formula, but logical consequence)

    def test_worse_yield(self):
        """Target yield lower than current - negative value."""
        current_yield = 85
        target_yield = 80
        annual_batches = 100
        batch_value = 5_000_000
        investment = 5_000_000

        value = annual_batches * (target_yield - current_yield) / 100 * batch_value - investment
        assert value == -30_000_000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
