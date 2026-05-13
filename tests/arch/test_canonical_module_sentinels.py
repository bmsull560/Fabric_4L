"""Sentinel checks for canonical runtime module ownership.

These tests keep a *small*, high-signal map of critical modules where
canonical-vs-compatibility ownership must not drift.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class CanonicalModuleSentinel:
    """Canonical + compatibility path pair for a critical module."""

    name: str
    canonical_path: str
    compatibility_path: str


# Keep this list intentionally small and high-impact.
# Add entries only for modules that would cause broad architecture drift
# if logic moved into compatibility-only roots.
SENTINELS: tuple[CanonicalModuleSentinel, ...] = (
    # Layer 3 migrated to service-first per ADR-027 (2026-05-13).
    # Compatibility is handled by namespace package __path__ appending
    # in value_fabric/layer3/__init__.py; no shim file remains.
    CanonicalModuleSentinel(
        name="layer3_api_models",
        canonical_path="services/layer3-knowledge/src/api/models.py",
        compatibility_path="value_fabric/layer3/__init__.py",
    ),
    CanonicalModuleSentinel(
        name="layer5_truth_object_model",
        canonical_path="services/layer5-ground-truth/src/layer5_ground_truth/models/truth_object.py",
        compatibility_path="value_fabric/layer5/models/truth_object.py",
    ),
    CanonicalModuleSentinel(
        name="layer5_api_main",
        canonical_path="services/layer5-ground-truth/src/layer5_ground_truth/api/main.py",
        compatibility_path="value_fabric/layer5/api/main.py",
    ),
)


def _parse_module(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _compatibility_has_local_implementation(path: Path) -> bool:
    """Return True when compatibility module defines local implementation logic.

    Compatibility files should only act as shims/re-exports for sentinels.
    """

    tree = _parse_module(path)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            return True
    return False


def test_canonical_sentinel_paths_exist() -> None:
    missing: list[str] = []
    for sentinel in SENTINELS:
        canonical = REPO_ROOT / sentinel.canonical_path
        compatibility = REPO_ROOT / sentinel.compatibility_path
        if not canonical.exists():
            missing.append(f"{sentinel.name}: missing canonical module {sentinel.canonical_path}")
        if not compatibility.exists():
            missing.append(
                f"{sentinel.name}: missing compatibility module {sentinel.compatibility_path}"
            )

    assert not missing, "\n".join(missing)


def test_sentinel_compatibility_modules_are_shims_only() -> None:
    violations: list[str] = []
    for sentinel in SENTINELS:
        compatibility = REPO_ROOT / sentinel.compatibility_path
        if _compatibility_has_local_implementation(compatibility):
            violations.append(
                f"{sentinel.name}: implementation logic found in compatibility path "
                f"{sentinel.compatibility_path}; move logic to canonical path "
                f"{sentinel.canonical_path}"
            )

    assert not violations, "\n".join(violations)


# ---------------------------------------------------------------------------
# Layer 5 — Ground Truth canonical import regression (ADR-027)
# ---------------------------------------------------------------------------


def test_layer5_ground_truth_imports_directly() -> None:
    """layer5_ground_truth must be importable without value_fabric namespace."""
    import layer5_ground_truth

    assert layer5_ground_truth.__file__ is not None


def test_layer5_api_imports_directly() -> None:
    """layer5_ground_truth.api must be importable via canonical path."""
    import layer5_ground_truth.api

    assert layer5_ground_truth.api.__file__ is not None


def test_layer5_models_imports_directly() -> None:
    """layer5_ground_truth.models must be importable via canonical path."""
    import layer5_ground_truth.models

    assert layer5_ground_truth.models.__file__ is not None


def test_layer5_resolves_to_canonical_service_tree() -> None:
    """layer5_ground_truth must resolve via services/layer5-ground-truth/src/."""
    import layer5_ground_truth

    canonical = (REPO_ROOT / "services" / "layer5-ground-truth" / "src" / "layer5_ground_truth").resolve()
    module_path = Path(layer5_ground_truth.__file__).parent.resolve()
    assert module_path == canonical, (
        f"layer5_ground_truth resolved to {module_path}, expected {canonical}"
    )


def test_layer5_no_production_imports_via_value_fabric_namespace() -> None:
    """Regression: no production code should import value_fabric.layer5.*.

    Layer 5 is fully migrated to service-first. Consumers must use
    layer5_ground_truth.* directly. The value_fabric/layer5/ shim
    remains for backward compatibility only.
    """
    import re
    import os

    pattern = re.compile(r"from value_fabric\.layer5|import value_fabric\.layer5")
    violations: list[str] = []
    skip_dirs = {".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".git", ".hypothesis"}

    # Only scan directories that contain production/runtime code
    scan_roots = [REPO_ROOT / d for d in ("services", "value_fabric", "scripts", "tests")]

    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(scan_root):
            # Prune skip directories
            dirnames[:] = [d for d in dirnames if d not in skip_dirs]
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                py_file = Path(dirpath) / fname
                rel_path = py_file.relative_to(REPO_ROOT).as_posix()
                # Skip shim files and tests that intentionally verify the shim
                if "value_fabric/layer5/" in rel_path:
                    continue
                if "test_check_layer5_shim" in rel_path:
                    continue
                if "test_canonical_module_sentinels" in rel_path:
                    continue
                if "test_import_topology" in rel_path:
                    continue

                content = py_file.read_text(encoding="utf-8")
                if pattern.search(content):
                    violations.append(str(rel_path))

    assert not violations, (
        "Found production imports via value_fabric.layer5:\n"
        + "\n".join(violations)
    )
