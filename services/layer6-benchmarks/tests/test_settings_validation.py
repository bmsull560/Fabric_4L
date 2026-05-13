import pytest
from pydantic import ValidationError

from value_fabric.layer6.settings import Layer6Settings


def _base_env() -> dict[str, str]:
    return {
        "ENVIRONMENT": "test",
        "DATABASE_URL": "postgresql+asyncpg://postgres:postgres@localhost:5432/fabric",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "strong-password-123",
        "JWT_SECRET": "j" * 32,
        "API_KEY_HMAC_SECRET": "a" * 32,
        "SERVICE_AUTH_SECRET": "s" * 32,
    }


def test_missing_critical_secret_fails_validation() -> None:
    env = _base_env()
    env["JWT_SECRET"] = ""

    with pytest.raises(ValidationError):
        Layer6Settings.model_validate(env)


def test_short_service_auth_secret_fails_validation() -> None:
    env = _base_env()
    env["SERVICE_AUTH_SECRET"] = "too-short"

    with pytest.raises(ValidationError):
        Layer6Settings.model_validate(env)


def test_production_database_sslmode_is_required() -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    env["DATABASE_URL"] = "postgresql://postgres:postgres@db:5432/fabric"

    with pytest.raises(ValidationError, match="sslmode"):
        Layer6Settings.model_validate(env)


def test_production_neo4j_requires_tls_scheme() -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    env["DATABASE_URL"] = "postgresql://postgres:postgres@db:5432/fabric?sslmode=require"
    env["NEO4J_URI"] = "bolt://neo4j:7687"

    with pytest.raises(ValidationError, match="NEO4J_URI"):
        Layer6Settings.model_validate(env)


def test_production_config_passes_with_secure_values() -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    env["DATABASE_URL"] = "postgresql://postgres:postgres@db:5432/fabric?sslmode=verify-full"
    env["NEO4J_URI"] = "neo4j+s://neo4j.example.com:7687"

    settings = Layer6Settings.model_validate(env)

    assert settings.environment == "production"


@pytest.mark.parametrize(
    ("flag_name", "flag_value"),
    [
        ("ALLOW_INSECURE_DEV_AUTH_BYPASS", "true"),
        ("DEV_AUTH_BYPASS", "true"),
        ("AUTH_BYPASS_ENABLED", "true"),
        ("JWT_FALLBACK_TO_QUERY_PARAM", "true"),
        ("ALLOW_EPHEMERAL_ENCRYPTION", "true"),
        ("ALLOW_DEV_AUTH_BYPASS", "I_UNDERSTAND_RISK"),
    ],
)
def test_production_rejects_bypass_flags(flag_name: str, flag_value: str) -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "production"
    env["DATABASE_URL"] = "postgresql://postgres:postgres@db:5432/fabric?sslmode=verify-full"
    env["NEO4J_URI"] = "neo4j+s://neo4j.example.com:7687"
    env[flag_name] = flag_value

    with pytest.raises(ValidationError, match=flag_name):
        Layer6Settings.model_validate(env)


def test_non_production_can_explicitly_enable_bypass_flag() -> None:
    env = _base_env()
    env["ENVIRONMENT"] = "test"
    env["ALLOW_INSECURE_DEV_AUTH_BYPASS"] = "true"

    settings = Layer6Settings.model_validate(env)

    assert settings.allow_insecure_dev_auth_bypass is True
