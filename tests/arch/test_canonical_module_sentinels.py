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
    CanonicalModuleSentinel(
        name="layer3_api_models",
        canonical_path="value_fabric/layer3/api/models.py",
        compatibility_path="services/layer3-knowledge/src/api/models.py",
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
