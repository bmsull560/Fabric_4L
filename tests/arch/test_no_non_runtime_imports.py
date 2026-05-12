"""Architecture tests preventing runtime imports from non-runtime roots."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

PYTHON_RUNTIME_ROOTS = (
    REPO_ROOT / "value_fabric",
    REPO_ROOT / "services",
    REPO_ROOT / "packages/shared/src",
)

SKIP_DIR_NAMES = {"tests", "test", "__pycache__", ".venv", "venv", "migrations"}
FORBIDDEN_IMPORT_PREFIXES = (
    "prototypes",
    "docs.archive",
)


def _iter_python_runtime_files() -> list[Path]:
    files: list[Path] = []
    for root in PYTHON_RUNTIME_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            rel_parts = path.relative_to(REPO_ROOT).parts
            if any(part in SKIP_DIR_NAMES for part in rel_parts):
                continue
            files.append(path)
    return files


def _violations_for_file(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    rel_path = path.relative_to(REPO_ROOT)
    violations: list[str] = []

    for node in ast.walk(tree):
        module_name = None
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name
                if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                    violations.append(f"{rel_path}:{node.lineno} imports forbidden root '{module_name}'")
        elif isinstance(node, ast.ImportFrom) and node.module:
            module_name = node.module
            if module_name.startswith(FORBIDDEN_IMPORT_PREFIXES):
                violations.append(f"{rel_path}:{node.lineno} imports forbidden root '{module_name}'")

    return violations


def test_runtime_python_modules_do_not_import_non_runtime_roots() -> None:
    violations: list[str] = []
    for path in _iter_python_runtime_files():
        violations.extend(_violations_for_file(path))

    assert not violations, "\n".join(violations)
