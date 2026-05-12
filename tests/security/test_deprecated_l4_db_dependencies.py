from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
L4_ROUTE_DIRS = [
    PROJECT_ROOT / "services" / "layer4-agents" / "src" / "api" / "routes",
    PROJECT_ROOT / "services" / "layer4-agents" / "src" / "tenants" / "api" / "routes",
    PROJECT_ROOT / "services" / "layer4-agents" / "src" / "feature_flags" / "api",
    PROJECT_ROOT / "services" / "layer4-agents" / "src" / "registry" / "api",
]


def _find_deprecated_dep_violations(file_path: Path) -> list[tuple[int, str]]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    violations: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "Depends":
            for arg in node.args:
                if isinstance(arg, ast.Name) and arg.id in {"get_db", "get_db_with_tenant"}:
                    violations.append((node.lineno, arg.id))
    return violations


def test_protected_routes_disallow_deprecated_db_dependencies() -> None:
    violations: list[str] = []

    for route_dir in L4_ROUTE_DIRS:
        if not route_dir.exists():
            continue
        for file_path in sorted(route_dir.glob("*.py")):
            if file_path.name.startswith("__"):
                continue
            for line, dep_name in _find_deprecated_dep_violations(file_path):
                rel_path = file_path.relative_to(PROJECT_ROOT)
                violations.append(f"{rel_path}:{line} uses Depends({dep_name})")

    assert not violations, (
        "Deprecated DB dependencies are wired into Layer 4 protected routes. "
        "Use Depends(get_db_from_context) for tenant-isolated DB access.\n"
        + "\n".join(violations)
    )
