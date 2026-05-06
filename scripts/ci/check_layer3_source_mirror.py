#!/usr/bin/env python3
"""Fail CI when Layer 3 mirrored Python source roots drift.

The repository currently keeps Layer 3 Python modules in two import roots:

* value_fabric/layer3
* services/layer3-knowledge/src

Until the project consolidates to a single canonical source tree, this guard makes
that mirror relationship explicit and fail-closed in CI.
"""

from __future__ import annotations

import filecmp
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOT_LAYER3 = ROOT / "value_fabric" / "layer3"
SERVICE_LAYER3 = ROOT / "services" / "layer3-knowledge" / "src"


def iter_python_files(base: Path) -> dict[str, Path]:
    """Return repo-local Python files keyed by path relative to the mirror root."""
    return {
        str(path.relative_to(base)): path
        for path in sorted(base.rglob("*.py"))
        if "__pycache__" not in path.parts
    }


def main() -> int:
    if not ROOT_LAYER3.exists():
        print(f"Missing Layer 3 root package: {ROOT_LAYER3.relative_to(ROOT)}")
        return 1
    if not SERVICE_LAYER3.exists():
        print(f"Missing Layer 3 service source root: {SERVICE_LAYER3.relative_to(ROOT)}")
        return 1

    root_files = iter_python_files(ROOT_LAYER3)
    service_files = iter_python_files(SERVICE_LAYER3)

    missing_in_service = sorted(set(root_files) - set(service_files))
    missing_in_root = sorted(set(service_files) - set(root_files))
    changed = sorted(
        rel
        for rel in set(root_files) & set(service_files)
        if not filecmp.cmp(root_files[rel], service_files[rel], shallow=False)
    )

    if not (missing_in_service or missing_in_root or changed):
        print(f"Layer 3 source mirror OK — {len(root_files)} files synchronized")
        return 0

    if missing_in_service:
        print("Missing in services/layer3-knowledge/src:")
        print("\n".join(f"  - {rel}" for rel in missing_in_service))
    if missing_in_root:
        print("Missing in value_fabric/layer3:")
        print("\n".join(f"  - {rel}" for rel in missing_in_root))
    if changed:
        print("Drifted mirrored files:")
        print("\n".join(f"  - {rel}" for rel in changed))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
