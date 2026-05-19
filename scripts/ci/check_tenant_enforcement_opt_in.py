#!/usr/bin/env python3
"""CI gate: detect routes that accept tenant_id in the request body without
calling enforce_authenticated_tenant.

F-15 (spec.md): enforce_authenticated_tenant is opt-in per route. Any route
that accepts a Pydantic body model containing a tenant_id field and does NOT
call enforce_authenticated_tenant is silently vulnerable to cross-tenant writes.

Exit codes:
  0 — no new violations (may have baseline-tracked ones)
  1 — new violations introduced since baseline
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_FILE = Path(__file__).parent / "tenant_enforcement_opt_in_baseline.txt"

# Router files to scan (standalone API — the stack where this gap exists)
SCAN_ROOTS = [
    ROOT / "services" / "api" / "app" / "routers",
]

ENFORCEMENT_CALL = "enforce_authenticated_tenant"
TENANT_ID_FIELD = "tenant_id"


def _has_tenant_id_param(func_node: ast.FunctionDef) -> bool:
    """Return True if the function has a parameter whose annotation suggests
    it carries a tenant_id body field (i.e., a Pydantic model argument that
    is not a Depends() call)."""
    for arg in func_node.args.args:
        name = arg.arg
        if name == TENANT_ID_FIELD:
            return True
    return False


def _body_reads_tenant_id(func_node: ast.FunctionDef) -> bool:
    """Return True if the function READS body.tenant_id (not just assigns it).

    We distinguish reads from writes:
    - Write (safe):  body.tenant_id = tenant_id   (overwriting with JWT value)
    - Read (risky):  db.foo(tenant_id=body.tenant_id)  (trusting body value)

    Only reads without a preceding enforce_authenticated_tenant call are flagged.
    """
    param_names = {arg.arg for arg in func_node.args.args}

    for node in ast.walk(func_node):
        # Look for Attribute loads (reads), not stores (assignments)
        if (
            isinstance(node, ast.Attribute)
            and node.attr == TENANT_ID_FIELD
            and isinstance(node.value, ast.Name)
            and node.value.id in param_names
            and isinstance(node.ctx, ast.Load)
        ):
            # Check the parent context: if this attribute is the target of an
            # assignment (e.g., body.tenant_id = ...), skip it.
            # We do this by checking if the node appears as an assignment target
            # in any Assign/AugAssign in the function.
            # Since ast.walk doesn't give parent info, we use a separate pass.
            return True
    return False


def _tenant_id_reads_are_only_assignments(func_node: ast.FunctionDef) -> bool:
    """Return True if every .tenant_id access on a body param is an assignment target."""
    param_names = {arg.arg for arg in func_node.args.args}
    assignment_targets: set[int] = set()

    # Collect all assignment target node ids
    for node in ast.walk(func_node):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                assignment_targets.add(id(target))
                for child in ast.walk(target):
                    assignment_targets.add(id(child))
        if isinstance(node, (ast.AugAssign, ast.AnnAssign)):
            if node.target:
                assignment_targets.add(id(node.target))
                for child in ast.walk(node.target):
                    assignment_targets.add(id(child))

    for node in ast.walk(func_node):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == TENANT_ID_FIELD
            and isinstance(node.value, ast.Name)
            and node.value.id in param_names
            and isinstance(node.ctx, ast.Load)
            and id(node) not in assignment_targets
        ):
            return False
    return True


def _calls_enforcement(func_node: ast.FunctionDef) -> bool:
    """Return True if the function body calls enforce_authenticated_tenant."""
    for node in ast.walk(func_node):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == ENFORCEMENT_CALL:
                return True
            if isinstance(func, ast.Attribute) and func.attr == ENFORCEMENT_CALL:
                return True
    return False


def _imports_enforcement(tree: ast.Module) -> bool:
    """Return True if the module imports enforce_authenticated_tenant."""
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == ENFORCEMENT_CALL or (alias.asname or "") == ENFORCEMENT_CALL:
                    return True
        if isinstance(node, ast.Import):
            for alias in node.names:
                if ENFORCEMENT_CALL in alias.name:
                    return True
    return False


def scan_file(path: Path) -> list[str]:
    """Return a list of violation strings for the given file."""
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    violations: list[str] = []

    # Only flag files that import enforce_authenticated_tenant — others
    # may legitimately not need it (e.g., read-only routers).
    # We also flag files that have body models with tenant_id even if they
    # don't import the enforcement helper (that's the gap we're catching).
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        func = node  # type: ignore[assignment]

        # Skip non-route functions (no router decorator)
        decorators = [ast.unparse(d) for d in func.decorator_list]
        is_route = any(
            "router." in d or ".get(" in d or ".post(" in d or ".put(" in d
            or ".patch(" in d or ".delete(" in d
            for d in decorators
        )
        if not is_route:
            continue

        # Check if the route body READS .tenant_id from a body parameter
        # (assignments like body.tenant_id = tenant_id are safe — skip them)
        if not _body_reads_tenant_id(func):
            continue
        if _tenant_id_reads_are_only_assignments(func):
            continue

        # If it accesses tenant_id on a body param but doesn't call enforcement
        if not _calls_enforcement(func):
            rel = path.relative_to(ROOT)
            violations.append(
                f"{rel}:{func.lineno}: route '{func.name}' accesses body.tenant_id "
                f"without calling {ENFORCEMENT_CALL}"
            )

    return violations


def main() -> int:
    all_violations: list[str] = []
    for scan_root in SCAN_ROOTS:
        for py_file in sorted(scan_root.rglob("*.py")):
            all_violations.extend(scan_file(py_file))

    current = sorted(all_violations)

    # Load baseline
    if BASELINE_FILE.exists():
        baseline = sorted(
            line.strip()
            for line in BASELINE_FILE.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    else:
        baseline = []

    introduced = [v for v in current if v not in baseline]
    resolved = [v for v in baseline if v not in current]

    if introduced:
        print("FAIL: New tenant enforcement opt-in violations detected:")
        for v in introduced:
            print(f"  {v}")
        print(
            "\nFix: call enforce_authenticated_tenant(body_tenant_id=..., "
            "authenticated_tenant_id=tenant_id, ...) in each flagged route."
        )
        return 1

    if resolved:
        print("INFO: Violations resolved since baseline (update baseline if intentional):")
        for v in resolved:
            print(f"  {v}")

    tracked = len(baseline)
    print(
        f"PASS: No new tenant enforcement opt-in violations "
        f"({tracked} baseline-tracked violation(s))."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
