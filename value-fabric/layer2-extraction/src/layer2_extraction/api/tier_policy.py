"""Tier-based access policy for extraction pipeline.

Separates tier-specific concerns from core extraction logic:
- Standard tier: Read-only job monitoring, results viewing
- Advanced tier: Full extraction orchestration, retry controls, raw extraction access

This ensures that extraction logic changes for one tier don't affect the other,
and provides clear trust boundaries for security-sensitive operations.
"""

from enum import Enum
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from fastapi import Request


class AccessTier(str, Enum):
    """User access tiers for extraction features."""

    STANDARD = "standard"
    ADVANCED = "advanced"
    ADMIN = "admin"


class ExtractionOperation(str, Enum):
    """Extraction operations that may be tier-restricted."""

    # Standard tier operations (read-only)
    VIEW_JOB_STATUS = "view_job_status"
    VIEW_RESULTS = "view_results"
    STREAM_LOGS = "stream_logs"

    # Advanced tier operations (extraction control)
    CREATE_JOB = "create_job"
    CANCEL_JOB = "cancel_job"
    TRIGGER_RETRY = "trigger_retry"
    VIEW_RAW_ENTITIES = "view_raw_entities"
    MODIFY_PIPELINE_CONFIG = "modify_pipeline_config"

    # Admin operations
    ADMIN_RETRY_ALL = "admin_retry_all"
    ADMIN_BYPASS_VALIDATION = "admin_bypass_validation"


# Tier-operation mapping - defines which tiers can perform which operations
TIER_OPERATION_MAP: dict[AccessTier, set[ExtractionOperation]] = {
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
    AccessTier.ADMIN: set(ExtractionOperation),  # All operations
}


def can_perform_operation(tier: AccessTier, operation: ExtractionOperation) -> bool:
    """Check if a tier can perform an operation.

    Args:
        tier: User's access tier
        operation: Operation to check

    Returns:
        True if operation is allowed, False otherwise
    """
    allowed_ops = TIER_OPERATION_MAP.get(tier, set())
    return operation in allowed_ops


def require_tier(operation: ExtractionOperation) -> Callable:
    """Decorator/FastAPI dependency to require a specific tier for an operation.

    Usage:
        @app.post("/jobs")
        async def create_job(
            request: Request,
            _enforce=Depends(require_tier(ExtractionOperation.CREATE_JOB))
        ):
            ...

    SECURITY: Fails closed - if tier cannot be determined, access is denied.
    """
    # Lazy import to avoid circular dependencies
    from fastapi import HTTPException, Request, status

    async def _enforce_tier(request: "Request") -> None:
        # Extract tier from request context (set by auth middleware)
        user_tier = getattr(request.state, "user_tier", None)

        if user_tier is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: user tier not determined",
            )

        try:
            tier = AccessTier(user_tier.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: invalid user tier",
            )

        if not can_perform_operation(tier, operation):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: {operation.value} requires higher tier",
            )

    return _enforce_tier


def get_tier_for_route(path: str) -> AccessTier:
    """Determine access tier for a route path.

    This maps frontend routes to their corresponding access tiers
    for backend validation alignment.

    SECURITY: Returns STANDARD for unknown routes (fail-closed to least privilege).
    """
    # Standard tier routes (monitoring only)
    if path.startswith("/jobs") and not any(
        p in path for p in ["/create", "/cancel", "/retry", "/config"]
    ):
        return AccessTier.STANDARD

    # Advanced tier routes
    if any(p in path for p in ["/extraction", "/pipeline", "/raw"]):
        return AccessTier.ADVANCED

    # Admin routes
    if path.startswith("/admin/"):
        return AccessTier.ADMIN

    # Default to standard (fail-closed)
    return AccessTier.STANDARD
