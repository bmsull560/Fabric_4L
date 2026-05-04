import importlib
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
SHARED_SRC = REPO_ROOT / "packages" / "shared" / "src"
if str(SHARED_SRC) not in sys.path:
    sys.path.insert(0, str(SHARED_SRC))


def _load_config(monkeypatch, **env):
    for key in ("ENVIRONMENT", "ENV", "APP_ENV", "CORS_ORIGINS", "JWT_SECRET", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    module = importlib.import_module("shared.config")
    return importlib.reload(module)


def test_layer1_treats_unknown_environment_as_production_like(monkeypatch):
    config = _load_config(monkeypatch, ENVIRONMENT="development")

    with pytest.raises(Exception, match="Unsafe production configuration") as exc_info:
        config.Settings(environment="qa")

    assert "CORS_ORIGINS" in str(exc_info.value)
    assert "JWT secret" in str(exc_info.value)


def test_layer1_rejects_wildcard_and_placeholder_cors_in_production_like_env(monkeypatch):
    config = _load_config(monkeypatch, ENVIRONMENT="development")

    with pytest.raises(Exception, match="Unsafe production configuration") as exc_info:
        config.Settings(
            environment="production",
            jwt_secret="x" * 48,
            database_url="postgresql://fabric:example@db.internal:5432/layer1",
            cors_origins=["https://*.example.com", "CHANGE_ME"],
        )

    message = str(exc_info.value)
    assert "Wildcard CORS" in message
    assert "deployable origin" in message


def test_layer1_cors_policy_uses_explicit_origins_methods_and_headers(monkeypatch):
    config = _load_config(monkeypatch, ENVIRONMENT="development")
    settings = config.Settings(
        environment="production",
        jwt_secret="x" * 48,
        database_url="postgresql://fabric:example@db.internal:5432/layer1",
        cors_origins=["https://app.example.com"],
    )

    assert settings.cors_policy == {
        "allow_origins": ["https://app.example.com"],
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Authorization", "Content-Type", "X-Request-ID", "X-Tenant-ID"],
    }


def test_layer1_development_default_cors_is_localhost_not_wildcard(monkeypatch):
    config = _load_config(monkeypatch, ENVIRONMENT="development")
    settings = config.Settings(environment="development")

    assert settings.cors_policy["allow_origins"] == ["http://localhost:5173", "http://localhost:3000"]
    assert settings.cors_policy["allow_credentials"] is True
    assert "*" not in settings.cors_policy["allow_methods"]
    assert "*" not in settings.cors_policy["allow_headers"]
