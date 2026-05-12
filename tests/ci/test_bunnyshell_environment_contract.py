from __future__ import annotations

from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
BUNNYSHELL_PATH = REPO_ROOT / "bunnyshell.yaml"


def _load_bunnyshell() -> dict:
    with BUNNYSHELL_PATH.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _component(config: dict, name: str) -> dict:
    for component in config["components"]:
        if component["name"] == name:
            return component
    raise AssertionError(f"missing Bunnyshell component: {name}")


def test_bunnyshell_yaml_parses():
    config = _load_bunnyshell()

    assert config["kind"] == "Environment"
    assert isinstance(config["components"], list)


def test_bunnyshell_has_no_deployable_secret_fallbacks_or_placeholders():
    text = BUNNYSHELL_PATH.read_text(encoding="utf-8")

    forbidden_fragments = [
        ":-postgres",
        ":-devpassword",
        ":-minioadmin",
        ":-dev-redis-password",
        "postgres:postgres",
        "redis://redis:6379",
        "sk-placeholder-change-in-production",
        "sk-ant-placeholder-change-in-production",
        "DEV_AUTH_BYPASS",
        "POSTGRES_HOST_AUTH_METHOD: trust",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in text


def test_bunnyshell_datastore_credentials_use_required_environment_variables():
    config = _load_bunnyshell()
    postgres_env = _component(config, "postgres")["dockerCompose"]["environment"]
    redis_compose = _component(config, "redis")["dockerCompose"]
    minio_env = _component(config, "minio")["dockerCompose"]["environment"]
    neo4j_env = _component(config, "neo4j")["dockerCompose"]["environment"]

    assert postgres_env["POSTGRES_USER"] == "${POSTGRES_USER}"
    assert postgres_env["POSTGRES_PASSWORD"] == "${POSTGRES_PASSWORD}"
    assert redis_compose["environment"]["REDIS_PASSWORD"] == "${REDIS_PASSWORD}"
    assert redis_compose["command"] == [
        "redis-server",
        "--requirepass",
        "${REDIS_PASSWORD}",
    ]
    assert redis_compose["healthcheck"]["test"] == [
        "CMD-SHELL",
        'redis-cli -a "$REDIS_PASSWORD" ping',
    ]
    assert minio_env["MINIO_ROOT_USER"] == "${MINIO_ROOT_USER}"
    assert minio_env["MINIO_ROOT_PASSWORD"] == "${MINIO_ROOT_PASSWORD}"
    assert neo4j_env["NEO4J_AUTH"] == "neo4j/${NEO4J_PASSWORD}"


def test_bunnyshell_application_credentials_are_required_and_auth_bypass_is_disabled():
    config = _load_bunnyshell()

    for name in ("layer1", "layer1-worker"):
        env = _component(config, name)["dockerCompose"]["environment"]
        assert env["LAYER1_DATABASE_URL"] == (
            "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/ingestion"
        )
        assert env["LAYER1_REDIS_URL"] == "redis://:${REDIS_PASSWORD}@redis:6379/0"
        assert env["LAYER1_S3_ACCESS_KEY"] == "${MINIO_ROOT_USER}"
        assert env["LAYER1_S3_SECRET_KEY"] == "${MINIO_ROOT_PASSWORD}"

    layer2_env = _component(config, "layer2")["dockerCompose"]["environment"]
    assert layer2_env["LAYER2_DATABASE_URL"] == (
        "postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/layer2_extraction"
    )
    assert layer2_env["OPENAI_API_KEY"] == "${OPENAI_API_KEY}"
    assert layer2_env["REDIS_URL"] == "redis://:${REDIS_PASSWORD}@redis:6379/0"

    layer4_env = _component(config, "layer4")["dockerCompose"]["environment"]
    assert "DEV_AUTH_BYPASS" not in layer4_env
    assert layer4_env["ANTHROPIC_API_KEY"] == "${ANTHROPIC_API_KEY}"
    assert layer4_env["OPENAI_API_KEY"] == "${OPENAI_API_KEY}"
    assert layer4_env["DATABASE_URL"] == (
        "postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/layer4_agents"
    )
    assert layer4_env["CHECKPOINT_DATABASE_URL"] == (
        "postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgres:5432/ground_truth"
    )


def test_bunnyshell_layer4_ingress_targets_container_service_port():
    config = _load_bunnyshell()
    layer4 = _component(config, "layer4")

    assert layer4["dockerCompose"]["ports"] == ["8004:8000"]
    assert layer4["hosts"] == [
        {
            "hostname": "layer4-{{ env.base_domain }}",
            "path": "/",
            "servicePort": 8000,
        }
    ]
