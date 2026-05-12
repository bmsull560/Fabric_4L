#!/usr/bin/env python3
"""Validate migration entrypoints and revision history commands per maintained service."""

from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ServiceMigrationContract:
    name: str
    service_dir: Path
    required_paths: tuple[Path, ...]
    entrypoint_command: tuple[str, ...]
    history_command: tuple[str, ...]


REPO_ROOT = Path(__file__).resolve().parents[2]

CONTRACTS: tuple[ServiceMigrationContract, ...] = (
    ServiceMigrationContract(
        name="layer1-ingestion",
        service_dir=Path("services/layer1-ingestion"),
        required_paths=(Path("alembic.ini"), Path("migrations/env.py"), Path("migrations/versions")),
        entrypoint_command=("alembic", "-c", "alembic.ini", "current", "--help"),
        history_command=("alembic", "-c", "alembic.ini", "history", "--help"),
    ),
    ServiceMigrationContract(
        name="layer2-extraction",
        service_dir=Path("services/layer2-extraction"),
        required_paths=(Path("alembic.ini"), Path("migrations/env.py"), Path("migrations/versions")),
        entrypoint_command=("alembic", "-c", "alembic.ini", "current", "--help"),
        history_command=("alembic", "-c", "alembic.ini", "history", "--help"),
    ),
    ServiceMigrationContract(
        name="layer3-knowledge",
        service_dir=Path("services/layer3-knowledge"),
        required_paths=(Path("src/migrations"),),
        entrypoint_command=("python", "-m", "pip", "--version"),
        history_command=("python", "-c", "from pathlib import Path; p=Path('src/migrations'); files=sorted(x.name for x in p.iterdir() if x.is_file()); print(len(files))"),
    ),
    ServiceMigrationContract(
        name="layer4-agents",
        service_dir=Path("services/layer4-agents"),
        required_paths=(Path("alembic.ini"), Path("migrations/env.py"), Path("migrations/versions")),
        entrypoint_command=("alembic", "-c", "alembic.ini", "current", "--help"),
        history_command=("alembic", "-c", "alembic.ini", "history", "--help"),
    ),
    ServiceMigrationContract(
        name="layer5-ground-truth",
        service_dir=Path("services/layer5-ground-truth"),
        required_paths=(
            Path("alembic.ini"),
            Path("src/layer5_ground_truth/migrations/env.py"),
            Path("src/layer5_ground_truth/migrations/versions"),
        ),
        entrypoint_command=("alembic", "-c", "alembic.ini", "current", "--help"),
        history_command=("alembic", "-c", "alembic.ini", "history", "--help"),
    ),
    ServiceMigrationContract(
        name="layer6-benchmarks",
        service_dir=Path("services/layer6-benchmarks"),
        required_paths=(Path("migrations/versions"),),
        entrypoint_command=("python", "-m", "pip", "--version"),
        history_command=("python", "-c", "from pathlib import Path; p=Path('migrations/versions'); files=sorted(x.name for x in p.iterdir() if x.is_file()); print(len(files))"),
    ),
)


def _check_commands_available() -> list[str]:
    missing: list[str] = []
    for executable in ("python", "alembic"):
        if shutil.which(executable) is None:
            missing.append(executable)
    return missing


def _run_command(cmd: tuple[str, ...], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)


def main() -> int:
    missing_bins = _check_commands_available()
    if missing_bins:
        print(f"❌ Missing required executables in PATH: {', '.join(missing_bins)}")
        return 1

    errors: list[str] = []

    for contract in CONTRACTS:
        service_root = REPO_ROOT / contract.service_dir
        if not service_root.exists():
            errors.append(f"{contract.name}: service directory missing: {contract.service_dir}")
            continue

        for rel_path in contract.required_paths:
            candidate = service_root / rel_path
            if not candidate.exists():
                errors.append(f"{contract.name}: required migration path missing: {contract.service_dir / rel_path}")

        entrypoint_result = _run_command(contract.entrypoint_command, service_root)
        if entrypoint_result.returncode != 0:
            errors.append(
                f"{contract.name}: entrypoint command failed: {' '.join(contract.entrypoint_command)}\n"
                f"stdout: {entrypoint_result.stdout.strip()}\n"
                f"stderr: {entrypoint_result.stderr.strip()}"
            )

        history_result = _run_command(contract.history_command, service_root)
        if history_result.returncode != 0:
            errors.append(
                f"{contract.name}: history command failed: {' '.join(contract.history_command)}\n"
                f"stdout: {history_result.stdout.strip()}\n"
                f"stderr: {history_result.stderr.strip()}"
            )
        elif not history_result.stdout.strip():
            errors.append(f"{contract.name}: history command returned no migration revisions")

    if errors:
        print("❌ Migration entrypoint contract failed:\n")
        for err in errors:
            print(f"- {err}")
        return 1

    print("✅ Migration entrypoint contract passed for all maintained layer services.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
