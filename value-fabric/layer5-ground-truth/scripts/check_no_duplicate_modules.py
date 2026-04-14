#!/usr/bin/env python3
"""Fail if legacy duplicate modules exist outside canonical layer5_ground_truth package."""

from __future__ import annotations

from pathlib import Path


def main() -> int:
    src_root = Path(__file__).resolve().parents[1] / "src"
    canonical_root = src_root / "layer5_ground_truth"
    module_dirs = ["api", "services", "models", "integration", "migrations"]

    violations: list[str] = []
    for module_dir in module_dirs:
        legacy_dir = src_root / module_dir
        canonical_dir = canonical_root / module_dir

        if legacy_dir.exists() and canonical_dir.exists():
            legacy_py = {p.name for p in legacy_dir.glob("*.py")}
            canonical_py = {p.name for p in canonical_dir.glob("*.py")}
            overlap = sorted(legacy_py & canonical_py)

            if overlap:
                overlaps = ", ".join(overlap)
                violations.append(
                    f"Duplicate module files found in '{legacy_dir}' and '{canonical_dir}': {overlaps}"
                )

    if violations:
        print("ERROR: legacy duplicate modules detected. Use src/layer5_ground_truth/* only.")
        for violation in violations:
            print(f" - {violation}")
        return 1

    print("OK: no legacy module duplicates found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
