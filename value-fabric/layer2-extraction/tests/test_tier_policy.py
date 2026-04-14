"""Tests for tier-based access policy in extraction pipeline.

Validates:
- Tier-operation mapping correctness
- Fail-closed behavior for unknown tiers/operations
- Route-to-tier resolution
"""

import importlib.util
import sys
from pathlib import Path

import pytest
from unittest.mock import MagicMock

# Load tier_policy module directly from file to avoid circular imports
tier_policy_path = Path(__file__).parent.parent / "src" / "layer2_extraction" / "api" / "tier_policy.py"
spec = importlib.util.spec_from_file_location("tier_policy", tier_policy_path)
tier_policy = importlib.util.module_from_spec(spec)
sys.modules["tier_policy"] = tier_policy
spec.loader.exec_module(tier_policy)

# Import the needed items
AccessTier = tier_policy.AccessTier
ExtractionOperation = tier_policy.ExtractionOperation
can_perform_operation = tier_policy.can_perform_operation
get_tier_for_route = tier_policy.get_tier_for_route


class TestCanPerformOperation:
    """Test tier-operation permission matrix."""

    def test_standard_tier_read_only(self):
        """Standard tier can only view, not modify."""
        assert can_perform_operation(AccessTier.STANDARD, ExtractionOperation.VIEW_JOB_STATUS)
        assert can_perform_operation(AccessTier.STANDARD, ExtractionOperation.VIEW_RESULTS)
        assert can_perform_operation(AccessTier.STANDARD, ExtractionOperation.STREAM_LOGS)

        # Cannot perform advanced operations
        assert not can_perform_operation(AccessTier.STANDARD, ExtractionOperation.CREATE_JOB)
        assert not can_perform_operation(AccessTier.STANDARD, ExtractionOperation.CANCEL_JOB)
        assert not can_perform_operation(AccessTier.STANDARD, ExtractionOperation.TRIGGER_RETRY)

    def test_advanced_tier_full_control(self):
        """Advanced tier has full extraction control."""
        # Can view
        assert can_perform_operation(AccessTier.ADVANCED, ExtractionOperation.VIEW_JOB_STATUS)
        assert can_perform_operation(AccessTier.ADVANCED, ExtractionOperation.VIEW_RESULTS)

        # Can control
        assert can_perform_operation(AccessTier.ADVANCED, ExtractionOperation.CREATE_JOB)
        assert can_perform_operation(AccessTier.ADVANCED, ExtractionOperation.CANCEL_JOB)
        assert can_perform_operation(AccessTier.ADVANCED, ExtractionOperation.TRIGGER_RETRY)
        assert can_perform_operation(AccessTier.ADVANCED, ExtractionOperation.VIEW_RAW_ENTITIES)

        # Cannot perform admin operations
        assert not can_perform_operation(AccessTier.ADVANCED, ExtractionOperation.ADMIN_RETRY_ALL)

    def test_admin_tier_all_operations(self):
        """Admin tier can perform all operations."""
        for op in ExtractionOperation:
            assert can_perform_operation(AccessTier.ADMIN, op)

    # SECURITY: Fail-closed tests
    def test_unknown_tier_denied_all(self):
        """Unknown tier is denied all operations (fail-closed)."""
        for op in ExtractionOperation:
            assert not can_perform_operation("unknown", op)  # type: ignore

    def test_unknown_operation_denied(self):
        """Unknown operation is denied for all tiers (fail-closed)."""
        fake_op = "fake_operation"  # type: ignore
        for tier in [AccessTier.STANDARD, AccessTier.ADVANCED, AccessTier.ADMIN]:
            assert not can_perform_operation(tier, fake_op)


# Note: require_tier dependency tests are tested via integration tests
# to avoid FastAPI import chain issues with shared.identity module.


class TestGetTierForRoute:
    """Test route-to-tier resolution."""

    def test_standard_routes(self):
        """Job viewing routes are standard tier."""
        assert get_tier_for_route("/jobs/status") == AccessTier.STANDARD
        assert get_tier_for_route("/jobs/123/results") == AccessTier.STANDARD
        assert get_tier_for_route("/jobs/123/logs") == AccessTier.STANDARD

    def test_advanced_routes(self):
        """Extraction control routes are advanced tier."""
        assert get_tier_for_route("/extraction") == AccessTier.ADVANCED
        assert get_tier_for_route("/pipeline/config") == AccessTier.ADVANCED
        assert get_tier_for_route("/raw/entities") == AccessTier.ADVANCED

    def test_admin_routes(self):
        """Admin routes require admin tier."""
        assert get_tier_for_route("/admin/retry-all") == AccessTier.ADMIN
        assert get_tier_for_route("/admin/config") == AccessTier.ADMIN

    # SECURITY: Fail-closed
    def test_unknown_routes_default_standard(self):
        """SECURITY: Unknown routes default to standard (least privilege)."""
        assert get_tier_for_route("/unknown-route") == AccessTier.STANDARD
        assert get_tier_for_route("/malicious/path") == AccessTier.STANDARD
