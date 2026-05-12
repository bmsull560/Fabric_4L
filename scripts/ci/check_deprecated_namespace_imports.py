#!/usr/bin/env python3
"""Report internal imports that still use deprecated compatibility namespaces."""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (Path("services"), Path("value_fabric"), Path("tests"), Path("scripts"))
DEPRECATED_PREFIXES = ("value_fabric.layer1_ingestion", "value_fabric.layer3_knowledge")
ALLOWLIST = {
    Path("value_fabric/layer1_ingestion/__init__.py"),
    Path("value_fabric/layer1_ingestion/src/__init__.py"),
    Path("value_fabric/layer3_knowledge/__init__.py"),
    Path("value_fabric/layer3_knowledge/src/__init__.py"),
    Path("tests/ci/test_deprecated_namespace_imports.py"),
}


@dataclass(frozen=True)
class DeprecatedImport:
    path: str
    line: int
    statement: str
    deprecated_namespace: str


def _iter_python_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        abs_root = repo_root / root
        if not abs_root.exists():
            continue
        for file_path in abs_root.rglob("*.py"):
            rel = file_path.relative_to(repo_root)
            if rel in ALLOWLIST:
                continue
            files.append(file_path)
    return sorted(files)


def _deprecated_target(name: str) -> str | None:
    for prefix in DEPRECATED_PREFIXES:
        if name == prefix or name.startswith(prefix + "."):
            return prefix
    return None


def _scan_file(file_path: Path, repo_root: Path) -> list[DeprecatedImport]:
    source = file_path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    lines = source.splitlines()
    rel = str(file_path.relative_to(repo_root))
    findings: list[DeprecatedImport] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                prefix = _deprecated_target(alias.name)
                if prefix:
                    findings.append(DeprecatedImport(rel, node.lineno, lines[node.lineno - 1].strip(), prefix))
        elif isinstance(node, ast.ImportFrom) and node.module:
            prefix = _deprecated_target(node.module)
            if prefix:
                findings.append(DeprecatedImport(rel, node.lineno, lines[node.lineno - 1].strip(), prefix))

    return findings


def scan(repo_root: Path) -> list[DeprecatedImport]:
    findings: list[DeprecatedImport] = []
    for file_path in _iter_python_files(repo_root):
        findings.extend(_scan_file(file_path, repo_root))
    return sorted(findings, key=lambda x: (x.path, x.line, x.statement))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    findings = scan(Path(args.repo_root).resolve())
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    else:
        print(f"Deprecated namespace import findings: {len(findings)}")
        for f in findings:
            print(f"{f.path}:{f.line} :: {f.statement} [{f.deprecated_namespace}]")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
