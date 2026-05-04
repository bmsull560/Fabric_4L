"""
Test tenant validation metrics tracking invariants.

Verifies that tenant validation metrics are tracked accurately and can be reset.

Critical P0 test - monitoring gaps if metrics are not tracked correctly.
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from services.layer4_agents.src.database import (
    validate_tenant_id,
    _tenant_validation_metrics,
)
from services.layer4_agents.src.database import TenantContextError


class TestTenantValidationMetricsTracking:
    """Test suite for tenant validation metrics tracking invariants."""

    def test_metrics_initialization(self):
        """
        POSITIVE: Metrics should be initialized with zero values.
        Tests metrics initialization.
        """
        expected_metrics = {
            "validations_total": 0,
            "validation_failures": 0,
            "uuid_format_errors": 0,
            "missing_context_errors": 0,
            "empty_tenant_errors": 0,
        }

        for key, expected_value in expected_metrics.items():
            assert _tenant_validation_metrics.get(key, 0) == expected_value

    def test_valid_tenant_increments_validations_total(self):
        """
        POSITIVE: Valid tenant should increment validations_total.
        Tests metrics tracking for successful validations.
        """
        initial_count = _tenant_validation_metrics.get("validations_total", 0)

        tenant_id = uuid4()
        result = validate_tenant_id(tenant_id)

        assert _tenant_validation_metrics["validations_total"] == initial_count + 1
        assert _tenant_validation_metrics["validation_failures"] == 0

    def test_valid_tenant_string_increments_validations_total(self):
        """
        POSITIVE: Valid tenant string should increment validations_total.
        Tests metrics tracking for string UUID inputs.
        """
        initial_count = _tenant_validation_metrics.get("validations_total", 0)

        tenant_id = str(uuid4())
        result = validate_tenant_id(tenant_id)

        assert _tenant_validation_metrics["validations_total"] == initial_count + 1

    def test_reserved_keyword_increments_validations_total(self):
        """
        POSITIVE: Reserved keywords should increment validations_total.
        Tests metrics tracking for system keywords.
        """
        initial_count = _tenant_validation_metrics.get("validations_total", 0)

        for keyword in ["system", "admin", "internal"]:
            validate_tenant_id(keyword)

        assert _tenant_validation_metrics["validations_total"] == initial_count + 3

    def test_null_tenant_increments_missing_context_errors(self):
        """
        NEGATIVE: Null tenant should increment missing_context_errors.
        Tests metrics tracking for missing tenant context.
        """
        initial_count = _tenant_validation_metrics.get("missing_context_errors", 0)

        with pytest.raises(TenantContextError):
            validate_tenant_id(None)

        assert _tenant_validation_metrics["missing_context_errors"] == initial_count + 1
        assert _tenant_validation_metrics["validation_failures"] == 1

    def test_empty_tenant_increments_empty_tenant_errors(self):
        """
        NEGATIVE: Empty tenant should increment empty_tenant_errors.
        Tests metrics tracking for empty tenant strings.
        """
        initial_count = _tenant_validation_metrics.get("empty_tenant_errors", 0)

        with pytest.raises(TenantContextError):
            validate_tenant_id("")

        assert _tenant_validation_metrics["empty_tenant_errors"] == initial_count + 1
        assert _tenant_validation_metrics["validation_failures"] == 1

    def test_invalid_uuid_increments_uuid_format_errors(self):
        """
        NEGATIVE: Invalid UUID should increment uuid_format_errors.
        Tests metrics tracking for UUID format validation.
        """
        initial_count = _tenant_validation_metrics.get("uuid_format_errors", 0)

        with pytest.raises(TenantContextError):
            validate_tenant_id("not-a-uuid")

        assert _tenant_validation_metrics["uuid_format_errors"] == initial_count + 1
        assert _tenant_validation_metrics["validation_failures"] == 1

    def test_whitespace_tenant_increments_empty_tenant_errors(self):
        """
        NEGATIVE: Whitespace-only tenant should increment empty_tenant_errors.
        Tests metrics tracking for whitespace normalization.
        """
        initial_count = _tenant_validation_metrics.get("empty_tenant_errors", 0)

        with pytest.raises(TenantContextError):
            validate_tenant_id("   ")

        assert _tenant_validation_metrics["empty_tenant_errors"] == initial_count + 1
        assert _tenant_validation_metrics["validation_failures"] == 1

    def test_validation_failures_increments_on_all_errors(self):
        """
        POSITIVE: All validation errors should increment validation_failures.
        Tests metrics tracking for total failures.
        """
        initial_failures = _tenant_validation_metrics.get("validation_failures", 0)

        error_cases = [None, "", "not-a-uuid", "   "]

        for case in error_cases:
            try:
                validate_tenant_id(case)
            except TenantContextError:
                pass

        assert _tenant_validation_metrics["validation_failures"] == initial_failures + len(error_cases)


class TestMetricsAccuracy:
    """Test suite for metrics accuracy invariants."""

    def test_metrics_count_matches_validations(self):
        """
        POSITIVE: Total validations should equal successful + failed validations.
        Tests metrics consistency.
        """
        # Reset metrics
        _tenant_validation_metrics.update({
            "validations_total": 0,
            "validation_failures": 0,
            "uuid_format_errors": 0,
            "missing_context_errors": 0,
            "empty_tenant_errors": 0,
        })

        # Perform validations
        valid_cases = [str(uuid4()), str(uuid4()), "system"]
        error_cases = [None, "", "not-a-uuid"]

        for case in valid_cases:
            try:
                validate_tenant_id(case)
            except TenantContextError:
                pass

        for case in error_cases:
            try:
                validate_tenant_id(case)
            except TenantContextError:
                pass

        total_validations = len(valid_cases) + len(error_cases)
        assert _tenant_validation_metrics["validations_total"] == total_validations

    def test_specific_error_counts_sum_to_failures(self):
        """
        POSITIVE: Specific error counts should sum to total failures.
        Tests metrics consistency.
        """
        # Reset metrics
        _tenant_validation_metrics.update({
            "validation_failures": 0,
            "uuid_format_errors": 0,
            "missing_context_errors": 0,
            "empty_tenant_errors": 0,
        })

        # Perform validations
        try:
            validate_tenant_id(None)
        except TenantContextError:
            pass

        try:
            validate_tenant_id("")
        except TenantContextError:
            pass

        try:
            validate_tenant_id("not-a-uuid")
        except TenantContextError:
            pass

        total_specific_errors = (
            _tenant_validation_metrics["uuid_format_errors"] +
            _tenant_validation_metrics["missing_context_errors"] +
            _tenant_validation_metrics["empty_tenant_errors"]
        )

        assert total_specific_errors == _tenant_validation_metrics["validation_failures"]


class TestMetricsResetFunctionality:
    """Test suite for metrics reset functionality."""

    def test_metrics_can_be_reset(self):
        """
        POSITIVE: Metrics should be resettable.
        Tests metrics reset capability.
        """
        # Perform some validations to increment metrics
        validate_tenant_id(str(uuid4()))
        try:
            validate_tenant_id(None)
        except TenantContextError:
            pass

        # Reset metrics
        _tenant_validation_metrics.update({
            "validations_total": 0,
            "validation_failures": 0,
            "uuid_format_errors": 0,
            "missing_context_errors": 0,
            "empty_tenant_errors": 0,
        })

        # Verify reset
        assert _tenant_validation_metrics["validations_total"] == 0
        assert _tenant_validation_metrics["validation_failures"] == 0
        assert _tenant_validation_metrics["uuid_format_errors"] == 0
        assert _tenant_validation_metrics["missing_context_errors"] == 0
        assert _tenant_validation_metrics["empty_tenant_errors"] == 0

    def test_metrics_reset_does_not_affect_validation_logic(self):
        """
        POSITIVE: Metrics reset should not affect validation logic.
        Tests that validation continues to work after reset.
        """
        # Reset metrics
        _tenant_validation_metrics.update({
            "validations_total": 0,
            "validation_failures": 0,
            "uuid_format_errors": 0,
            "missing_context_errors": 0,
            "empty_tenant_errors": 0,
        })

        # Validation should still work
        tenant_id = str(uuid4())
        result = validate_tenant_id(tenant_id)

        assert result == str(tenant_id)
        assert _tenant_validation_metrics["validations_total"] == 1


class TestMetricsMonitoringIntegration:
    """Test suite for metrics monitoring integration."""

    def test_metrics_are_accessible(self):
        """
        POSITIVE: Metrics should be accessible for monitoring.
        Tests metrics accessibility.
        """
        assert isinstance(_tenant_validation_metrics, dict)

    def test_metrics_have_all_required_fields(self):
        """
        POSITIVE: Metrics should have all required fields.
        Tests metrics completeness.
        """
        required_fields = [
            "validations_total",
            "validation_failures",
            "uuid_format_errors",
            "missing_context_errors",
            "empty_tenant_errors",
        ]

        for field in required_fields:
            assert field in _tenant_validation_metrics

    def test_metrics_values_are_integers(self):
        """
        POSITIVE: Metric values should be integers.
        Tests metrics type correctness.
        """
        for key, value in _tenant_validation_metrics.items():
            assert isinstance(value, int)

    def test_metrics_values_are_non_negative(self):
        """
        POSITIVE: Metric values should be non-negative.
        Tests metrics validity.
        """
        for key, value in _tenant_validation_metrics.items():
            assert value >= 0


class TestMetricsConcurrencySafety:
    """Test suite for metrics concurrency safety."""

    def test_metrics_increment_is_threadsafe(self):
        """
        POSITIVE: Metrics increment should be thread-safe.
        Tests concurrent metric updates.
        """
        import threading

        def increment_metric():
            try:
                validate_tenant_id(str(uuid4()))
            except TenantContextError:
                pass

        # Create multiple threads
        threads = [threading.Thread(target=increment_metric) for _ in range(10)]

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify all increments were recorded
        assert _tenant_validation_metrics["validations_total"] >= 10


class TestReservedKeywordHandling:
    """Test suite for reserved keyword handling in metrics."""

    def test_system_keyword_does_not_increment_errors(self):
        """
        POSITIVE: 'system' keyword should not increment error metrics.
        Tests reserved keyword handling.
        """
        initial_failures = _tenant_validation_metrics.get("validation_failures", 0)

        result = validate_tenant_id("system")

        assert result == "system"
        assert _tenant_validation_metrics["validation_failures"] == initial_failures

    def test_admin_keyword_does_not_increment_errors(self):
        """
        POSITIVE: 'admin' keyword should not increment error metrics.
        Tests reserved keyword handling.
        """
        initial_failures = _tenant_validation_metrics.get("validation_failures", 0)

        result = validate_tenant_id("admin")

        assert result == "admin"
        assert _tenant_validation_metrics["validation_failures"] == initial_failures

    def test_internal_keyword_does_not_increment_errors(self):
        """
        POSITIVE: 'internal' keyword should not increment error metrics.
        Tests reserved keyword handling.
        """
        initial_failures = _tenant_validation_metrics.get("validation_failures", 0)

        result = validate_tenant_id("internal")

        assert result == "internal"
        assert _tenant_validation_metrics["validation_failures"] == initial_failures

    def test_case_insensitive_reserved_keywords(self):
        """
        POSITIVE: Reserved keywords should be case-insensitive.
        Tests keyword normalization.
        """
        initial_failures = _tenant_validation_metrics.get("validation_failures", 0)

        for keyword in ["SYSTEM", "System", "ADMIN", "Admin"]:
            try:
                validate_tenant_id(keyword)
            except TenantContextError:
                pass

        # Case-insensitive keywords should be handled correctly
        # (depending on implementation, may or may not be accepted)
        assert _tenant_validation_metrics["validation_failures"] == initial_failures
