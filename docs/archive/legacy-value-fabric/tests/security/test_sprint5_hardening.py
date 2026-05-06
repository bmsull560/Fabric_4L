# Migrated from tests/security/test_sprint5_hardening.py during legacy path cleanup.

"""
Sprint 5 Security Hardening — Regression Tests.

Tests for every fix applied during the security review:
  FIX-C1: GovernanceMiddleware sets governance_context on request.state
  FIX-C2: REGISTRY_TOKEN removed from committed .env.production / .env.staging
  FIX-H1: GovernanceMiddleware rejects unauthenticated requests with 401
  FIX-H2: VITE_ENABLE_MOCK_FALLBACK=false in staging
  FIX-H3: Tenant ID not leaked in error response bodies
  FIX-H4: dependencies.py reads governance_context
  FIX-H5: L3 tests use governance_context
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]  # Fabric_4L/

# Build the old (banned) pattern via concatenation so the CI lint regex
# (which scans for the literal string) does not flag this test file itself.
_OLD_ATTR = "request.state" + ".context"
_OLD_ASSIGN = _OLD_ATTR + " = context"
_OLD_REGEX = re.compile(r"request\.state" + r"\.context\b")


def _read_file(rel_path: str) -> str:
    """Read a file relative to the project root."""
    return (PROJECT_ROOT / rel_path).read_text(encoding="utf-8")


# ===========================================================================
# FIX-C1 / FIX-H4: governance_context attribute alignment
# ===========================================================================
class TestGovernanceContextAttribute:
    """Verify that middleware and dependencies use the canonical attribute name."""

    def test_shared_middleware_sets_governance_context(self):
        """shared/identity/middleware.py must set governance_context on request.state."""
        src = _read_file("shared/identity/middleware.py")
        assert "request.state.governance_context = context" in src, (
            "GovernanceMiddleware must set governance_context on request.state"
        )
        # Must NOT use the old pattern
        assert _OLD_ASSIGN not in src, (
            "Old attribute pattern still present in middleware"
        )

    def test_shared_dependencies_reads_governance_context(self):
        """shared/identity/dependencies.py must read governance_context."""
        src = _read_file("shared/identity/dependencies.py")
        assert 'getattr(request.state, "governance_context"' in src, (
            "dependencies.py must read governance_context"
        )

    def test_dil_auth_reads_governance_context(self):
        """services/shared/security/dil_auth.py must read governance_context."""
        src = _read_file("services/shared/security/dil_auth.py")
        assert 'getattr(request.state, "governance_context"' in src, (
            "dil_auth.py must read governance_context"
        )

    def test_l3_tests_use_governance_context(self):
        """L3 test files must reference governance_context, not the old attribute."""
        for rel in (
            "services/layer3-knowledge/tests/test_tenant_context_extraction.py",
            "services/layer3-knowledge/tests/test_tenant_isolation.py",
        ):
            src = _read_file(rel)
            occurrences = _OLD_REGEX.findall(src)
            assert len(occurrences) == 0, (
                f"{rel} still uses old attribute pattern"
            )


# ===========================================================================
# FIX-C2: No hardcoded secrets in committed env files
# ===========================================================================
class TestNoHardcodedSecrets:
    """REGISTRY_TOKEN must not be hardcoded in production or staging env files."""

    @pytest.mark.parametrize("env_file", [".env.production", ".env.staging"])
    def test_registry_token_not_hardcoded(self, env_file):
        src = _read_file(f"frontend/{env_file}")
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            if stripped.startswith("REGISTRY_TOKEN="):
                value = stripped.split("=", 1)[1].strip()
                assert value == "", (
                    f"REGISTRY_TOKEN has a hardcoded value in {env_file}: {value[:20]}..."
                )


# ===========================================================================
# FIX-H1: GovernanceMiddleware rejects unauthenticated requests
# ===========================================================================
class TestMiddlewareRejectsUnauthenticated:
    """GovernanceMiddleware.dispatch() must return 401 when no tenant resolved."""

    def test_dispatch_contains_401_guard(self):
        """The dispatch method must check for missing tenant_id and return 401."""
        src = _read_file("shared/identity/middleware.py")
        assert "not context.tenant_id" in src, (
            "Middleware must check for missing tenant_id"
        )
        assert "status_code=401" in src or "status_code = 401" in src, (
            "Middleware must return 401 for unauthenticated requests"
        )
        assert "WWW-Authenticate" in src, (
            "401 response must include WWW-Authenticate header"
        )


# ===========================================================================
# FIX-H2: Mock fallback disabled in staging
# ===========================================================================
class TestMockFallbackDisabledInStaging:
    """VITE_ENABLE_MOCK_FALLBACK must be false in staging."""

    def test_staging_mock_fallback_false(self):
        src = _read_file("frontend/.env.staging")
        for line in src.splitlines():
            stripped = line.strip()
            if stripped.startswith("VITE_ENABLE_MOCK_FALLBACK="):
                value = stripped.split("=", 1)[1].strip().lower()
                assert value == "false", (
                    f"VITE_ENABLE_MOCK_FALLBACK must be false in staging, got: {value}"
                )
                return
        pytest.fail("VITE_ENABLE_MOCK_FALLBACK not found in .env.staging")


# ===========================================================================
# FIX-H3: No tenant_id in error response bodies
# ===========================================================================
class TestNoTenantIdInErrorResponses:
    """Error responses must not leak internal tenant IDs."""

    def test_no_tenant_id_in_middleware_error_responses(self):
        """Middleware error responses must not include tenant_id field."""
        src = _read_file("shared/identity/middleware.py")
        response_contents = re.findall(r"content='([^']+)'", src)
        for content in response_contents:
            assert "tenant_id" not in content, (
                f"Error response body leaks tenant_id: {content[:80]}..."
            )


# ===========================================================================
# FIX-H5: Platform contract lint passes for old_request_state
# ===========================================================================
class TestPlatformContractCompliance:
    """CI lint patterns must not fire on our fixed files."""

    @pytest.mark.parametrize("rel_path", [
        "shared/identity/middleware.py",
        "shared/identity/dependencies.py",
        "services/layer3-knowledge/tests/test_tenant_context_extraction.py",
        "services/layer3-knowledge/tests/test_tenant_isolation.py",
    ])
    def test_no_old_request_state_pattern(self, rel_path):
        src = _read_file(rel_path)
        matches = _OLD_REGEX.findall(src)
        assert len(matches) == 0, (
            f"{rel_path} still contains {len(matches)} old attribute patterns"
        )
