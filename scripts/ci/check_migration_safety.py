#!/usr/bin/env python3
"""Migration safety gate: fail if migration scripts contain unsafe patterns.

Checks for:
- print() in migration scripts (should use structured logging)
- destructive Cypher without MIGRATION_REVIEW_REQUIRED marker
- missing dry_run parameter
- Neo4j Enterprise-only constraints without Community fallback note
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_ROOTS = (
    REPO_ROOT / "value_fabric" / "layer3" / "migrations",
    REPO_ROOT / "services" / "layer2-extraction" / "migrations",
    REPO_ROOT / "services" / "layer3-knowledge" / "migrations",
    REPO_ROOT / "services" / "layer4-agents" / "migrations",
)

SKIP_DIRS = {"__pycache__", ".venv", ".hypothesis", ".git"}

DESTRUCTIVE_KEYWORDS = ("DETACH DELETE", "DROP ", "REMOVE ", "DROP CONSTRAINT", "DROP INDEX")
ENTERPRISE_KEYWORDS = ("NODE KEY", "EXISTS", "ASSERT exists")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    category: str
    message: str


def _iter_migration_files():
    import os
    for root in MIGRATION_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                if fname.endswith(".py"):
                    yield Path(dirpath) / fname


def scan() -> list[Finding]:
    findings: list[Finding] = []

    for path in _iter_migration_files():
        rel = str(path.relative_to(REPO_ROOT))
        source = path.read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines()

        has_dry_run_param = "dry_run" in source
        has_review_marker = "MIGRATION_REVIEW_REQUIRED" in source

        for i, line in enumerate(lines, start=1):
            # 1. print() in migrations
            if re.search(r"\bprint\(", line):
                findings.append(Finding(rel, i, "print_in_migration", "print() in migration script; use structured logging"))

            # 2. destructive Cypher without review marker
            upper = line.upper()
            if any(kw in upper for kw in DESTRUCTIVE_KEYWORDS):
                if not has_review_marker:
                    findings.append(Finding(rel, i, "destructive_without_marker", "destructive Cypher without MIGRATION_REVIEW_REQUIRED marker"))

            # 3. Enterprise-only constraints without fallback comment
            if any(kw in upper for kw in ENTERPRISE_KEYWORDS):
                # Check for Community fallback comment in surrounding 5 lines
                context = "\n".join(lines[max(0, i - 5) : i + 5])
                if "community" not in context.lower() and "fallback" not in context.lower():
                    findings.append(Finding(rel, i, "enterprise_no_fallback", "Neo4j Enterprise-only constraint without Community fallback note"))

        # 4. missing dry_run
        if not has_dry_run_param:
            findings.append(Finding(rel, 1, "missing_dry_run", "migration script lacks dry_run parameter"))

    seen = set()
    deduped = []
    for f in findings:
        key = (f.path, f.line, f.category, f.message)
        if key not in seen:
            seen.add(key)
            deduped.append(f)

    return deduped


BASELINE_PATH = REPO_ROOT / "docs" / "reference" / "migration-safety-baseline.json"


def _load_baseline() -> set[tuple[str, int, str, str]]:
    if not BASELINE_PATH.exists():
        return set()
    data = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    return {
        (str(item["path"]).replace("\\", "/"), int(item["line"]), str(item["category"]), str(item["message"]))
        for item in data.get("findings", [])
    }


def _subtract_baseline(
    findings: list[Finding], baseline: set[tuple[str, int, str, str]]
) -> list[Finding]:
    return [
        f for f in findings
        if (f.path.replace("\\", "/"), f.line, f.category, f.message) not in baseline
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--use-baseline", action="store_true")
    args = parser.parse_args(argv)

    findings = scan()
    if args.use_baseline:
        baseline = _load_baseline()
        findings = _subtract_baseline(findings, baseline)

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(f"Migration safety findings: {len(findings)}")
        for f in findings:
            print(f"  [{f.category}] {f.path}:{f.line} :: {f.message}")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
