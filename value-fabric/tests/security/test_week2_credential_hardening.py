"""Week 2 Credential Hardening — Regression Tests.

Tests for:
- F-4: K8s postgres credentials moved to secretKeyRef
- F-5: Grafana credentials from env vars
- F-6: Vault dev mode blocked in production
- F-7: Redis requirepass authentication
- F-8: Flower basic auth
- F-9: CORS fail-closed in production

Run with: pytest tests/security/test_week2_credential_hardening.py -v
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent.parent


class TestK8sCredentialHardening:
    """F-4: K8s manifests must not contain hardcoded credentials."""

    def test_layer1_no_hardcoded_database_url(self):
        """Layer1 ingestion must use secretKeyRef for DATABASE_URL."""
        manifest_path = REPO_ROOT / "k8s" / "base" / "layer1-ingestion.yml"
        content = manifest_path.read_text()

        # Should not contain hardcoded postgres://user:password@
        hardcoded_pattern = r'value:\s*"postgresql://[^"]+:[^@]+@'
        matches = re.findall(hardcoded_pattern, content)

        assert len(matches) == 0, f"Found hardcoded DB credentials: {matches}"

    def test_layer1_uses_secretkeyref(self):
        """Layer1 must reference secrets via secretKeyRef."""
        manifest_path = REPO_ROOT / "k8s" / "base" / "layer1-ingestion.yml"
        content = manifest_path.read_text()

        # Should contain secretKeyRef for DATABASE_URL
        assert "secretKeyRef:" in content
        assert "layer1-db-credentials" in content


class TestDockerComposeCredentialHardening:
    """F-5, F-7, F-8: docker-compose must use env vars for credentials."""

    @pytest.fixture
    def compose_content(self):
        """Load docker-compose.yml content."""
        compose_path = REPO_ROOT / "value-fabric" / "docker-compose.yml"
        return compose_path.read_text()

    def test_redis_requires_password(self, compose_content):
        """Redis must use --requirepass with env var."""
        assert "--requirepass ${REDIS_PASSWORD:?REDIS_PASSWORD is required}" in compose_content

    def test_grafana_uses_env_password(self, compose_content):
        """Grafana admin password must come from env var."""
        assert "${GRAFANA_ADMIN_PASSWORD:?" in compose_content

    def test_flower_uses_basic_auth(self, compose_content):
        """Flower must use --basic_auth with env vars."""
        assert "--basic_auth=${FLOWER_USER" in compose_content
        assert "${FLOWER_PASSWORD:?" in compose_content

    def test_flower_has_env_vars(self, compose_content):
        """Flower service must define FLOWER_USER and FLOWER_PASSWORD env vars."""
        # Check that env vars are passed through
        assert "FLOWER_USER=${FLOWER_USER" in compose_content
        assert "FLOWER_PASSWORD=${FLOWER_PASSWORD" in compose_content


class TestVaultDevModeGuard:
    """F-6: Vault dev mode must be guarded by profile."""

    def test_vault_has_dev_profile(self):
        """Vault service must only start with --profile dev."""
        compose_path = REPO_ROOT / "value-fabric" / "docker-compose.yml"
        content = compose_path.read_text()

        # Find vault service section
        vault_match = re.search(
            r"vault:.*?\n\n", content, re.DOTALL
        )
        assert vault_match, "Vault service not found"
        vault_section = vault_match.group(0)

        # Must have profiles: - dev
        assert "profiles:" in vault_section
        assert "- dev" in vault_section


class TestCorsFailClosed:
    """F-9: CORS must fail-closed in production."""

    def test_cors_wildcard_blocked_in_production(self):
        """Wildcard CORS origins must raise RuntimeError in production."""
        # Patch os.environ to simulate production without CORS_ORIGINS
        test_env = {
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "",  # Empty = wildcard
        }

        with patch.dict(os.environ, test_env, clear=False):
            # Importing the module should trigger the check
            # We need to reimport to trigger the module-level code
            import importlib
            import sys

            # Remove the module to force reimport
            module_names = [
                "value-fabric.layer4-agents.src.api.main",
                "layer4_agents.src.api.main",
            ]
            for name in list(sys.modules.keys()):
                if "main" in name and "layer4" in name:
                    del sys.modules[name]

            # This should raise RuntimeError
            with pytest.raises(RuntimeError) as exc_info:
                # Import the main module which runs the CORS check
                from layer4_agents.src.api import main

            assert "CORS_ORIGINS must be set" in str(exc_info.value)

    def test_cors_wildcard_allowed_in_development(self):
        """Wildcard CORS origins should only warn in development."""
        test_env = {
            "ENVIRONMENT": "development",
            "CORS_ORIGINS": "",  # Empty = wildcard
        }

        with patch.dict(os.environ, test_env, clear=False):
            # Should not raise in development
            import importlib
            import sys

            # Clear cached module
            for name in list(sys.modules.keys()):
                if "main" in name and "layer4" in name:
                    del sys.modules[name]

            # This should NOT raise
            try:
                from layer4_agents.src.api import main
            except RuntimeError as e:
                if "CORS_ORIGINS" in str(e):
                    pytest.fail("Should not raise RuntimeError in development")


class TestEnvExampleCompleteness:
    """Verify .env.example documents all required secrets."""

    def test_env_example_has_service_auth_secret(self):
        """.env.example must document SERVICE_AUTH_SECRET."""
        env_path = REPO_ROOT / "value-fabric" / ".env.example"
        content = env_path.read_text()

        assert "SERVICE_AUTH_SECRET=" in content

    def test_env_example_has_redis_password(self):
        """.env.example must document REDIS_PASSWORD."""
        env_path = REPO_ROOT / "value-fabric" / ".env.example"
        content = env_path.read_text()

        assert "REDIS_PASSWORD=" in content

    def test_env_example_has_grafana_password(self):
        """.env.example must document GRAFANA_ADMIN_PASSWORD."""
        env_path = REPO_ROOT / "value-fabric" / ".env.example"
        content = env_path.read_text()

        assert "GRAFANA_ADMIN_PASSWORD=" in content

    def test_env_example_has_flower_password(self):
        """.env.example must document FLOWER_PASSWORD."""
        env_path = REPO_ROOT / "value-fabric" / ".env.example"
        content = env_path.read_text()

        assert "FLOWER_PASSWORD=" in content

    def test_env_example_has_cors_origins(self):
        """.env.example must document CORS_ORIGINS."""
        env_path = REPO_ROOT / "value-fabric" / ".env.example"
        content = env_path.read_text()

        assert "CORS_ORIGINS=" in content
