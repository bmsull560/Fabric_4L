#!/usr/bin/env python3
"""Python enforcement script for Fabric 4L platform contract.

Scans value-fabric/ and shared/ for non-canonical patterns.
 - ERROR: violations that block CI.
 - WARN: violations that escalate to ERROR after the migration deadline.
"""

import os
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules", ".git", ".pytest_cache", ".mypy_cache", ".ruff_cache", "dist", "build"}

# Error patterns: (pattern, regex, description)
ERROR_PATTERNS = [
    ("get_db_usage", r"Depends\s*\(\s*get_db\b", "Use get_db_from_context() instead of get_db()"),
    ("get_db_with_tenant_usage", r"Depends\s*\(\s*get_db_with_tenant\b", "Use get_db_from_context() instead of get_db_with_tenant()"),
    ("db_session_usage", r"with\s+db_session\s*\(", "Use db_session_for_context() instead of db_session()"),
    ("old_request_state", r"request\.state\.context\b", "Use request.state.governance_context instead of request.state.context"),
    ("manual_db_commit", r"await\s*db\s*\.\s*commit\s*\(", "Route handlers MUST NOT call db.commit() or db.rollback()"),
    ("manual_db_rollback", r"await\s*db\s*\.\s*rollback\s*\(", "Route handlers MUST NOT call db.commit() or db.rollback()"),
]

# Warn patterns: (pattern, regex, description, deadline)
WARN_PATTERNS = [
    ("raw_dict_agent_return", r"return\s*\{", "Agent execute() should return a Pydantic model or use AgentResultEnvelope", "2026-06-30"),
    ("inline_tool_definition", r"class\s*\w+Tool\s*\(.*name\s*=\s*\"\w+\"", "Tools must be defined in their own module and registered", "2026-06-15"),
]


def should_skip_dir(dirname: str) -> bool:
    return dirname in SKIP_DIRS


def scan_file(path: str):
    violations = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except (UnicodeDecodeError, OSError):
        return violations

    for pattern_name, regex, description in ERROR_PATTERNS:
        for match in re.finditer(regex, content):
            line_number = content[:match.start()].count("\n") + 1
            violations.append(("ERROR", path, line_number, pattern_name, description))

    for pattern_name, regex, description, deadline in WARN_PATTERNS:
        for match in re.finditer(regex, content):
            line_number = content[:match.start()].count("\n") + 1
            violations.append(("WARN", path, line_number, pattern_name, description, deadline))

    return violations


def main():
    targets = [
        PROJECT_ROOT / "value-fabric",
        PROJECT_ROOT / "shared",
    ]

    all_violations = []
    for target in targets:
        if not target.exists():
            continue
        for root, dirs, files in os.walk(target):
            # Modify dirs in-place to skip unwanted directories
            dirs[:] = [d for d in dirs if not should_skip_dir(d)]
            for file in files:
                if file.endswith(".py"):
                    path = os.path.join(root, file)
                    all_violations.extend(scan_file(path))

    errors = [v for v in all_violations if v[0] == "ERROR"]
    warnings = [v for v in all_violations if v[0] == "WARN"]

    if errors:
        print("== Platform Contract Violations ==", file=sys.stderr)
        for _, path, line, name, desc in errors:
            rel = Path(path).relative_to(PROJECT_ROOT)
            print(f"ERROR: {rel}::{line} [{name}] {desc}", file=sys.stderr)
    if warnings:
        for _, path, line, name, desc, deadline in warnings:
            rel = Path(path).relative_to(PROJECT_ROOT)
            print(f"WARN: {rel}::{line} [{name}] {desc} (deadline: {deadline})", file=sys.stderr)

    print(f"\nResults: {len(errors)} errors, {len(warnings)} warnings.")

    if errors:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
