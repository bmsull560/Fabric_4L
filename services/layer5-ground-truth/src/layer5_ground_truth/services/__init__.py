"""Layer 5 Ground Truth — service layer."""

from .freshness_monitor import (
    DEFAULT_TTL_BY_CLAIM_TYPE,
    FreshnessMonitor,
    check_freshness,
    get_stale_truths,
)
from .state_machine import (
    ALLOWED_TRANSITIONS,
    STATUS_TO_MATURITY,
    InsufficientEvidenceError,
    InvalidTransitionError,
    TransitionConflictError,
    ValidationStateMachine,
)
from .truth_service import (
    add_source,
    create_truth_object,
    get_truth_object,
    list_truth_objects,
    soft_delete_truth_object,
    validate_truth_object,
)

__all__ = [
    # Freshness monitor
    "DEFAULT_TTL_BY_CLAIM_TYPE",
    "FreshnessMonitor",
    "check_freshness",
    "get_stale_truths",
    # State machine
    "ALLOWED_TRANSITIONS",
    "STATUS_TO_MATURITY",
    "InsufficientEvidenceError",
    "InvalidTransitionError",
    "TransitionConflictError",
    "ValidationStateMachine",
    # Truth service
    "add_source",
    "create_truth_object",
    "get_truth_object",
    "list_truth_objects",
    "soft_delete_truth_object",
    "validate_truth_object",
]
