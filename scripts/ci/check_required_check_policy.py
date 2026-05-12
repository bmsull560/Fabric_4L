#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
METADATA_PATH = REPO_ROOT / "docs" / "governance" / "branch-protection-required-checks.yml"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "branch-protection-validation.yml"


def _load_yaml(path: Path) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must parse to a mapping")
    return data


def main() -> int:
    metadata = _load_yaml(METADATA_PATH)
    checks = metadata.get("required_status_checks")
    if not isinstance(checks, list) or not checks or not all(isinstance(c, str) for c in checks):
        print("required_status_checks must be a non-empty string list", file=sys.stderr)
        return 1

    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    errors: list[str] = []

    for check in checks:
        if f'"{check}"' not in workflow_text:
            errors.append(f"missing required check in workflow validation list: {check}")

    for pattern in metadata.get("protected_branch_patterns", []):
        if pattern == "release/*" and "release/" not in workflow_text:
            errors.append("workflow does not validate release/* branches")
        elif pattern == "main" and '"main"' not in workflow_text:
            errors.append("workflow does not validate main branch")

    if metadata.get("enforcement", {}).get("pull_request_merges") and "strict" not in workflow_text:
        errors.append("workflow does not assert strict required status checks (PR merge up-to-date enforcement)")

    if metadata.get("enforcement", {}).get("direct_pushes") and "contexts" not in workflow_text:
        errors.append("workflow does not assert required status check contexts (direct push enforcement)")

    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print("Required check policy metadata matches branch-protection validation workflow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
