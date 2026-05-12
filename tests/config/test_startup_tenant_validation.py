"""S2-J: Startup Tenant Validation Tests — Pillar 2 + Pillar 3.

Ship/No-Ship Gate: These tests verify that the application refuses to start
(or visibly degrades) when tenant-critical infrastructure is missing or
misconfigured.  They complement the existing test_startup_validation.py by
focusing specifically on tenant isolation prerequisites.

Expected Initial State:
    - test_startup_rejects_missing_jwt_secret_in_prod:     PASS
    - test_startup_rejects_weak_jwt_secret_in_prod:        FAIL (no length check)
    - test_startup_summary_reports_rls_status:              FAIL (no RLS in summary)
    - test_startup_validates_rls_prerequisites:             FAIL (no RLS validation)
    - test_degraded_redis_disables_rate_limiting:           PASS
    - test_degraded_redis_does_not_disable_auth:            PASS
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Module loading helper
# ---------------------------------------------------------------------------

def _load_security_config():
    """Load the security.config module directly to avoid sys.path issues
    when using patch.dict(clear=True)."""
    import importlib.util
    config_path = _PROJECT_ROOT / "value_fabric" / "shared" / "security" / "config.py"
    spec = importlib.util.spec_from_file_location("security_config", config_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Tests: JWT Secret Validation
# ---------------------------------------------------------------------------

class TestJWTSecretValidation:
    """Verify JWT secret is validated at startup."""

    def test_startup_rejects_missing_jwt_secret_in_prod(self):
        """Production startup must fail if JWT_SECRET is missing."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "",
            "DATABASE_URL": "postgresql://user:pass@localhost/db?sslmode=require",
            "REDIS_URL": "redis://localhost:6379",
        }, clear=True):
            mod = _load_security_config()
            with pytest.raises(ValueError, match="JWT_SECRET.*required.*production"):
                mod.validate_jwt_config()

    def test_startup_rejects_weak_jwt_secret_in_prod(self):
        """Production startup must fail if JWT_SECRET is too short.

        A JWT secret shorter than 32 characters is brute-forceable.
        Expected initial state: FAIL — no length validation exists.
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "short",
        }, clear=True):
            mod = _load_security_config()
            with pytest.raises(ValueError, match="JWT_SECRET.*at least 32"):
                mod.validate_jwt_config()

    def test_startup_rejects_default_jwt_secret_in_prod(self):
        """Production must reject known default/test JWT secrets."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "JWT_SECRET": "changeme",
        }, clear=True):
            mod = _load_security_config()
            with pytest.raises(ValueError, match="known default/test value"):
                mod.validate_jwt_config()


# ---------------------------------------------------------------------------
# Tests: Startup Summary Completeness
# ---------------------------------------------------------------------------

class TestStartupSummaryCompleteness:
    """Verify the startup summary reports tenant isolation status."""

    def test_startup_summary_reports_rls_status(self):
        """Startup summary must include RLS enforcement status.

        Expected initial state: FAIL — get_startup_summary() doesn't report RLS.
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql://user:pass@localhost/db?sslmode=require",
            "JWT_SECRET": "a" * 32,
            "REDIS_URL": "redis://localhost:6379",
            "AUDIT_SINK_URL": "http://localhost:9200",
            "CORS_ORIGINS": "https://app.example.com",
        }, clear=True):
            mod = _load_security_config()
            summary = mod.get_startup_summary()

            assert summary["rls_status"] == "active"
            assert summary["rls_enforcement"] == {
                "supported_backend": True,
                "superuser_connection": False,
                "enforced": True,
                "status": "enforced",
            }
            assert summary["degraded_control_status"]["is_degraded"] is False

    def test_startup_summary_reports_degraded_controls(self):
        """Startup summary must list degraded controls when Redis is missing."""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "JWT_SECRET": "a" * 32,
            "REDIS_URL": "",
        }, clear=True):
            mod = _load_security_config()
            summary = mod.get_startup_summary()

            degraded = summary.get("degraded_controls", [])
            assert "redis" in [c.lower() for c in degraded], (
                f"Startup summary does not report Redis as degraded. "
                f"Degraded controls: {degraded}"
            )
            assert "rate_limiting" in [c.lower() for c in degraded], (
                f"Startup summary does not report rate_limiting as degraded. "
                f"Degraded controls: {degraded}"
            )


# ---------------------------------------------------------------------------
# Tests: RLS Prerequisites
# ---------------------------------------------------------------------------

class TestRLSPrerequisiteValidation:
    """Verify startup validates RLS prerequisites."""

    def test_startup_validates_rls_prerequisites(self):
        """Production startup must validate that the database supports RLS.

        Expected initial state: FAIL — no RLS prerequisite check exists.
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DATABASE_URL": "mysql://user:pass@db/service",
        }, clear=True):
            mod = _load_security_config()
            with pytest.raises(ValueError, match="must use PostgreSQL"):
                mod.validate_rls_prerequisites()

    def test_startup_rejects_superuser_connection_in_prod(self):
        """Production must warn/reject if connecting as PostgreSQL superuser.

        Superuser roles bypass all RLS policies, making tenant isolation
        completely ineffective.

        Expected initial state: FAIL — no superuser detection exists.
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql://postgres:pass@db/service?sslmode=require",
        }, clear=True):
            mod = _load_security_config()
            with pytest.raises(ValueError, match="superuser"):
                mod.validate_rls_prerequisites()


# ---------------------------------------------------------------------------
# Tests: Degraded Dependency Behavior
# ---------------------------------------------------------------------------

class TestDegradedDependencyBehavior:
    """Verify correct behavior when dependencies are degraded."""

    def test_degraded_redis_does_not_disable_auth(self):
        """Missing Redis must NOT disable JWT authentication.

        Rate limiting can degrade gracefully, but authentication must
        never be optional — even if Redis is down.
        """
        # The startup summary should not list 'authentication' as degraded
        # when only Redis is missing
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DATABASE_URL": "postgresql://user:pass@localhost/db?sslmode=require",
            "JWT_SECRET": "a" * 32,
            "REDIS_URL": "",
            "AUDIT_SINK_URL": "http://localhost:9200",
            "CORS_ORIGINS": "https://app.example.com",
        }, clear=True):
            mod = _load_security_config()
            summary = mod.get_startup_summary()

            degraded = [c.lower() for c in summary.get("degraded_controls", [])]
            assert "authentication" not in degraded, (
                "Authentication is listed as degraded when Redis is missing. "
                "JWT authentication must NEVER degrade — it is the foundation "
                "of tenant isolation."
            )
            assert "jwt" not in degraded, (
                "JWT validation is listed as degraded when Redis is missing. "
                "JWT validation does not depend on Redis."
            )

    def test_degraded_audit_still_allows_startup(self):
        """Missing audit sink should warn but not prevent startup.

        Audit is important but not a hard dependency — the application
        should start with a warning, not crash.
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "staging",
            "DATABASE_URL": "postgresql://user:pass@localhost/db",
            "JWT_SECRET": "a" * 32,
            "REDIS_URL": "redis://localhost:6379",
            "AUDIT_SINK_URL": "",
            "CORS_ORIGINS": "https://app.example.com",
        }, clear=True):
            mod = _load_security_config()
            summary = mod.get_startup_summary()

            degraded = [c.lower() for c in summary.get("degraded_controls", [])]
            assert "audit" in degraded, (
                "Missing audit sink is not reported as degraded."
            )
            # The fact that we got here without an exception means startup
            # succeeded — which is the correct behavior for missing audit.
