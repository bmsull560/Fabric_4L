#!/usr/bin/env python3
"""Governance gate for approved deprecation usage budget in hotspot paths."""
from __future__ import annotations
import argparse, json, re, sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = REPO_ROOT / "tests" / "baselines" / "deprecation-budget.json"
HOTSPOTS = [
    REPO_ROOT / "apps" / "web" / "src",
    REPO_ROOT / "services" / "layer4-agents" / "src",
    REPO_ROOT / "value_fabric" / "layer1_ingestion",
    REPO_ROOT / "value_fabric" / "layer3_knowledge",
]
FILE_GLOBS = ("*.py", "*.ts", "*.tsx", "*.js", "*.jsx", "*.md")

@dataclass(frozen=True)
class Rule:
    key: str
    regex: re.Pattern[str]

RULES = [
    Rule("ts_js_doc_deprecated", re.compile(r"@deprecated")),
    Rule("py_route_deprecated", re.compile(r"\bdeprecated\s*=\s*True\b")),
    Rule("py_deprecated_message", re.compile(r"\bis deprecated\b")),
]

def iter_files():
    for hotspot in HOTSPOTS:
        if not hotspot.exists():
            continue
        for glob in FILE_GLOBS:
            yield from hotspot.rglob(glob)

def scan_findings() -> set[str]:
    findings: set[str] = set()
    for path in iter_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
            for rule in RULES:
                if rule.regex.search(line):
                    findings.add(f"{rel}:{i}:{rule.key}")
    return findings

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=BASELINE_PATH)
    parser.add_argument("--strict-removal-dates", action="store_true", default=True)
    parser.add_argument("--allow-overdue", action="store_true")
    args = parser.parse_args()

    data = json.loads(args.baseline.read_text(encoding="utf-8"))
    approved = {item["id"] for item in data.get("approved", [])}
    findings = scan_findings()

    new_findings = sorted(findings - approved)
    stale_baseline = sorted(approved - findings)

    overdue: list[str] = []
    today = date.today()
    for item in data.get("approved", []):
        target = item.get("target_removal_date")
        if not target:
            continue
        if item["id"] not in findings:
            continue
        if date.fromisoformat(target) < today:
            overdue.append(f"{item['id']} (target_removal_date={target})")

    if stale_baseline:
        print("Stale baseline entries (already removed, please prune baseline):")
        for item in stale_baseline:
            print(f"  - {item}")

    if new_findings:
        print("New deprecated usages not in baseline:")
        for item in new_findings:
            print(f"  - {item}")

    if overdue:
        print("Overdue deprecated usages still present:")
        for item in overdue:
            print(f"  - {item}")

    if overdue and not args.allow_overdue:
        return 1
    if new_findings:
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
