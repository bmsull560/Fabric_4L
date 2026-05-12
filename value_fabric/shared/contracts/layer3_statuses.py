"""Canonical Layer 3 status literals aligned to contracts/openapi/layer3-knowledge.json."""

from typing import Literal

HEALTH_STATUSES = ("healthy", "unhealthy", "degraded")
INGEST_STATUSES = ("success", "partial", "failed")
SYNC_STATUSES = ("synced", "pending", "failed", "outdated")
ENTITY_STATUSES = ("validated", "pending", "draft", "deprecated")
BENCHMARK_STATUSES = ("active", "draft", "deprecated")
FORMULA_VERSION_STATUSES = (
    "draft",
    "under_review",
    "approved",
    "active",
    "deprecated",
    "retired",
)

HealthStatus = Literal["healthy", "unhealthy", "degraded"]
IngestStatus = Literal["success", "partial", "failed"]
SyncStatus = Literal["synced", "pending", "failed", "outdated"]
EntityStatus = Literal["validated", "pending", "draft", "deprecated"]
BenchmarkStatus = Literal["active", "draft", "deprecated"]
FormulaVersionStatus = Literal[
    "draft", "under_review", "approved", "active", "deprecated", "retired"
]
