"""Policy models."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class GateSeverity(Enum):
    """Gate severity levels."""
    BLOCKER = "blocker"
    CRITICAL = "critical"
    WARNING = "warning"


class Comparator(Enum):
    """Threshold comparators."""
    EQ = "eq"
    GTE = "gte"
    LTE = "lte"
    CONTAINS = "contains"
    NOT_EMPTY = "not_empty"


@dataclass
class PolicyThreshold:
    """Threshold definition from policy."""
    name: str
    expected: Any
    comparator: str
    max_allowed_failures: int = 0


@dataclass
class GatePolicy:
    """Policy definition for a single gate."""
    gate_id: str
    severity: GateSeverity
    owner: str
    description: str
    checks: list[PolicyThreshold] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    fail_on_error: bool = True
    max_allowed_failures: int = 0
    enabled_profiles: list[str] = field(default_factory=list)


@dataclass
class PolicyConfig:
    """Complete policy configuration."""
    version: str = "1.0"
    enforcement_mode: str = "fail-closed"
    block_on_missing_artifacts: bool = True
    stale_gate_results: dict = field(default_factory=dict)
    gates: list[GatePolicy] = field(default_factory=list)
    profiles: dict = field(default_factory=dict)
