"""Security regression tests for auth bypass guardrails."""

from __future__ import annotations

import pytest

from value_fabric.shared.security import validate_production_safety


def test_production_rejects_all_bypass_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    base_env = {
        "ENVIRONMENT": "production",
        "JWT_SECRET": "x" * 48,
        "DATABASE_URL": "postgresql://app_user:securepassword@db.internal:5432/valuefabric",
        "CREDENTIALS_MASTER_KEY": "x" * 48,
        "API_KEY_HMAC_SECRET": "x" * 48,
        "CORS_ORIGINS": "https://app.example.com",
        "DEFAULT_TENANT_ID": "00000000-0000-4000-a000-000000000001",
        "SERVICE_AUTH_SECRET": "x" * 48,
        "MULTI_TENANT_MODE": "true",
        "LLM_PROVIDER": "openai",
    }
    for key, value in base_env.items():
        monkeypatch.setenv(key, value)

    for bypass_var, bypass_value in (
        ("ALLOW_INSECURE_DEV_AUTH_BYPASS", "true"),
        ("DEV_AUTH_BYPASS", "true"),
        ("ALLOW_DEV_AUTH_BYPASS", "I_UNDERSTAND_RISK"),
        ("AUTH_BYPASS_ENABLED", "true"),
    ):
        monkeypatch.setenv(bypass_var, bypass_value)
        with pytest.raises(RuntimeError, match=bypass_var):
            validate_production_safety(environment="production")
        monkeypatch.delenv(bypass_var)
