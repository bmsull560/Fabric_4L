#!/usr/bin/env python3
"""Launch-freeze guard for runtime compatibility shims and registry metadata."""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ci.compatibility_registry import (
    REGISTRY_PATH,
    RegistryEntry,
    has_platform_architecture_approval,
    parse_registry,
    path_is_covered,
)

CANONICAL_RUNTIME_ROOTS = (
    REPO_ROOT / "value_fabric/layer1",
    REPO_ROOT / "value_fabric/layer3",
    REPO_ROOT / "value_fabric/layer4",
    REPO_ROOT / "services/layer4-agents/src",
    REPO_ROOT / "services/layer5-ground-truth/src/layer5_ground_truth",
)
PATH_MARKERS = ("compat", "legacy", "shim")
SKIP_DIRS = {"__pycache__", ".git", ".venv", ".tox", ".pytest_cache", "node_modules"}


@dataclass(frozen=True)
class Violation:
    path: str
    message: str


def _iter_candidate_paths() -> list[str]:
    candidates: list[str] = []
    for root in CANONICAL_RUNTIME_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            rel = path.relative_to(REPO_ROOT).as_posix()
            lowered = rel.lower()
            if any(marker in lowered for marker in PATH_MARKERS):
                candidates.append(rel)
    return sorted(set(candidates))


def _validate_entry(entry: RegistryEntry) -> list[Violation]:
    violations: list[Violation] = []
    location = f"{REGISTRY_PATH.relative_to(REPO_ROOT).as_posix()}:{entry.line_number}"
    if not entry.owner:
        violations.append(Violation(location, f"{entry.shim_id} is missing owner metadata"))
    try:
        entry.target_removal_date_obj
    except ValueError:
        violations.append(Violation(location, f"{entry.shim_id} has invalid target removal date: {entry.target_removal_date!r}"))
    if not entry.review_metadata:
        violations.append(Violation(location, f"{entry.shim_id} is missing review metadata"))
    elif not has_platform_architecture_approval(entry.review_metadata):
        violations.append(
            Violation(
                location,
                f"{entry.shim_id} review metadata must include Platform Architecture approval plus an ISO date",
            )
        )
    if not entry.removal_ticket:
        violations.append(Violation(location, f"{entry.shim_id} is missing post-launch removal ticket"))
    return violations


def check_launch_freeze() -> list[Violation]:
    entries = parse_registry(REGISTRY_PATH)
    violations: list[Violation] = []

    for entry in entries:
        violations.extend(_validate_entry(entry))

    for candidate in _iter_candidate_paths():
        if not path_is_covered(candidate, entries):
            violations.append(
                Violation(
                    candidate,
                    "net-new compatibility wrapper/shim path detected under canonical runtime roots without explicit Platform Architecture approval in the compatibility registry",
                )
            )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)

    violations = check_launch_freeze()
    print(f"Compatibility launch-freeze findings: {len(violations)}")
    for violation in violations:
        print(f"  - {violation.path}: {violation.message}")

    return 1 if args.strict and violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
