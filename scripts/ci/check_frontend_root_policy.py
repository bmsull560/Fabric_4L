#!/usr/bin/env python3
"""Fail CI when new non-doc files are added under legacy frontend/ root."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ALLOWED_EXACT = set()
ALLOWED_SUFFIXES = (".md",)
ALLOWED_PREFIXES = (
    "frontend/archive/",
    "frontend/docs/",
)


def git_changed_added_files(base_ref: str) -> list[str]:
    cmd = ["git", "diff", "--name-status", f"{base_ref}...HEAD"]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    added: list[str] = []
    for raw_line in result.stdout.splitlines():
        if not raw_line.strip():
            continue
        status, path = raw_line.split("\t", 1)
        if status.startswith("A"):
            added.append(path)
    return added


def is_allowed(path: str) -> bool:
    if path in ALLOWED_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return True
    return path.endswith(ALLOWED_SUFFIXES)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", default="origin/main")
    args = parser.parse_args()

    try:
        changed = git_changed_added_files(args.base_ref)
    except subprocess.CalledProcessError as exc:
        print(exc.stdout)
        print(exc.stderr, file=sys.stderr)
        return exc.returncode

    violations = [
        path
        for path in changed
        if path.startswith("frontend/") and not is_allowed(path)
    ]

    if violations:
        print("Frontend root policy violation:")
        print("apps/web/ is the only valid frontend source root.")
        print("The following added files are not allowed under frontend/:")
        for item in violations:
            print(f" - {item}")
        return 1

    print("Frontend root policy check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
