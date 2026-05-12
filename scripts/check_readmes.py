#!/usr/bin/env python3
"""Check that every service directory contains a README.md with an owner mention."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow importing sibling _lib without a package __init__.py
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _lib import resolve_repo_root  # type: ignore[import-not-found]


def check_services(services_dir: Path) -> list[tuple[str, bool, bool]]:
    """Scan *services_dir* for README.md presence and owner mention."""
    results: list[tuple[str, bool, bool]] = []
    try:
        entries = os.listdir(services_dir)
    except OSError as exc:
        print(f"ERROR: cannot list {services_dir}: {exc}", file=sys.stderr)
        return results

    for svc in entries:
        svc_path = services_dir / svc
        if not svc_path.is_dir():
            continue

        readme = svc_path / "README.md"
        has_readme = readme.is_file()
        has_owner = False
        if has_readme:
            try:
                content = readme.read_text(encoding="utf-8")
                has_owner = "owner" in content.lower()
            except OSError as exc:
                print(f"WARNING: cannot read {readme}: {exc}", file=sys.stderr)

        results.append((svc, has_readme, has_owner))
    return results


def main() -> int:
    repo_root = resolve_repo_root()
    services_dir = repo_root / "services"
    results = check_services(services_dir)

    if not results:
        print("No service directories found.", file=sys.stderr)
        return 1

    for svc, has_readme, has_owner in results:
        print(f"{svc}: README={has_readme}, Owner={has_owner}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
