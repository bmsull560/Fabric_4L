"""Typed service output contracts for TruthObject freshness monitoring."""

from pydantic import BaseModel
from value_fabric.shared.models.typed_dict import TypedDictModel


class FreshnessCounts(BaseModel):
    """Aggregated TruthObject freshness counts for a tenant."""

    stale: int
    fresh: int
    expiring_soon: int
    total: int


class FreshnessCheckResponse(TypedDictModel):
    """Result envelope returned after a freshness reconciliation run."""

    checked: int
    marked_stale: int
    dry_run: bool
    timestamp: str


class FreshnessSummaryResponse(TypedDictModel):
    """Tenant-scoped summary of TruthObject freshness state."""

    tenant_id: str
    timestamp: str
    summary: FreshnessCounts
    warning_threshold_days: int
