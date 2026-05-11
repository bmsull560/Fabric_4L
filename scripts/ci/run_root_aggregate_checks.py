#!/usr/bin/env python3
"""Fail-closed root aggregate package checks.

The root package scripts must not pass when pnpm selects zero package scripts.
This runner keeps the expected workspace checks explicit and verifies every
package/script pair before invoking pnpm.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class PackageCheck:
    package_path: str
    script: str


EXPECTED_CHECKS: dict[str, tuple[PackageCheck, ...]] = {
    "typecheck": (
        PackageCheck("apps/web", "typecheck"),
        PackageCheck("packages/config", "typecheck"),
        PackageCheck("packages/platform-contract", "typecheck"),
        PackageCheck("packages/eslint-plugin-fabric-contracts", "typecheck"),
    ),
    "lint": (
        PackageCheck("apps/web", "lint"),
        PackageCheck("packages/eslint-plugin-fabric-contracts", "lint"),
    ),
    "test": (
        PackageCheck("apps/web", "test"),
        PackageCheck("packages/config", "test"),
        PackageCheck("packages/platform-contract", "test"),
        PackageCheck("packages/eslint-plugin-fabric-contracts", "test"),
    ),
}

Runner = Callable[[Sequence[str], Path], subprocess.CompletedProcess[str]]


class AggregateCheckError(RuntimeError):
    """Raised when aggregate check configuration or execution fails."""


def _load_package_json(path: Path) -> dict[str, object]:
    package_json = path / "package.json"
    if not package_json.exists():
        raise AggregateCheckError(f"Missing expected package manifest: {package_json}")
    with package_json.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def validate_expected_checks(target: str, repo_root: Path = REPO_ROOT) -> tuple[PackageCheck, ...]:
    checks = EXPECTED_CHECKS.get(target)
    if checks is None:
        valid = ", ".join(sorted(EXPECTED_CHECKS))
        raise AggregateCheckError(f"Unsupported aggregate check {target!r}; expected one of: {valid}")
    if not checks:
        raise AggregateCheckError(f"Aggregate check {target!r} has zero package checks configured")

    for check in checks:
        package_dir = repo_root / check.package_path
        package = _load_package_json(package_dir)
        scripts = package.get("scripts")
        if not isinstance(scripts, dict) or check.script not in scripts:
            package_name = package.get("name", check.package_path)
            raise AggregateCheckError(
                f"Missing required script {check.script!r} in {check.package_path}/package.json "
                f"({package_name})"
            )

    return checks


def default_runner(command: Sequence[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    executable = shutil.which(command[0])
    if executable is None:
        print(f"Command not found: {command[0]}", file=sys.stderr)
        return subprocess.CompletedProcess(command, 127)
    resolved_command = [executable, *command[1:]]
    return subprocess.run(resolved_command, cwd=cwd, text=True, check=False)


def run_aggregate_check(
    target: str,
    repo_root: Path = REPO_ROOT,
    runner: Runner = default_runner,
) -> int:
    checks = validate_expected_checks(target, repo_root)
    print(f"Root aggregate {target}: {len(checks)} package checks planned.")

    failures: list[tuple[PackageCheck, int]] = []
    for check in checks:
        command = ["pnpm", "--dir", check.package_path, "run", check.script]
        print(f"\n## {check.package_path}:{check.script}")
        result = runner(command, repo_root)
        if result.returncode != 0:
            failures.append((check, result.returncode))

    passed = len(checks) - len(failures)
    print(f"\nRoot aggregate {target} summary: {passed} passed, {len(failures)} failed.")
    if failures:
        for check, returncode in failures:
            print(
                f" - {check.package_path}:{check.script} failed with exit code {returncode}",
                file=sys.stderr,
            )
        return 1
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=sorted(EXPECTED_CHECKS))
    args = parser.parse_args(argv)

    try:
        return run_aggregate_check(args.target)
    except AggregateCheckError as exc:
        print(f"Root aggregate check configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
