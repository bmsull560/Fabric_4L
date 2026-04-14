"""Tests for API key hashing and verification (shared/identity/hashing.py)."""

import os
from unittest.mock import patch

import pytest

from ..hashing import (
    _get_hmac_secret,
    extract_key_prefix,
    generate_api_key,
    hash_api_key,
    verify_api_key,
)


class TestGenerateApiKey:
    """Tests for generate_api_key()."""

    def test_prefix(self):
        """Generated key starts with the vf_ prefix."""
        key = generate_api_key()
        assert key.startswith("vf_")

    def test_length(self):
        """Generated key is long enough to contain 256 bits of entropy."""
        key = generate_api_key()
        # vf_ (3 chars) + 43-char base64url string from 32 bytes
        assert len(key) >= 40

    def test_uniqueness(self):
        """Two generated keys are never equal."""
        keys = {generate_api_key() for _ in range(100)}
        assert len(keys) == 100

    def test_url_safe_characters(self):
        """Generated key only contains URL-safe characters."""
        key = generate_api_key()
        # After stripping the prefix, we should have base64url chars
        body = key[3:]
        for char in body:
            assert char.isalnum() or char in ("-", "_", "=")


class TestHashApiKey:
    """Tests for hash_api_key()."""

    @patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "test-secret-123"})
    def test_returns_hex_string(self):
        """Hash is a valid hex digest (SHA-256 = 64 hex chars)."""
        h = hash_api_key("vf_testkey")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)

    @patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "test-secret-123"})
    def test_deterministic(self):
        """Same key + same secret → same hash."""
        h1 = hash_api_key("vf_testkey")
        h2 = hash_api_key("vf_testkey")
        assert h1 == h2

    @patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "test-secret-123"})
    def test_different_keys_produce_different_hashes(self):
        """Different keys → different hashes."""
        h1 = hash_api_key("vf_key_one")
        h2 = hash_api_key("vf_key_two")
        assert h1 != h2

    def test_different_secrets_produce_different_hashes(self):
        """Different secrets → different hashes for the same key."""
        with patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "secret-A"}):
            h1 = hash_api_key("vf_same_key")
        with patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "secret-B"}):
            h2 = hash_api_key("vf_same_key")
        assert h1 != h2


class TestVerifyApiKey:
    """Tests for verify_api_key()."""

    @patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "verify-test-secret"})
    def test_valid_key_returns_true(self):
        """A correctly hashed key verifies successfully."""
        raw = generate_api_key()
        stored = hash_api_key(raw)
        assert verify_api_key(raw, stored) is True

    @patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "verify-test-secret"})
    def test_wrong_key_returns_false(self):
        """An incorrect key does not verify."""
        raw = generate_api_key()
        stored = hash_api_key(raw)
        assert verify_api_key("vf_wrong_key", stored) is False

    @patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "verify-test-secret"})
    def test_tampered_hash_returns_false(self):
        """A tampered hash fails verification."""
        raw = generate_api_key()
        stored = hash_api_key(raw)
        tampered = "a" * 64
        assert verify_api_key(raw, tampered) is False


class TestExtractKeyPrefix:
    """Tests for extract_key_prefix()."""

    def test_default_length(self):
        """Returns the first 12 characters by default."""
        key = "vf_abcdefghijklmnop"
        assert extract_key_prefix(key) == "vf_abcdefghi"
        assert len(extract_key_prefix(key)) == 12

    def test_custom_length(self):
        """Accepts a custom prefix length."""
        key = "vf_abcdefghijklmnop"
        assert extract_key_prefix(key, 5) == "vf_ab"

    def test_short_key(self):
        """Returns the whole key if shorter than the prefix length."""
        key = "vf_ab"
        assert extract_key_prefix(key) == "vf_ab"


class TestGetHmacSecret:
    """Tests for _get_hmac_secret()."""

    @patch.dict(os.environ, {"API_KEY_HMAC_SECRET": "my-strong-secret"})
    def test_returns_secret_from_env(self):
        """Reads the secret from the environment."""
        assert _get_hmac_secret() == b"my-strong-secret"

    @patch.dict(os.environ, {}, clear=True)
    def test_returns_empty_bytes_when_unset(self):
        """Falls back to empty bytes when env var is not set."""
        # Remove the key if it exists
        os.environ.pop("API_KEY_HMAC_SECRET", None)
        assert _get_hmac_secret() == b""

    @patch.dict(os.environ, {}, clear=True)
    def test_logs_warning_when_unset(self, caplog):
        """Logs a warning when the env var is missing."""
        os.environ.pop("API_KEY_HMAC_SECRET", None)
        import logging
        with caplog.at_level(logging.WARNING):
            _get_hmac_secret()
        assert "API_KEY_HMAC_SECRET is not set" in caplog.text
