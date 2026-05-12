"""Tier-based access policy for extraction pipeline."""

from __future__ import annotations

from enum import Enum


class AccessTier(str, Enum):
    """Access tiers for extraction operations."""

    STANDARD = "standard"
    ADVANCED = "advanced"
    ADMIN = "admin"


class ExtractionOperation(str, Enum):
    """Extraction operations subject to tier policy."""

    VIEW_JOB_STATUS = "view_job_status"
    VIEW_RESULTS = "view_results"
    STREAM_LOGS = "stream_logs"
    CREATE_JOB = "create_job"
    CANCEL_JOB = "cancel_job"
    TRIGGER_RETRY = "trigger_retry"
    VIEW_RAW_ENTITIES = "view_raw_entities"
    ADMIN_RETRY_ALL = "admin_retry_all"


_TIER_PERMISSIONS: dict[AccessTier, set[ExtractionOperation]] = {
    AccessTier.STANDARD: {
        ExtractionOperation.VIEW_JOB_STATUS,
        ExtractionOperation.VIEW_RESULTS,
        ExtractionOperation.STREAM_LOGS,
    },
    AccessTier.ADVANCED: {
        ExtractionOperation.VIEW_JOB_STATUS,
        ExtractionOperation.VIEW_RESULTS,
        ExtractionOperation.STREAM_LOGS,
        ExtractionOperation.CREATE_JOB,
        ExtractionOperation.CANCEL_JOB,
        ExtractionOperation.TRIGGER_RETRY,
        ExtractionOperation.VIEW_RAW_ENTITIES,
    },
    AccessTier.ADMIN: set(ExtractionOperation),
}

_ROUTE_TIER_MAP: dict[str, AccessTier] = {
    "/jobs/status": AccessTier.STANDARD,
    "/jobs/123/results": AccessTier.STANDARD,
    "/jobs/123/logs": AccessTier.STANDARD,
    "/extraction": AccessTier.ADVANCED,
    "/pipeline/config": AccessTier.ADVANCED,
    "/raw/entities": AccessTier.ADVANCED,
    "/admin/retry-all": AccessTier.ADMIN,
    "/admin/config": AccessTier.ADMIN,
}


def can_perform_operation(tier: AccessTier | str, operation: ExtractionOperation | str) -> bool:
    """Check if a tier can perform an operation (fail-closed)."""
    try:
        if isinstance(tier, str):
            tier = AccessTier(tier)
        if isinstance(operation, str):
            operation = ExtractionOperation(operation)
    except ValueError:
        return False

    allowed = _TIER_PERMISSIONS.get(tier, set())
    return operation in allowed


def get_tier_for_route(route: str) -> AccessTier:
    """Resolve the required access tier for a route (defaults to STANDARD)."""
    return _ROUTE_TIER_MAP.get(route, AccessTier.STANDARD)
