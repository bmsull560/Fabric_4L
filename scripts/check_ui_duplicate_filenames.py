#!/usr/bin/env python3
"""Detect duplicate UI component filenames between production and prototype trees."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Allow importing sibling _lib without a package __init__.py
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _lib import resolve_repo_root  # type: ignore[import-not-found]


PROD_UI_REL = Path("apps/web/client/src/components/ui")
PROTOTYPE_UI_REL = Path("prototypes/ui-prototype/non-production/ui-components-archive")
BASELINE_REL = Path("scripts/ui_duplicate_baseline.txt")


def _filenames(path: Path) -> set[str]:
    """Return the set of filenames inside *path* (non-recursive)."""
    if not path.exists():
        return set()
    return {p.name for p in path.glob("*") if p.is_file()}


def _load_baseline(path: Path) -> set[str]:
    """Load the baseline duplicate list, ignoring blank lines and comments."""
    if not path.exists():
        return set()
    return {
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root (default: auto-detected)",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve() if args.repo_root else resolve_repo_root()
    prod_ui = repo_root / PROD_UI_REL
    proto_ui = repo_root / PROTOTYPE_UI_REL
    baseline_file = repo_root / BASELINE_REL

    prod = _filenames(prod_ui)
    proto = _filenames(proto_ui)
    current = sorted(prod & proto)
    baseline = _load_baseline(baseline_file)
    new_duplicates = sorted(set(current) - baseline)

    if new_duplicates:
        print(
            "New duplicate UI component filenames detected across "
            "prototype and production trees:"
        )
        for name in new_duplicates:
            print(f"  - {name}")
        print(
            "\nResolve by renaming/removing prototype files or migrating "
            "to canonical production path."
        )
        return 1

    print(
        f"UI duplicate filename guard passed "
        f"(baseline={len(baseline)}, current={len(current)}, new={len(new_duplicates)})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
