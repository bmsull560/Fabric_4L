#!/usr/bin/env python3
"""Fail on high-risk Layer 3 Cypher construction patterns.

This gate intentionally targets injection-prone patterns that bypass tenant
parameters. It is not a full Cypher parser; it complements tenant isolation
tests and the ScopedQuery builder boundary.
"""

from __future__ import annotations

import ast
import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = ROOT / "services" / "layer3-knowledge" / "src"
SKIP_PARTS = {"migrations", "__pycache__"}
APPROVED_ROUTE_MARKERS = ("TenantScopedCypher", "custom_tenant_query", "match_node_query", "ScopedQuery", "strict-scoped-query-execution")


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

    is_route_file = "api/routes" in path.as_posix()
    source_lines = source.splitlines()
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
        if (
            is_route_file
            and isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and "MATCH (" in node.value
            and (
                lambda ln: not any(
                    marker in "\n".join(source_lines[max(0, ln - 12) : min(len(source_lines), ln + 12)])
                    for marker in APPROVED_ROUTE_MARKERS
                )
            )(node.lineno)
        ):
            findings.append(
                Finding(
                    path,
                    node.lineno,
                    "api/routes Cypher MATCH must be created via approved tenant-scoped helper",
                )
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", default=str(DEFAULT_TARGET))
    parser.add_argument("--report-json", default="", help="Optional JSON audit report path")
    args = parser.parse_args()

    target = (ROOT / args.target).resolve() if not Path(args.target).is_absolute() else Path(args.target)
    findings: list[Finding] = []
    files = iter_python_files(target)
    for path in files:
        findings.extend(scan_file(path))

    if args.report_json:
        report_path = (ROOT / args.report_json).resolve() if not Path(args.report_json).is_absolute() else Path(args.report_json)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(
            json.dumps(
                {
                    "target": str(target.relative_to(ROOT) if target.is_relative_to(ROOT) else target),
                    "files_scanned": len(files),
                    "findings": [
                        {
                            "path": str(finding.path.relative_to(ROOT)),
                            "line": finding.line,
                            "message": finding.message,
                        }
                        for finding in findings
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    if findings:
        print("Layer 3 Cypher scope gate failed:")
        for finding in findings:
            print(f"  {finding}")
        return 1

    print(f"Layer 3 Cypher scope gate passed. Files scanned: {len(files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
