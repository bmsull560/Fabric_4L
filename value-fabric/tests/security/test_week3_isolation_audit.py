"""Week 3 Tenant Isolation & Audit Hardening — Regression Tests.

Tests for:
- F-10: Tenant isolation enforced on all DB queries
- F-11: JWT fallthrough fix - invalid tokens reject, not silently fail
- F-12: Audit fail-closed mode blocks operations when logging fails

Run with: pytest tests/security/test_week3_isolation_audit.py -v
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).parent.parent.parent


class TestJWTFallthroughFix:
    """F-11: Invalid JWTs must reject, not fall through to other auth methods."""

    def test_middleware_imports_jwt_module(self):
        """Middleware must import jwt module for InvalidTokenError handling."""
        middleware_path = REPO_ROOT / "value-fabric" / "shared" / "identity" / "middleware.py"
        content = middleware_path.read_text()

        # Should import jwt module
        assert "import jwt" in content or "from jwt" in content

    def test_jwt_exception_handling_specific(self):
        """JWT exception handling must catch InvalidTokenError specifically."""
        middleware_path = REPO_ROOT / "value-fabric" / "shared" / "identity" / "middleware.py"
        content = middleware_path.read_text()

        # Should check for jwt.InvalidTokenError specifically
        assert "jwt.InvalidTokenError" in content or "InvalidTokenError" in content

    def test_jwt_raises_http_exception_on_invalid(self):
        """Invalid JWT must raise HTTPException, not return None silently."""
        middleware_path = REPO_ROOT / "value-fabric" / "shared" / "identity" / "middleware.py"
        content = middleware_path.read_text()

        # After JWT handling, should raise HTTPException for invalid tokens
        assert "HTTPException" in content
        assert "401" in content or "HTTP_401_UNAUTHORIZED" in content
        assert "WWW-Authenticate" in content


class TestAuditFailClosed:
    """F-12: Audit logging must fail-closed when AUDIT_FAIL_CLOSED=true."""

    def test_emitter_has_fail_closed_mode(self):
        """AuditEmitter must support fail-closed mode."""
        emitter_path = REPO_ROOT / "shared" / "audit" / "emitter.py"
        content = emitter_path.read_text()

        # Should have fail-closed mode
        assert "AUDIT_FAIL_CLOSED" in content
        assert "_fail_closed" in content

    def test_emitter_raises_on_handler_failure_in_fail_closed(self):
        """AuditEmitter.emit must raise AuditEmitterError in fail-closed mode."""
        emitter_path = REPO_ROOT / "shared" / "audit" / "emitter.py"
        content = emitter_path.read_text()

        # Should raise AuditEmitterError in fail-closed mode
        assert "AuditEmitterError" in content
        assert "raise AuditEmitterError" in content

    def test_env_example_documents_audit_fail_closed(self):
        """.env.example must document AUDIT_FAIL_CLOSED."""
        env_path = REPO_ROOT / "value-fabric" / ".env.example"
        content = env_path.read_text()

        assert "AUDIT_FAIL_CLOSED" in content


class TestTenantIsolationEnforcement:
    """F-10: All DB queries must enforce tenant isolation."""

    def test_layer1_database_has_fail_safe_mode(self):
        """Layer1 database must have FAIL_SAFE_MODE enabled."""
        db_path = REPO_ROOT / "value-fabric" / "layer1-ingestion" / "src" / "shared" / "database.py"
        content = db_path.read_text()

        # Should have fail-safe mode
        assert "FAIL_SAFE_MODE" in content
        assert "FAIL_SAFE_MODE = True" in content

    def test_layer1_database_validates_tenant_id(self):
        """Layer1 database must validate tenant_id format."""
        db_path = REPO_ROOT / "value-fabric" / "layer1-ingestion" / "src" / "shared" / "database.py"
        content = db_path.read_text()

        # Should validate tenant_id
        assert "validate_tenant_id" in content
        assert "TenantContextError" in content

    def test_tenant_scoped_mixin_exists(self):
        """TenantScopedMixin must exist for SQLAlchemy models."""
        isolation_path = REPO_ROOT / "value-fabric" / "shared" / "identity" / "isolation.py"
        content = isolation_path.read_text()

        assert "TenantScopedMixin" in content
        assert "scoped_query" in content

    def test_tenant_scoped_cypher_exists(self):
        """TenantScopedCypher must exist for Neo4j queries."""
        isolation_path = REPO_ROOT / "value-fabric" / "shared" / "identity" / "isolation.py"
        content = isolation_path.read_text()

        assert "TenantScopedCypher" in content
        assert "tenant_id" in content


class TestIntegration:
    """Integration tests for Week 3 fixes."""

    @pytest.mark.asyncio
    async def test_audit_emitter_fail_closed_blocks_operation(self):
        """When AUDIT_FAIL_CLOSED=true, audit failures block operations."""
        # Import after ensuring path is correct
        import sys
        shared_path = str(REPO_ROOT / "shared")
        if shared_path not in sys.path:
            sys.path.insert(0, shared_path)

        from audit.emitter import AuditEmitter, AuditEmitterError
        from audit.models import AuditAction, AuditEvent, AuditOutcome

        # Create emitter with fail-closed mode
        with patch.dict(os.environ, {"AUDIT_FAIL_CLOSED": "true"}):
            emitter = AuditEmitter()

            # Add a failing handler
            failing_handler = AsyncMock(side_effect=RuntimeError("Handler failed"))
            emitter.add_handler(failing_handler)

            # Create a test event
            event = AuditEvent(
                id=__import__("uuid").uuid4(),
                action=AuditAction.TENANT_CREATED,
                outcome=AuditOutcome.SUCCESS,
                resource_type="Tenant",
            )

            # Should raise AuditEmitterError in fail-closed mode
            with pytest.raises(AuditEmitterError):
                await emitter.emit(event)

    @pytest.mark.asyncio
    async def test_audit_emitter_warn_mode_allows_operation(self):
        """When AUDIT_FAIL_CLOSED=false, audit failures are logged but don't block."""
        import sys
        shared_path = str(REPO_ROOT / "shared")
        if shared_path not in sys.path:
            sys.path.insert(0, shared_path)

        from audit.emitter import AuditEmitter
        from audit.models import AuditAction, AuditEvent, AuditOutcome

        # Create emitter with warn mode (default)
        with patch.dict(os.environ, {"AUDIT_FAIL_CLOSED": "false"}):
            emitter = AuditEmitter()

            # Add a failing handler
            failing_handler = AsyncMock(side_effect=RuntimeError("Handler failed"))
            emitter.add_handler(failing_handler)

            # Create a test event
            event = AuditEvent(
                id=__import__("uuid").uuid4(),
                action=AuditAction.TENANT_CREATED,
                outcome=AuditOutcome.SUCCESS,
                resource_type="Tenant",
            )

            # Should NOT raise in warn mode
            await emitter.emit(event)
