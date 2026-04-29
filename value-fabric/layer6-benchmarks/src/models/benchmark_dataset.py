"""Benchmark dataset models for Layer 6.

Storage model aligned with Neo4j + provenance tracking.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional
from shared.models.typed_dict import TypedDictModel


class StatisticalProfile_to_dictResult(TypedDictModel):
    mean: Any
    p10: Any
    p25: Any
    p50: Any
    p75: Any
    p90: Any
    sample_size: Any
    std_dev: Any


@dataclass
class StatisticalProfile:
    """Statistical profile for a benchmark metric."""

    p10: Decimal
    p25: Decimal
    p50: Decimal
    p75: Decimal
    p90: Decimal
    mean: Decimal
    std_dev: Decimal
    sample_size: int

    def to_dict(self) -> Dict[str, Any]:
        return StatisticalProfile_to_dictResult.model_validate({
            "p10": str(self.p10),
            "p25": str(self.p25),
            "p50": str(self.p50),
            "p75": str(self.p75),
            "p90": str(self.p90),
            "mean": str(self.mean),
            "std_dev": str(self.std_dev),
            "sample_size": self.sample_size,
        })


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StatisticalProfile":
        return cls(
            p10=Decimal(data["p10"]),
            p25=Decimal(data["p25"]),
            p50=Decimal(data["p50"]),
            p75=Decimal(data["p75"]),
            p90=Decimal(data["p90"]),
            mean=Decimal(data["mean"]),
            std_dev=Decimal(data["std_dev"]),
            sample_size=data["sample_size"],
        )


@dataclass
class BenchmarkMetric:
    """Individual metric within a benchmark dataset."""

    name: str
    unit: str  # e.g., "USD", "hours", "percent"
    description: str
    profile: StatisticalProfile

    # Validation rules
    lower_bound: Optional[Decimal] = None
    upper_bound: Optional[Decimal] = None
    is_higher_better: bool = True  # For comparison direction


@dataclass
class BenchmarkDataset:
    """Benchmark dataset for an industry/segment.

    Curated dataset (not validated claims) for peer comparison
    and statistical validation.
    """

    dataset_id: str
    name: str
    description: str

    # Classification
    industry: str
    segment: Optional[str]  # e.g., "enterprise", "mid-market", "small"
    geography: Optional[str]  # e.g., "US", "EU", "global"

    # Metrics
    metrics: Dict[str, BenchmarkMetric] = field(default_factory=dict)

    # Metadata
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    data_source: Optional[str] = None  # e.g., "Gartner 2024", "Internal Study"

    # Provenance
    provenance_id: Optional[str] = None  # Links to L4 provenance tracking
    is_public: bool = False

    def get_metric(self, name: str) -> Optional[BenchmarkMetric]:
        """Get metric by name."""
        return self.metrics.get(name)

    def add_metric(self, metric: BenchmarkMetric) -> None:
        """Add metric to dataset."""
        self.metrics[metric.name] = metric
        self.updated_at = datetime.now(timezone.utc)


@dataclass
class ComparisonRequest:
    """Request for peer comparison."""

    dataset_id: str
    metric: str
    company_value: Decimal
    industry: str
    segment: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of peer comparison with statistical profile."""

    percentile: int  # 0-100
    peer_median: Decimal
    peer_range: tuple[Decimal, Decimal]  # (p10, p90)
    sample_size: int
    confidence: str  # high, medium, low

    # Detailed breakdown
    statistical_profile: Optional[StatisticalProfile] = None

    # Interpretation
    assessment: str = ""  # e.g., "above average", "top performer"


@dataclass
class RangeValidationRequest:
    """Request for range validation."""

    dataset_id: str
    metric: str
    value: Decimal
    tolerance_percent: int = 10


@dataclass
class RangeValidationResult:
    """Result of range validation."""

    is_valid: bool
    expected_range: tuple[Decimal, Decimal]
    actual_value: Decimal
    deviation_percent: Optional[float]
    severity: str  # info, warning, error

    # Guidance
    message: str = ""
    recommended_action: Optional[str] = None


# Manufacturing benchmark reference dataset (seed data)
MANUFACTURING_BENCHMARK_SEED = {
    "dataset_id": "manufacturing-efficiency-2024",
    "name": "Manufacturing Efficiency Benchmarks 2024",
    "description": "Peer benchmarks for manufacturing efficiency metrics",
    "industry": "manufacturing",
    "segment": "enterprise",
    "geography": "global",
    "version": "1.0.0",
    "data_source": "Industry Consortium 2024",
    "is_public": True,
    "metrics": {
        "oee_overall_equipment_effectiveness": {
            "name": "oee_overall_equipment_effectiveness",
            "unit": "percent",
            "description": "Overall Equipment Effectiveness",
            "profile": {
                "p10": "45.0",
                "p25": "55.0",
                "p50": "65.0",
                "p75": "75.0",
                "p90": "85.0",
                "mean": "65.0",
                "std_dev": "12.5",
                "sample_size": 1250,
            },
            "lower_bound": "30.0",
            "upper_bound": "95.0",
            "is_higher_better": True,
        },
        "production_cycle_time_minutes": {
            "name": "production_cycle_time_minutes",
            "unit": "minutes",
            "description": "Average production cycle time",
            "profile": {
                "p10": "15.0",
                "p25": "25.0",
                "p50": "45.0",
                "p75": "75.0",
                "p90": "120.0",
                "mean": "56.0",
                "std_dev": "28.0",
                "sample_size": 890,
            },
            "is_higher_better": False,
        },
        "defect_rate_percent": {
            "name": "defect_rate_percent",
            "unit": "percent",
            "description": "Manufacturing defect rate",
            "profile": {
                "p10": "0.1",
                "p25": "0.5",
                "p50": "1.5",
                "p75": "3.0",
                "p90": "5.0",
                "mean": "2.1",
                "std_dev": "1.4",
                "sample_size": 1100,
            },
            "lower_bound": "0.0",
            "upper_bound": "10.0",
            "is_higher_better": False,
        },
        "energy_consumption_per_unit_kwh": {
            "name": "energy_consumption_per_unit_kwh",
            "unit": "kWh",
            "description": "Energy consumption per unit produced",
            "profile": {
                "p10": "0.5",
                "p25": "1.2",
                "p50": "2.5",
                "p75": "4.0",
                "p90": "6.5",
                "mean": "2.8",
                "std_dev": "1.8",
                "sample_size": 675,
            },
            "is_higher_better": False,
        },
    },
}
