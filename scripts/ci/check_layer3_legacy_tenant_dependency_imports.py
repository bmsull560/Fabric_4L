#!/usr/bin/env python3
"""Block new Layer 3 API imports from the legacy tenant dependency module.

The only approved Layer 3 Neo4j tenant dependency module is
``src.api.dependencies_tenant_secured``. ``dependencies_tenant`` is a temporary
compatibility shim that logs deprecation warnings and has a hard removal date of
2026-09-30.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SCAN_ROOT = Path("services/layer3-knowledge/src/api")
LEGACY_MODULE_SUFFIX = "dependencies_tenant"
CANONICAL_MODULE = "dependencies_tenant_secured"
ALLOWLIST = {
    Path("services/layer3-knowledge/src/api/dependencies_tenant.py"),
}


@dataclass(frozen=True)
class Finding:
    path: Path
    line: int
    statement: str

    def render(self, repo_root: Path) -> str:
        return f"{self.path.relative_to(repo_root).as_posix()}:{self.line}: {self.statement}"


def _is_legacy_module(module: str | None) -> bool:
    if not module:
        return False
    normalized = module.lstrip(".")
    return normalized == LEGACY_MODULE_SUFFIX or normalized.endswith(f".{LEGACY_MODULE_SUFFIX}")


def _scan_file(path: Path, repo_root: Path) -> list[Finding]:
    rel = path.relative_to(repo_root)
    if rel in ALLOWLIST:
        return []

    source = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [Finding(path, exc.lineno or 1, f"unable to parse Python file: {exc.msg}")]

    lines = source.splitlines()
    findings: list[Finding] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_legacy_module(alias.name):
                    findings.append(Finding(path, node.lineno, lines[node.lineno - 1].strip()))
        elif isinstance(node, ast.ImportFrom):
            if _is_legacy_module(node.module):
                findings.append(Finding(path, node.lineno, lines[node.lineno - 1].strip()))
                continue
            for alias in node.names:
                if alias.name != LEGACY_MODULE_SUFFIX:
                    continue
                if node.module in {"", None} or (node.module or "").lstrip(".").endswith("api"):
                    findings.append(Finding(path, node.lineno, lines[node.lineno - 1].strip()))
    return findings


def scan(repo_root: Path, scan_root: Path) -> list[Finding]:
    root = repo_root / scan_root
    if not root.exists():
        return []
    findings: list[Finding] = []
    for path in sorted(root.rglob("*.py")):
        findings.extend(_scan_file(path, repo_root))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--scan-root", default=str(DEFAULT_SCAN_ROOT))
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    findings = scan(repo_root, Path(args.scan_root))
    if not findings:
        print(f"Layer 3 tenant dependency import gate passed: use {CANONICAL_MODULE}.")
        return 0

    print("Layer 3 legacy tenant dependency imports found:")
    for finding in findings:
        print(f"  - {finding.render(repo_root)}")
    print(
        "\nMigrate these imports to services/layer3-knowledge/src/api/"
        f"{CANONICAL_MODULE}.py. The legacy shim is removal-targeted for 2026-09-30."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
