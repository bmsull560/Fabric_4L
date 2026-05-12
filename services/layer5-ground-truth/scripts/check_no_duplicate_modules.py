#!/usr/bin/env python3
"""Fail CI when Layer 5 compatibility modules drift from shim-only adapters."""

from __future__ import annotations

import ast
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
CANONICAL_ROOT = REPO_ROOT / "services" / "layer5-ground-truth" / "src" / "layer5_ground_truth"
SHIM_ROOT = REPO_ROOT / "value_fabric" / "layer5"


def _py_files(root: Path) -> list[Path]:
    return sorted(path for path in root.rglob("*.py") if "__pycache__" not in path.parts)


def _canonical_module_for(rel: Path) -> str:
    parts = ["layer5_ground_truth", *rel.with_suffix("").parts]
    if rel.name == "__init__.py":
        parts = parts[:-1]
    return ".".join(parts)


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
    if len(body) == 1 and isinstance(body[0], ast.ImportFrom):
        node = body[0]
        return node.module == expected_module and len(node.names) == 1 and node.names[0].name == "*"

    return (
        f'_CANONICAL_MODULE = "{expected_module}"' in text
        and "from importlib import import_module as _import_module" in text
        and "_module = _import_module(_CANONICAL_MODULE)" in text
    )


def _shim_violations() -> list[str]:
    violations: list[str] = []
    canonical_files = {path.relative_to(CANONICAL_ROOT) for path in _py_files(CANONICAL_ROOT)}
    shim_files = {path.relative_to(SHIM_ROOT) for path in _py_files(SHIM_ROOT)}

    for rel in sorted(canonical_files - shim_files):
        violations.append(f"missing shim for canonical module: value_fabric/layer5/{rel.as_posix()}")
    for rel in sorted(shim_files - canonical_files):
        violations.append(f"shim without canonical module: value_fabric/layer5/{rel.as_posix()}")

    for rel in sorted(canonical_files & shim_files):
        expected_module = _canonical_module_for(rel)
        if not _is_thin_shim(SHIM_ROOT / rel, expected_module):
            violations.append(
                "non-shim implementation in compatibility tree: "
                f"value_fabric/layer5/{rel.as_posix()} must re-export {expected_module}"
            )

    for path in _py_files(CANONICAL_ROOT):
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(REPO_ROOT).as_posix()
        if "Compatibility shim" in text and "from layer5_ground_truth" in text and "import *" in text:
            violations.append(f"canonical tree contains a self-recursive compatibility shim: {rel}")
        if "sys.path" in text:
            violations.append(f"canonical tree must not mutate sys.path: {rel}")

    return violations


def main() -> int:
    violations = _shim_violations()
    if not violations:
        print("OK: Layer 5 canonical tree and compatibility shims are aligned.")
        return 0

    print("ERROR: Layer 5 source-of-truth contract failed.")
    print("Canonical source-of-truth: services/layer5-ground-truth/src/layer5_ground_truth")
    print("Compatibility tree must stay shim-only: value_fabric/layer5")
    for violation in violations:
        print(f" - {violation}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
