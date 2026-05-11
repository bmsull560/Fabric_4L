#!/usr/bin/env python3
"""Fail-closed Docker Compose static contract validation.

This gate validates compose syntax through Docker Compose v2 and then checks
repo-local contracts that `docker compose config` does not catch reliably:
build contexts, Dockerfile paths, bind-mount sources, and healthcheck coverage.
It intentionally does not start containers.
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]

TARGET_COMPOSE_FILES = (
    "docker-compose.dev.yml",
    "docker-compose.live.yml",
    "docker-compose.release-smoke.yml",
    "docker-compose.full.yml",
)

SAFE_REQUIRED_ENV_DEFAULTS = {
    "NEO4J_PASSWORD": "compose-contract-neo4j-password",
    "MINIO_ROOT_USER": "composecontract",
    "MINIO_ROOT_PASSWORD": "compose-contract-minio-password",
    "JWT_SECRET": "compose-contract-jwt-secret-minimum-32-characters",
    "FLOWER_PASSWORD": "compose-contract-flower-password",
    "GRAFANA_ADMIN_PASSWORD": "compose-contract-grafana-password",
    "REDIS_PASSWORD": "compose-contract-redis-password",
    "POSTGRES_USER": "compose_contract_user",
    "POSTGRES_PASSWORD": "compose-contract-postgres-password",
    "SERVICE_AUTH_SECRET": "compose-contract-service-auth-secret-32chars",
}

ONE_SHOT_SERVICE_PATTERNS = (
    "init",
    "migrate",
    "migration",
    "seed",
    "runner",
    "test",
)

SKIPPED_BIND_SOURCES = {
    "/var/run/docker.sock",
}


@dataclass(frozen=True)
class ComposeFailure:
    compose_file: str
    service: str
    message: str

    def format(self) -> str:
        prefix = f"{self.compose_file}"
        if self.service:
            prefix += f"::{self.service}"
        return f"{prefix}: {self.message}"


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def run_command(
    args: list[str],
    *,
    cwd: Path = REPO_ROOT,
    env: dict[str, str] | None = None,
    stdout_path: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    if stdout_path:
        with stdout_path.open("w", encoding="utf-8") as stdout_file:
            result = subprocess.run(
                args,
                cwd=cwd,
                env=env,
                text=True,
                stdout=stdout_file,
                stderr=subprocess.PIPE,
                check=False,
            )
    else:
        result = subprocess.run(
            args,
            cwd=cwd,
            env=env,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        command = " ".join(args)
        fail(f"command failed ({command}): {stderr}")
    return result


def docker_env() -> dict[str, str]:
    env = os.environ.copy()
    for key, value in SAFE_REQUIRED_ENV_DEFAULTS.items():
        env.setdefault(key, value)
    return env


def require_docker_compose() -> None:
    run_command(["docker", "--version"])
    run_command(["docker", "compose", "version"])


def load_compose(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        fail(f"{path.name} must parse as a YAML mapping")
    if not isinstance(data.get("services"), dict):
        fail(f"{path.name} must define a services mapping")
    return data


def has_unresolved_env_reference(value: str) -> bool:
    return "${" in value or "$" in value


def looks_like_path(source: str) -> bool:
    normalized = source.replace("\\", "/")
    return (
        normalized.startswith(".")
        or normalized.startswith("/")
        or normalized.startswith("~")
        or bool(re.match(r"^[A-Za-z]:/", normalized))
    )


def resolve_repo_path(source: str, repo_root: Path = REPO_ROOT) -> Path | None:
    if has_unresolved_env_reference(source):
        return None
    if source in SKIPPED_BIND_SOURCES:
        return None
    source_path = Path(source)
    if source_path.is_absolute():
        return source_path
    return (repo_root / source_path).resolve()


def split_short_volume(volume: str) -> tuple[str | None, str | None]:
    if ":" not in volume:
        return None, volume
    parts = volume.split(":")
    if re.match(r"^[A-Za-z]$", parts[0]) and len(parts) > 2:
        source = ":".join(parts[:2])
        target = parts[2] if len(parts) == 3 else parts[2]
        return source, target
    return parts[0], parts[1] if len(parts) > 1 else None


def iter_bind_sources(
    service: dict[str, Any], declared_volumes: set[str]
) -> list[str]:
    sources: list[str] = []
    for volume in service.get("volumes") or []:
        if isinstance(volume, str):
            source, _target = split_short_volume(volume)
            if source is None:
                continue
            if source in declared_volumes or not looks_like_path(source):
                continue
            sources.append(source)
        elif isinstance(volume, dict):
            volume_type = volume.get("type")
            source = volume.get("source") or volume.get("src")
            if not source:
                continue
            if volume_type and volume_type != "bind":
                continue
            if source in declared_volumes or not looks_like_path(str(source)):
                continue
            sources.append(str(source))
    return sources


def resolve_build_paths(
    service: dict[str, Any], repo_root: Path = REPO_ROOT
) -> tuple[Path, Path] | None:
    build = service.get("build")
    if not build:
        return None
    if isinstance(build, str):
        context_value = build
        dockerfile_value = "Dockerfile"
    elif isinstance(build, dict):
        context_value = str(build.get("context", "."))
        dockerfile_value = str(build.get("dockerfile", "Dockerfile"))
    else:
        return None

    context_path = Path(context_value)
    if not context_path.is_absolute():
        context_path = repo_root / context_path
    context_path = context_path.resolve()

    dockerfile_path = Path(dockerfile_value)
    if not dockerfile_path.is_absolute():
        if dockerfile_value.startswith("."):
            dockerfile_path = context_path / dockerfile_path
        else:
            dockerfile_path = context_path / dockerfile_path
    return context_path, dockerfile_path.resolve()


def dockerfile_has_healthcheck(dockerfile_path: Path) -> bool:
    if not dockerfile_path.exists() or not dockerfile_path.is_file():
        return False
    for line in dockerfile_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip().upper()
        if stripped.startswith("HEALTHCHECK") and "HEALTHCHECK NONE" not in stripped:
            return True
    return False


def is_one_shot_service(service_name: str, service: dict[str, Any]) -> bool:
    name = service_name.lower()
    if any(pattern in name for pattern in ONE_SHOT_SERVICE_PATTERNS):
        return True
    restart = str(service.get("restart", "")).lower()
    command = service.get("command", "")
    command_text = " ".join(command) if isinstance(command, list) else str(command)
    if restart in {"no", "none", "false"} and any(
        token in command_text.lower() for token in ("alembic", "seed", "pytest", "pnpm run seed")
    ):
        return True
    return False


def validate_compose_contract(compose_file: Path, repo_root: Path = REPO_ROOT) -> list[ComposeFailure]:
    data = load_compose(compose_file)
    declared_volumes = set((data.get("volumes") or {}).keys())
    failures: list[ComposeFailure] = []

    services = data["services"]
    for service_name, service in services.items():
        if not isinstance(service, dict):
            failures.append(
                ComposeFailure(compose_file.name, service_name, "service definition must be a mapping")
            )
            continue

        build_paths = resolve_build_paths(service, repo_root)
        dockerfile_path: Path | None = None
        if build_paths:
            context_path, dockerfile_path = build_paths
            if not context_path.exists() or not context_path.is_dir():
                failures.append(
                    ComposeFailure(
                        compose_file.name,
                        service_name,
                        f"build context does not exist: {context_path}",
                    )
                )
            if not dockerfile_path.exists() or not dockerfile_path.is_file():
                failures.append(
                    ComposeFailure(
                        compose_file.name,
                        service_name,
                        f"Dockerfile does not exist: {dockerfile_path}",
                    )
                )

        for source in iter_bind_sources(service, declared_volumes):
            resolved = resolve_repo_path(source, repo_root)
            if resolved is None:
                continue
            if not resolved.exists():
                failures.append(
                    ComposeFailure(
                        compose_file.name,
                        service_name,
                        f"bind-mount source does not exist: {source}",
                    )
                )

        has_healthcheck = "healthcheck" in service
        if not has_healthcheck and dockerfile_path:
            has_healthcheck = dockerfile_has_healthcheck(dockerfile_path)
        if not has_healthcheck and not is_one_shot_service(service_name, service):
            failures.append(
                ComposeFailure(
                    compose_file.name,
                    service_name,
                    "long-running service has no compose healthcheck or Dockerfile HEALTHCHECK",
                )
            )

    return failures


def validate_all(artifact_dir: Path, compose_files: tuple[str, ...] = TARGET_COMPOSE_FILES) -> None:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    env = docker_env()
    require_docker_compose()

    failures: list[ComposeFailure] = []
    for compose_name in compose_files:
        compose_path = REPO_ROOT / compose_name
        if not compose_path.exists():
            failures.append(ComposeFailure(compose_name, "", "compose file is missing"))
            continue
        run_command(["docker", "compose", "-f", compose_name, "config", "--quiet"], env=env)
        artifact_path = artifact_dir / f"{compose_path.stem}.resolved.yml"
        run_command(["docker", "compose", "-f", compose_name, "config"], env=env, stdout_path=artifact_path)
        failures.extend(validate_compose_contract(compose_path))

    if failures:
        for failure in failures:
            print(failure.format(), file=sys.stderr)
        raise SystemExit(1)

    print(f"Docker Compose config contract passed for {len(compose_files)} compose files.")
    print(f"Resolved configs written to {artifact_dir}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        default="artifacts/docker-compose-config",
        help="Directory for resolved compose config artifacts.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    validate_all((REPO_ROOT / args.artifact_dir).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
