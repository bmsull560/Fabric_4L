"""CI gate: enforce the Layer 3 monolith code freeze (ARCH-L3-007).

Rejects pull requests that add new HTTP route decorators to
``services/layer3-knowledge/src/api/app_monolith.py``.

New endpoints must be added to the v2 bounded routers under
``services/layer3-knowledge/src/api/routers/``.

Usage
-----
    # Check against the current working tree (local dev):
    python scripts/ci/check_l3_monolith_freeze.py

    # Check only lines added in a PR (CI mode, requires git):
    python scripts/ci/check_l3_monolith_freeze.py --diff-only --base-ref origin/main

Exit codes
----------
    0  No violations found.
    1  New route decorators detected in app_monolith.py.
"""

from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MONOLITH_PATH = REPO_ROOT / "services/layer3-knowledge/src/api/app_monolith.py"

# Regex for the diff-only mode: matches added lines (+) with a route decorator.
_ADDED_ROUTE_RE = re.compile(
    r"^\+\s*@app\.(get|post|put|patch|delete|options|head|websocket)\s*\(",
    re.MULTILINE,
)

# AST-based: decorator names that constitute HTTP route registrations on `app`.
_ROUTE_DECORATOR_ATTRS = {"get", "post", "put", "patch", "delete", "options", "head", "websocket"}

# Lines that existed before the freeze (baseline route count).
# We record the frozen set of route paths so the gate can distinguish
# pre-existing routes from newly added ones when running in full-file mode.
# This baseline is updated automatically when ARCH-L3-011 removes routes.
_FROZEN_ROUTE_BASELINE_FILE = Path(__file__).parent / "l3_monolith_route_baseline.txt"


def _load_baseline() -> set[str]:
    """Load the set of frozen route paths from the baseline file."""
    if not _FROZEN_ROUTE_BASELINE_FILE.exists():
        return set()
    lines = _FROZEN_ROUTE_BASELINE_FILE.read_text().splitlines()
    return {ln.strip() for ln in lines if ln.strip() and not ln.startswith("#")}


def _collect_routes_from_ast(source: str) -> list[tuple[int, str]]:
    """Return (lineno, path_or_repr) for every @app.<method>(...) decorator."""
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        print(f"  SyntaxError parsing {MONOLITH_PATH}: {exc}", file=sys.stderr)
        return []

    routes: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not (isinstance(func, ast.Attribute) and func.attr in _ROUTE_DECORATOR_ATTRS):
                continue
            if not (isinstance(func.value, ast.Name) and func.value.id == "app"):
                continue
            # Extract the first positional argument (the path string) if present.
            path_repr = "<dynamic>"
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                path_repr = str(decorator.args[0].value)
            routes.append((node.lineno, path_repr))
    return routes


def check_full_file() -> list[str]:
    """Return violation messages for routes not in the frozen baseline."""
    if not MONOLITH_PATH.exists():
        return [f"Monolith file not found: {MONOLITH_PATH}"]

    source = MONOLITH_PATH.read_text()
    routes = _collect_routes_from_ast(source)
    baseline = _load_baseline()

    violations: list[str] = []
    for lineno, path in routes:
        if path not in baseline:
            violations.append(
                f"  {MONOLITH_PATH.relative_to(REPO_ROOT)}:{lineno}  "
                f"New route '{path}' added to frozen monolith. "
                f"Add it to api/routers/ instead."
            )
    return violations


def check_diff(base_ref: str) -> list[str]:
    """Return violation messages for added route lines in the diff vs base_ref."""
    try:
        diff = subprocess.check_output(
            ["git", "diff", base_ref, "--", str(MONOLITH_PATH)],
            cwd=REPO_ROOT,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        return [f"git diff failed: {exc}"]

    violations: list[str] = []
    for match in _ADDED_ROUTE_RE.finditer(diff):
        method = match.group(1)
        violations.append(
            f"  New @app.{method}(...) route added to frozen monolith "
            f"(app_monolith.py). Add it to api/routers/ instead."
        )
    return violations


def generate_baseline() -> None:
    """Write the current route set to the baseline file (run once to initialise)."""
    if not MONOLITH_PATH.exists():
        print(f"Monolith not found: {MONOLITH_PATH}", file=sys.stderr)
        sys.exit(1)

    source = MONOLITH_PATH.read_text()
    routes = _collect_routes_from_ast(source)
    paths = sorted({path for _, path in routes})

    _FROZEN_ROUTE_BASELINE_FILE.write_text(
        "# Auto-generated by check_l3_monolith_freeze.py --generate-baseline\n"
        "# Do not edit manually. Re-run with --generate-baseline after ARCH-L3-011 removes routes.\n"
        + "\n".join(paths)
        + "\n"
    )
    print(f"Baseline written: {len(paths)} routes → {_FROZEN_ROUTE_BASELINE_FILE}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--diff-only",
        action="store_true",
        help="Only check lines added in the diff (faster, requires git).",
    )
    parser.add_argument(
        "--base-ref",
        default="origin/main",
        help="Git ref to diff against (default: origin/main).",
    )
    parser.add_argument(
        "--generate-baseline",
        action="store_true",
        help="Write the current monolith routes to the baseline file and exit.",
    )
    args = parser.parse_args()

    if args.generate_baseline:
        generate_baseline()
        return 0

    if args.diff_only:
        violations = check_diff(args.base_ref)
    else:
        violations = check_full_file()

    if violations:
        print("FAIL: Layer 3 monolith freeze violation (ARCH-L3-007)", file=sys.stderr)
        for v in violations:
            print(v, file=sys.stderr)
        print(
            "\nNew endpoints must be added to "
            "services/layer3-knowledge/src/api/routers/",
            file=sys.stderr,
        )
        return 1

    print(f"OK: No new routes added to app_monolith.py ({len(violations)} violations)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
