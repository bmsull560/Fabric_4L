"""Regression tests for P0-5: API Key rejection in layers without DB access.

These tests verify that layers without database access properly reject API key
authentication with clear logging.
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from shared.identity.api_key_stub import (
    reject_api_key_unsupported,
    reject_api_key_with_error,
)


class TestApiKeyRejection:
    """Test API key rejection in layers without database access."""

    def test_reject_api_key_unsupported_returns_none(self):
        """reject_api_key_unsupported must always return None."""
        result = reject_api_key_unsupported("some-api-key")
        assert result is None

    def test_reject_api_key_unsupported_logs_warning(self, caplog):
        """reject_api_key_unsupported must log a warning."""
        with caplog.at_level(logging.WARNING):
            reject_api_key_unsupported("test-key-123")

        assert "API key authentication rejected" in caplog.text
        assert "Use JWT Bearer tokens instead" in caplog.text

    def test_reject_api_key_with_error_returns_none(self):
        """reject_api_key_with_error must always return None."""
        result = reject_api_key_with_error("some-api-key")
        assert result is None

    def test_reject_api_key_with_error_logs_error(self, caplog):
        """reject_api_key_with_error must log an error."""
        with caplog.at_level(logging.ERROR):
            reject_api_key_with_error("test-key-123")

        assert "rejected" in caplog.text
        assert "disabled in this layer" in caplog.text

    def test_reject_api_key_does_not_leak_full_key(self, caplog):
        """Only first 8 characters of key should be logged."""
        with caplog.at_level(logging.ERROR):
            reject_api_key_with_error("super-secret-key-that-is-long")

        # Should log truncated key
        assert "super-sec" not in caplog.text
        assert "super-se" in caplog.text or "'super" in caplog.text
