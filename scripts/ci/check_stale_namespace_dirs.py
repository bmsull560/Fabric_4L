#!/usr/bin/env python3
"""Guard that deleted legacy namespace directories are not reintroduced.

Per ADR-027, the following directories were removed and must not exist:
  - value_fabric/layer1_ingestion/
  - value_fabric/layer3_knowledge/
  - value_fabric/layer2_extraction/
  - value_fabric/layer6_benchmarks/

Additionally, shim-only directories must contain only __init__.py:
  - value_fabric/layer1/
  - value_fabric/layer2/
  - value_fabric/layer3/
  - value_fabric/layer4/
  - value_fabric/layer5/
  - value_fabric/layer6/

Run as a CI step or locally:

    python scripts/ci/check_stale_namespace_dirs.py

Exit 0 when clean, 1 when violations found.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# These directories must not exist at all (fully deleted per ADR-027).
DELETED_DIRS: tuple[str, ...] = (
    "value_fabric/layer1_ingestion",
    "value_fabric/layer3_knowledge",
    "value_fabric/layer2_extraction",
    "value_fabric/layer6_benchmarks",
)

# These directories must exist but contain only __init__.py (shim-only).
SHIM_ONLY_DIRS: tuple[str, ...] = (
    "value_fabric/layer1",
    "value_fabric/layer2",
    "value_fabric/layer3",
    "value_fabric/layer4",
    "value_fabric/layer5",
    "value_fabric/layer6",
)


def main() -> int:
    violations: list[str] = []

    # Check deleted directories are gone.
    for rel in DELETED_DIRS:
        path = REPO_ROOT / rel
        if path.exists():
            contents = list(path.iterdir())
            violations.append(
                f"DELETED dir reintroduced: {rel}/ ({len(contents)} item(s))"
            )

    # Check shim-only directories contain only __init__.py.
    for rel in SHIM_ONLY_DIRS:
        path = REPO_ROOT / rel
        if not path.exists():
            violations.append(f"SHIM dir missing: {rel}/ (expected to exist as namespace shim)")
            continue
        non_init = [
            p.relative_to(REPO_ROOT)
            for p in path.iterdir()
            if p.name not in ("__init__.py", "__pycache__")
        ]
        if non_init:
            violations.append(
                f"SHIM dir {rel}/ contains non-shim files: "
                + ", ".join(str(p) for p in sorted(non_init))
            )

    if violations:
        print("Stale namespace directory violations found:", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1

    print("Stale namespace directory check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
