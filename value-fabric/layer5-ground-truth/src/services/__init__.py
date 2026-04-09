"""Layer 5 Ground Truth — service layer."""

from .state_machine import (
    ALLOWED_TRANSITIONS,
    STATUS_TO_MATURITY,
    InsufficientEvidenceError,
    InvalidTransitionError,
    ValidationStateMachine,
)
from .truth_service import (
    add_source,
    create_truth_object,
    get_truth_object,
    list_truth_objects,
    mark_stale_objects,
    soft_delete_truth_object,
    validate_truth_object,
)

__all__ = [
    "ALLOWED_TRANSITIONS",
    "STATUS_TO_MATURITY",
    "InsufficientEvidenceError",
    "InvalidTransitionError",
    "ValidationStateMachine",
    "add_source",
    "create_truth_object",
    "get_truth_object",
    "list_truth_objects",
    "mark_stale_objects",
    "soft_delete_truth_object",
    "validate_truth_object",
]
