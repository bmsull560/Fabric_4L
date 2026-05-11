from __future__ import annotations

import importlib.util
import os
import shutil
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "ci" / "check_docker_compose_config.py"


def load_module():
    spec = importlib.util.spec_from_file_location("check_docker_compose_config", SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_file(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def repo_tmp_path(name: str) -> Path:
    path = REPO_ROOT / ".tmp" / "docker-compose-config-tests" / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def test_bind_mount_classification_ignores_named_and_anonymous_volumes():
    module = load_module()

    service = {
        "volumes": [
            "named-data:/var/lib/data",
            "/app/node_modules",
            "./scripts/init.sh:/docker-entrypoint-initdb.d/init.sh:ro",
            {"type": "volume", "source": "cache", "target": "/cache"},
            {"type": "bind", "source": "./config.yml", "target": "/etc/config.yml"},
        ]
    }

    assert module.iter_bind_sources(service, {"named-data", "cache"}) == [
        "./scripts/init.sh",
        "./config.yml",
    ]


def test_missing_bind_source_fails():
    module = load_module()
    tmp_path = repo_tmp_path("missing-bind")
    compose = write_file(
        tmp_path / "docker-compose.test.yml",
        """
services:
  api:
    image: alpine:3.20
    volumes:
      - ./missing.yml:/etc/missing.yml:ro
    healthcheck:
      test: ["CMD", "true"]
""",
    )

    failures = module.validate_compose_contract(compose, tmp_path)

    assert [failure.message for failure in failures] == [
        "bind-mount source does not exist: ./missing.yml"
    ]


def test_missing_build_context_and_dockerfile_fail():
    module = load_module()
    tmp_path = repo_tmp_path("missing-build")
    compose = write_file(
        tmp_path / "docker-compose.test.yml",
        """
services:
  api:
    build:
      context: ./missing-context
      dockerfile: ./Dockerfile
    healthcheck:
      test: ["CMD", "true"]
""",
    )

    failures = module.validate_compose_contract(compose, tmp_path)

    messages = [failure.message for failure in failures]
    assert any(message.startswith("build context does not exist:") for message in messages)
    assert any(message.startswith("Dockerfile does not exist:") for message in messages)


def test_healthcheck_exemption_applies_only_to_one_shot_services():
    module = load_module()
    tmp_path = repo_tmp_path("health-exemption")
    write_file(
        tmp_path / "service" / "Dockerfile",
        "FROM alpine:3.20\nCMD [\"sh\"]\n",
    )
    compose = write_file(
        tmp_path / "docker-compose.test.yml",
        """
services:
  api:
    build:
      context: ./service
      dockerfile: ./Dockerfile
  layer5-migrate:
    build:
      context: ./service
      dockerfile: ./Dockerfile
    command: alembic upgrade head
    restart: "no"
""",
    )

    failures = module.validate_compose_contract(compose, tmp_path)

    assert len(failures) == 1
    assert failures[0].service == "api"
    assert "has no compose healthcheck" in failures[0].message


def test_dockerfile_healthcheck_satisfies_long_running_service():
    module = load_module()
    tmp_path = repo_tmp_path("dockerfile-healthcheck")
    write_file(
        tmp_path / "service" / "Dockerfile",
        "FROM alpine:3.20\nHEALTHCHECK CMD true\nCMD [\"sh\"]\n",
    )
    compose = write_file(
        tmp_path / "docker-compose.test.yml",
        """
services:
  api:
    build:
      context: ./service
      dockerfile: ./Dockerfile
""",
    )

    assert module.validate_compose_contract(compose, tmp_path) == []


def test_required_env_defaults_are_safe_and_do_not_use_real_env(monkeypatch):
    module = load_module()
    for key in module.SAFE_REQUIRED_ENV_DEFAULTS:
        monkeypatch.delenv(key, raising=False)

    env = module.docker_env()

    for key, expected in module.SAFE_REQUIRED_ENV_DEFAULTS.items():
        assert env[key] == expected
        assert expected.startswith(("compose-contract", "compose_contract", "composecontract"))
        assert expected != os.environ.get(key)
