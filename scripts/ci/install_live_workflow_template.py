#!/usr/bin/env python3
"""Install or verify the live workflow validation GitHub Actions template.

The automation identity used for repository remediation may not have permission to
push files under ``.github/workflows``. This utility gives maintainers with
workflow-write permission a deterministic way to install the reviewed template, or
to verify that an existing workflow matches the repository-owned template exactly.
"""

from __future__ import annotations

import argparse
import difflib
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = REPO_ROOT / "docs" / "validation" / "ci-templates" / "live-workflow-validation.yml"
TARGET = REPO_ROOT / ".github" / "workflows" / "live-workflow-validation.yml"


def unified_diff(existing: str, desired: str) -> str:
    return "".join(
        difflib.unified_diff(
            existing.splitlines(keepends=True),
            desired.splitlines(keepends=True),
            fromfile=str(TARGET),
            tofile=str(TEMPLATE),
        )
    )


def install(*, check: bool) -> int:
    if not TEMPLATE.exists():
        print(f"template not found: {TEMPLATE}", file=sys.stderr)
        return 2

    desired = TEMPLATE.read_text(encoding="utf-8")
    existing = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""

    if existing == desired:
        print(f"live workflow template is already installed: {TARGET}")
        return 0

    if check:
        print("live workflow template is not installed or differs from the reviewed template", file=sys.stderr)
        if existing:
            print(unified_diff(existing, desired), file=sys.stderr)
        else:
            print(f"missing target workflow: {TARGET}", file=sys.stderr)
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(TEMPLATE, TARGET)
    print(f"installed live workflow template: {TARGET}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or verify the live validation workflow template")
    parser.add_argument("--check", action="store_true", help="Only verify that the workflow is installed and up to date")
    args = parser.parse_args()
    return install(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
