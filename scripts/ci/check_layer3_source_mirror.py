#!/usr/bin/env python3
"""Fail CI when Layer 3 compatibility shims drift from canonical runtime modules."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANONICAL_ROOT = ROOT / "value_fabric" / "layer3"
COMPAT_ROOT = ROOT / "services" / "layer3-knowledge" / "src"

# These are intentionally mirrored as compatibility shims in the service tree.
MIRRORED_DIRS = (
    "analytics",
    "auth",
    "backup",
    "config",
    "db",
    "gateway",
    "ingestion",
    "load_balancing",
    "models",
    "performance",
    "rate_limiting",
    "retrieval",
    "schema",
    "security",
    "services",
    "tracing",
)
MIRRORED_FILES = ("__init__.py", "logging_config.py")

EXCEPTION_DIRS = ("api", "agents", "cache", "docs", "metrics", "migrations")
EXCEPTION_FILES = ("config.py",)
EXCEPTION_OWNER = "Owner: layer3-knowledge"
EXCEPTION_TARGET = "Removal/migration target: 2026-09-30"


def _py_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _canonical_module_for(rel: Path) -> str:
    parts = ["value_fabric", "layer3", *rel.with_suffix("").parts]
    if rel.name == "__init__.py":
        parts = parts[:-1]
    return ".".join(parts)


def _is_mirrored(rel: Path) -> bool:
    if rel.parts and rel.parts[0] in MIRRORED_DIRS:
        return True
    return rel.as_posix() in MIRRORED_FILES


def _is_thin_shim(path: Path, expected_module: str) -> bool:
    text = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError:
        return False

    body = [
        node
        for node in tree.body
        if not (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
        )
    ]
    return (
        len(body) == 1
        and isinstance(body[0], ast.ImportFrom)
        and body[0].module == expected_module
        and len(body[0].names) == 1
        and body[0].names[0].name == "*"
    )



def _is_exception_path(rel: Path) -> bool:
    return rel.as_posix() in EXCEPTION_FILES or (rel.parts and rel.parts[0] in EXCEPTION_DIRS)


def _has_exception_docstring(path: Path) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except SyntaxError:
        return False
    doc = ast.get_docstring(tree)
    if not doc:
        return False
    return "Allowed service-local exception" in doc and EXCEPTION_OWNER in doc and EXCEPTION_TARGET in doc

def _violations() -> list[str]:
    violations: list[str] = []
    canonical_files = {path.relative_to(CANONICAL_ROOT) for path in _py_files(CANONICAL_ROOT)}
    mirrored_files = {rel for rel in canonical_files if _is_mirrored(rel)}
    compat_files = {path.relative_to(COMPAT_ROOT) for path in _py_files(COMPAT_ROOT)}

    for rel in sorted(mirrored_files - compat_files):
        violations.append(f"missing compatibility shim: services/layer3-knowledge/src/{rel.as_posix()}")

    for rel in sorted((compat_files - mirrored_files)):
        if _is_mirrored(rel):
            violations.append(
                "mirrored path has no canonical source module: "
                f"services/layer3-knowledge/src/{rel.as_posix()}"
            )

    for rel in sorted(mirrored_files & compat_files):
        expected_module = _canonical_module_for(rel)
        compat_path = COMPAT_ROOT / rel
        text = compat_path.read_text(encoding="utf-8")
        if any(marker in text for marker in ("<<<<<<<", "=======", ">>>>>>>")):
            violations.append(
                "merge conflict markers detected in compatibility path: "
                f"services/layer3-knowledge/src/{rel.as_posix()}"
            )
            continue
        if not _is_thin_shim(compat_path, expected_module):
            violations.append(
                "non-shim implementation in compatibility tree: "
                f"services/layer3-knowledge/src/{rel.as_posix()} must re-export {expected_module}"
            )

    for rel in sorted(compat_files):
        if not _is_exception_path(rel):
            continue
        if not _has_exception_docstring(COMPAT_ROOT / rel):
            violations.append(
                "service-local exception missing required governance docstring: "
                f"services/layer3-knowledge/src/{rel.as_posix()}"
            )

    for path in _py_files(CANONICAL_ROOT):
        rel_path = path.relative_to(CANONICAL_ROOT)
        if not _is_mirrored(rel_path):
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT).as_posix()
        if "Compatibility shim" in text and "from value_fabric.layer3" in text and "import *" in text:
            violations.append(f"canonical tree contains a self-recursive compatibility shim: {rel}")
        if "sys.path" in text:
            violations.append(f"canonical tree must not mutate sys.path: {rel}")

    return violations


def main() -> int:
    violations = _violations()
    if not violations:
        print("OK: Layer 3 canonical tree and compatibility shims are aligned.")
        return 0

    print("ERROR: Layer 3 source-of-truth contract failed.")
    print("Canonical source-of-truth: value_fabric/layer3")
    print("Compatibility shims: services/layer3-knowledge/src (mirrored paths only)")
    for violation in violations:
        print(f" - {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
