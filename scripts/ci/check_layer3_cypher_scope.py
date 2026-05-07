#!/usr/bin/env python3
"""Fail on high-risk Layer 3 Cypher construction patterns.

This gate intentionally targets injection-prone patterns that bypass tenant
parameters. It is not a full Cypher parser; it complements tenant isolation
tests and the ScopedQuery builder boundary.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = ROOT / "services" / "layer3-knowledge" / "src"
SKIP_PARTS = {"migrations", "__pycache__"}


class Finding:
    def __init__(self, path: Path, line: int, message: str) -> None:
        self.path = path
        self.line = line
        self.message = message

    def __str__(self) -> str:
        rel = self.path.relative_to(ROOT)
        return f"{rel}:{self.line}: {self.message}"


def _contains_name(node: ast.AST, names: set[str]) -> bool:
    return any(isinstance(child, ast.Name) and child.id in names for child in ast.walk(node))


def _string_value(node: ast.AST) -> str:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        return "".join(part.value if isinstance(part, ast.Constant) else "{}" for part in node.values)
    return ""


def scan_file(path: Path) -> list[Finding]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    findings: list[Finding] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr):
            rendered = _string_value(node)
            if "tenant_id:" in rendered and _contains_name(node, {"tenant_id", "effective_tenant_id"}):
                findings.append(
                    Finding(path, node.lineno, "tenant_id must be passed as a Neo4j parameter, not interpolated")
                )
            if "type(" in rendered and _contains_name(node, {"relationship_types", "rel_types_str"}):
                findings.append(
                    Finding(path, node.lineno, "relationship type filters must use validated parameter lists")
                )

        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr != "run" or not node.args:
                continue
            first_arg = node.args[0]
            if isinstance(first_arg, ast.JoinedStr):
                findings.append(
                    Finding(path, node.lineno, "session.run must not receive an inline f-string Cypher query")
                )

    return findings


def iter_python_files(target: Path) -> list[Path]:
    files: list[Path] = []
    for path in target.rglob("*.py"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        files.append(path)
    return sorted(files)


def main() -> int:
    target = (ROOT / sys.argv[1]).resolve() if len(sys.argv) > 1 else DEFAULT_TARGET
    findings: list[Finding] = []
    for path in iter_python_files(target):
        findings.extend(scan_file(path))

    if findings:
        print("Layer 3 Cypher scope gate failed:")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print("Layer 3 Cypher scope gate passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
