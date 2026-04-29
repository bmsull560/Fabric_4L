"""JWT Configuration Validation Tests — P0 Critical Gap Remediation

Validates that JWT configuration is properly validated at startup,
especially in production environments.

Production Invariant: Production deployments must have secure JWT configuration.

Author: Autonomous Test Assurance Agent
Date: 2026-04-29
"""

from __future__ import annotations

import os
from unittest.mock import patch

import pytest


pytestmark = [
    pytest.mark.security,
    pytest.mark.jwt_config,
]


class TestProductionJWTSecretValidation:
    """P0: Production requires strong JWT secrets."""

    def test_production_requires_jwt_secret(self):
        """P0: Production startup fails without JWT_SECRET."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "",  # Empty
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            # Import and test the validation function
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                with pytest.raises(ValueError) as exc_info:
                    validate_jwt_config()
                
                assert "JWT_SECRET is required" in str(exc_info.value), (
                    "Production should require JWT_SECRET"
                )
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")

    def test_production_rejects_weak_jwt_secret(self):
        """P0: Production startup fails with weak JWT_SECRET (<32 chars)."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "short",  # Too short (only 5 chars)
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                with pytest.raises(ValueError) as exc_info:
                    validate_jwt_config()
                
                assert "at least 32 characters" in str(exc_info.value), (
                    "Production should reject weak JWT_SECRET"
                )
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")

    def test_production_rejects_31_char_secret(self):
        """P0: 31-character secret is rejected (need 32+)."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "a" * 31,  # Exactly 31 chars - should fail
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                with pytest.raises(ValueError) as exc_info:
                    validate_jwt_config()
                
                assert "at least 32 characters" in str(exc_info.value)
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")

    def test_production_accepts_32_char_secret(self):
        """POSITIVE: 32-character secret is accepted."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "a" * 32,  # Exactly 32 chars - should pass
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                # Should not raise
                validate_jwt_config()
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")


class TestProductionJWTIssuerValidation:
    """P0: Production requires JWT issuer."""

    def test_production_requires_jwt_issuer(self):
        """P0: Production startup fails without JWT_ISSUER."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "a" * 32,
            "JWT_ISSUER": "",  # Empty
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                with pytest.raises(ValueError) as exc_info:
                    validate_jwt_config()
                
                assert "JWT_ISSUER is required" in str(exc_info.value), (
                    "Production should require JWT_ISSUER"
                )
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")

    def test_production_rejects_missing_issuer(self):
        """P0: Production startup fails when JWT_ISSUER not set."""
        # Remove JWT_ISSUER from environment
        env_copy = os.environ.copy()
        env_copy.pop("JWT_ISSUER", None)
        env_copy["ENVIRONMENT"] = "production"
        env_copy["JWT_SECRET"] = "a" * 32
        env_copy["JWT_AUDIENCE"] = "test-audience"
        
        with patch.dict(os.environ, env_copy, clear=True):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                with pytest.raises(ValueError) as exc_info:
                    validate_jwt_config()
                
                assert "JWT_ISSUER is required" in str(exc_info.value)
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")


class TestProductionJWTAudienceValidation:
    """P0: Production requires JWT audience."""

    def test_production_requires_jwt_audience(self):
        """P0: Production startup fails without JWT_AUDIENCE."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "a" * 32,
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "",  # Empty
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                with pytest.raises(ValueError) as exc_info:
                    validate_jwt_config()
                
                assert "JWT_AUDIENCE is required" in str(exc_info.value), (
                    "Production should require JWT_AUDIENCE"
                )
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")


class TestDevelopmentEnvironment:
    """Development environment is more permissive."""

    def test_development_allows_missing_jwt_secret(self):
        """Development allows missing JWT_SECRET."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "JWT_SECRET": "",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                # Should not raise in development
                validate_jwt_config()
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")

    def test_development_allows_weak_jwt_secret(self):
        """Development allows weak JWT_SECRET."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "development",
            "JWT_SECRET": "weak",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                # Should not raise in development
                validate_jwt_config()
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")


class TestStagingEnvironment:
    """Staging environment should match production validation."""

    def test_staging_requires_jwt_secret(self):
        """P0: Staging should validate like production."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "JWT_SECRET": "",
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                # Staging should enforce production-like validation
                with pytest.raises(ValueError) as exc_info:
                    validate_jwt_config()
                
                assert "JWT_SECRET is required" in str(exc_info.value)
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")


class TestEdgeCases:
    """Edge cases for JWT configuration."""

    def test_jwt_secret_with_special_characters_accepted(self):
        """Special characters in JWT secret are handled."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "my$ecr3t!@#$%^&*()_+key-that-is-32chars",
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                # Should not raise - special chars should be fine
                validate_jwt_config()
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")

    def test_very_long_jwt_secret_accepted(self):
        """Very long JWT secrets are accepted."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "a" * 128,  # 128 chars
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                # Should not raise
                validate_jwt_config()
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")

    def test_unicode_jwt_secret_handled(self):
        """Unicode characters in JWT secret are handled."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "🔐secret-key-with-32-chars!!🔐🔐🔐",
            "JWT_ISSUER": "test-issuer",
            "JWT_AUDIENCE": "test-audience",
        }, clear=False):
            try:
                from shared.identity.dependencies import validate_jwt_config
                
                # Should not raise or crash
                validate_jwt_config()
            except ImportError:
                pytest.skip("shared.identity.dependencies not available")
