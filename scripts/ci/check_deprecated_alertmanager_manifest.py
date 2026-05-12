#!/usr/bin/env python3
"""Guard canonical Alertmanager/alert-rule paths and deprecated manifests."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CanonicalSet:
    env: str
    alertmanager: Path
    rules: Path


CANONICAL_BY_ENV = [
    CanonicalSet(
        env="dev",
        alertmanager=Path("monitoring/alertmanager/alertmanager.yml"),
        rules=Path("monitoring/alerting/rules.yml"),
    ),
    CanonicalSet(
        env="staging",
        alertmanager=Path("monitoring/alertmanager/alertmanager-enhanced.yml"),
        rules=Path("monitoring/alerting/rules.yml"),
    ),
    CanonicalSet(
        env="prod",
        alertmanager=Path("monitoring/alertmanager/alertmanager-production.yml"),
        rules=Path("monitoring/alerting/rules-production.yml"),
    ),
]

NON_AUTHORITATIVE_FILES = {
    Path("monitoring/alerting/alertmanager.yml"): "Deprecated duplicate (legacy Alertmanager config path)",
    Path("k8s/monitoring-alertmanager.yml"): "Compatibility/derived manifest generated from k8s/base/monitoring-alertmanager.yml",
}

DEPRECATED_MANIFESTS = [
    Path("k8s/alertmanager.yml"),
]

REGEN_SIGNAL_FILES = {
    Path("scripts/monitoring-sync.sh"),
    Path("scripts/ci/validate-alertmanager-config.sh"),
}



def _changed_files() -> set[Path]:
    base_ref = os.environ.get("GITHUB_BASE_REF")
    cmd = ["git", "diff", "--name-only"]
    if base_ref:
        cmd.append(f"origin/{base_ref}...HEAD")
    else:
        cmd.append("HEAD~1...HEAD")
    try:
        output = subprocess.check_output(cmd, cwd=REPO_ROOT, text=True)
    except Exception:
        return set()
    return {Path(line.strip()) for line in output.splitlines() if line.strip()}


def main() -> int:
    errors: list[str] = []

    for deprecated in DEPRECATED_MANIFESTS:
        if (REPO_ROOT / deprecated).exists():
            errors.append(
                f"Deprecated manifest detected: {deprecated}. "
                "Use k8s/base/monitoring-alertmanager.yml (canonical) with compatibility wrappers only."
            )

    for entry in CANONICAL_BY_ENV:
        for path in (entry.alertmanager, entry.rules):
            if not (REPO_ROOT / path).exists():
                errors.append(f"Missing canonical {entry.env} source-of-truth file: {path}")

    changed = _changed_files()
    changed_non_authoritative = sorted(path for path in changed if path in NON_AUTHORITATIVE_FILES)

    if changed_non_authoritative:
        used_regen = any(path in changed for path in REGEN_SIGNAL_FILES)
        if not used_regen:
            lines = [
                "Detected edits to non-authoritative alerting files without regeneration signal:",
            ]
            for path in changed_non_authoritative:
                lines.append(f"  - {path}: {NON_AUTHORITATIVE_FILES[path]}")
            lines.append(
                "If intentional, run the regeneration workflow/script and include the regeneration script change in the same commit."
            )
            errors.append("\n".join(lines))

    if errors:
        print("ERROR: Alertmanager/alert-rule governance checks failed:")
        for err in errors:
            print(f"- {err}")
        return 1

    print("OK: Alertmanager/alert-rule governance checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
