#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGET = ROOT / "services" / "layer3-knowledge" / "src"
BASELINE_SAFE_PATH = Path("services/layer3-knowledge/src/db/tenant_queries.py")

CLASS_SAFE = "Safe"
CLASS_UNSAFE = "Unsafe"
CLASS_UNKNOWN = "Unknown"

APPROVED_HELPERS = {"execute_tenant_scoped", "execute_tenant_query", "execute_scoped_query", "run_tenant_query"}

@dataclass
class Finding:
    path: Path
    line: int
    function: str
    classification: str
    reason: str

class Visitor(ast.NodeVisitor):
    def __init__(self, path: Path):
        self.path = path
        self.findings: list[Finding] = []
        self.stack: list[str] = []

    def _fn(self) -> str:
        return self.stack[-1] if self.stack else "<module>"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.stack.append(node.name)
        self.generic_visit(node)
        self.stack.pop()

    def visit_Call(self, node: ast.Call) -> None:
        classification: str | None = None
        reason = ""
        if isinstance(node.func, ast.Attribute) and node.func.attr == "run":
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "session":
                classification = CLASS_SAFE if self.path == (ROOT / BASELINE_SAFE_PATH) else CLASS_UNSAFE
                reason = (
                    "baseline-safe reference implementation" if classification == CLASS_SAFE
                    else "raw session.run() detected; use approved tenant-scoping helper wrapper"
                )
        elif isinstance(node.func, ast.Name) and node.func.id in APPROVED_HELPERS:
            classification = CLASS_SAFE
            reason = f"approved tenant-scoping helper used: {node.func.id}"

        if classification:
            self.findings.append(Finding(self.path, getattr(node, "lineno", 1), self._fn(), classification, reason))
        self.generic_visit(node)


def iter_files(target: Path) -> list[Path]:
    return sorted(p for p in target.rglob("*.py") if "__pycache__" not in p.parts and "migrations" not in p.parts)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("target", nargs="?", default=str(DEFAULT_TARGET))
    parser.add_argument("--report-json", default="artifacts/layer3-query-entrypoint-matrix.json")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    all_findings: list[Finding] = []
    parse_errors: list[dict[str, str | int]] = []
    for path in iter_files(target):
        source = path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            parse_errors.append(
                {
                    "path": str(path.relative_to(ROOT)),
                    "line": int(exc.lineno or 1),
                    "message": str(exc.msg),
                }
            )
            continue
        v = Visitor(path)
        v.visit(tree)
        all_findings.extend(v.findings)

    report = {
        "target": str(target.relative_to(ROOT) if target.is_relative_to(ROOT) else target),
        "baseline_safe_reference": str(BASELINE_SAFE_PATH),
        "summary": {
            CLASS_SAFE: sum(1 for f in all_findings if f.classification == CLASS_SAFE),
            CLASS_UNSAFE: sum(1 for f in all_findings if f.classification == CLASS_UNSAFE),
            CLASS_UNKNOWN: sum(1 for f in all_findings if f.classification == CLASS_UNKNOWN),
            "parse_errors": len(parse_errors),
        },
        "parse_errors": parse_errors,
        "findings": [
            {
                "path": str(f.path.relative_to(ROOT)),
                "line": f.line,
                "function": f.function,
                "classification": f.classification,
                "reason": f.reason,
            }
            for f in all_findings
        ],
    }

    out = (ROOT / args.report_json).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    unsafe = report["summary"][CLASS_UNSAFE]
    print(f"Layer 3 query entrypoint matrix written: {out.relative_to(ROOT)}")
    print(f"Safe={report['summary'][CLASS_SAFE]} Unsafe={unsafe} Unknown={report['summary'][CLASS_UNKNOWN]}")
    if unsafe:
        print("FAIL: unsafe query entrypoints found")
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
