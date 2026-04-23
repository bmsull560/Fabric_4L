"""Gate SDK models and data classes."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import UUID, uuid4


class GateSeverity(Enum):
    """Gate severity levels."""
    BLOCKER = "blocker"      # Fails release
    CRITICAL = "critical"    # Fails release
    WARNING = "warning"      # Advisory only


class GateResult(Enum):
    """Gate execution results."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    ERROR = "error"          # Infrastructure failure


class GateProfile(Enum):
    """Gate execution profiles."""
    PR_FAST = "pr-fast"
    MAINLINE_FULL = "mainline-full"
    RELEASE_CANDIDATE = "release-candidate"


@dataclass
class CheckResult:
    """Result of a single check within a gate."""
    name: str
    result: GateResult
    value: Any = None              # Actual measured value
    threshold: Any = None          # Expected threshold
    comparator: str = "eq"         # "eq", "gte", "lte", "contains"
    duration_ms: int = 0
    message: Optional[str] = None
    log_path: Optional[Path] = None


@dataclass
class GateArtifact:
    """Artifact produced by a gate."""
    path: Path
    content_type: str              # application/json, text/markdown
    checksum: str                  # sha256
    size_bytes: int


@dataclass
class GateVerdict:
    """Verdict from policy evaluation."""
    result: GateResult
    blocks_release: bool
    reason: str
    failed_checks: list[CheckResult] = field(default_factory=list)
    duration_seconds: float = 0.0


@dataclass
class GateExecution:
    """Complete record of a gate execution."""
    execution_id: UUID = field(default_factory=uuid4)
    gate_id: str = ""
    profile: GateProfile = GateProfile.PR_FAST
    started_at: datetime = field(default_factory=datetime.utcnow)
    finished_at: Optional[datetime] = None
    results: list[CheckResult] = field(default_factory=list)
    artifacts: list[GateArtifact] = field(default_factory=list)
    verdict: Optional[GateVerdict] = None
    trace_id: Optional[str] = None


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
class ReleaseManifest:
    """Signed release manifest."""
    manifest_version: str = "2.0"
    release_id: str = ""
    commit: str = ""
    branch: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    profile: str = ""
    gates: list[dict] = field(default_factory=list)
    verdict: Optional[dict] = None
    signatures: dict = field(default_factory=dict)
