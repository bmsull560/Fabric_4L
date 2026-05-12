#!/usr/bin/env python3
"""Fail CI when Layer 5 module roots or module names are duplicated."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path


def _py_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if path.name != "__pycache__")


def _build_module_map(root: Path) -> dict[str, list[Path]]:
    modules: dict[str, list[Path]] = defaultdict(list)
    for path in _py_files(root):
        if path.name == "__init__.py":
            continue
        rel = path.relative_to(root)
        module_name = ".".join(rel.with_suffix("").parts)
        modules[module_name].append(path)
    return dict(modules)


def _duplicate_roots(canonical_root: Path, service_root: Path) -> list[tuple[str, Path, Path]]:
    duplicates: list[tuple[str, Path, Path]] = []
    for entry in sorted(service_root.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        canonical_candidate = canonical_root / entry.name
        if canonical_candidate.is_dir():
            duplicates.append((entry.name, canonical_candidate, entry))
    return duplicates


def _duplicate_module_names(canonical_root: Path, service_root: Path) -> list[tuple[str, list[Path], list[Path]]]:
    canonical_modules = _build_module_map(canonical_root)
    service_modules = _build_module_map(service_root)

    duplicates: list[tuple[str, list[Path], list[Path]]] = []
    for module_name in sorted(canonical_modules.keys() & service_modules.keys()):
        duplicates.append((module_name, canonical_modules[module_name], service_modules[module_name]))
    return duplicates


def main() -> int:
    repo_root = Path(__file__).resolve().parents[3]
    canonical_root = repo_root / "value_fabric" / "layer5"
    service_root = repo_root / "services" / "layer5-ground-truth" / "src" / "layer5_ground_truth"

    duplicate_roots = _duplicate_roots(canonical_root, service_root)
    duplicate_modules = _duplicate_module_names(canonical_root, service_root)

    if not duplicate_roots and not duplicate_modules:
        print("OK: no duplicate Layer 5 package roots or module names detected.")
        return 0

    print("ERROR: duplicate Layer 5 modules detected across canonical and service package trees.")
    print("Canonical source-of-truth: value_fabric/layer5")
    print("Service wrapper path should not duplicate canonical module/package names:")
    print("  services/layer5-ground-truth/src/layer5_ground_truth")

    if duplicate_roots:
        print("\nConflicting package roots:")
        for name, canonical_path, service_path in duplicate_roots:
            print(f" - package '{name}':")
            print(f"   canonical: {canonical_path}")
            print(f"   duplicate: {service_path}")
            print(f"   action: remove/rename service package root and import from {canonical_path}")

    if duplicate_modules:
        print("\nConflicting module names:")
        for module_name, canonical_paths, service_paths in duplicate_modules:
            print(f" - module '{module_name}':")
            print(f"   canonical: {canonical_paths[0]}")
            print(f"   duplicate: {service_paths[0]}")
            print("   action: keep canonical module in value_fabric/layer5 and delete/rename duplicate")

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
