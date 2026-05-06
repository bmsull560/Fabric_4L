"""Report legacy root-level shared imports.

Production runtime code must import shared functionality through
``value_fabric.shared`` only. This scanner reports remaining
``shared`` / ``shared.*`` imports without making the migration
strictly blocking by default.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]

IGNORED_PATH_PARTS = {
    "archive",
    "docs",
    "generated",
    "node_modules",
    "reports",
    ".venv",
    "venv",
    "__pycache__",
    "prototypes",
    "experiments",
}


def _remove_prefix(value: str, prefix: str) -> str:
    """Remove prefix from string (Python < 3.9 compatibility)."""
    return value[len(prefix):] if value.startswith(prefix) else value

# Scope definitions for filtering
SCOPE_DEFINITIONS = {
    "all": [],  # No filtering
    "runtime": [],  # Production runtime only (services/ + packages/, excluding tests/)
    "tests": [],  # Test files only
    "executable": [],  # Executable code (services/, packages/, tests/, scripts/)
    "docs": [],  # Documentation files
}

EXPLICIT_TEST_ALLOWLIST = {
    Path("tests/contract/test_shared_import_boundary.py"),
}

SCAN_ROOTS = (
    Path("services"),
    Path("packages"),
    Path("shared"),
    Path("value_fabric"),
)


@dataclass(frozen=True)
class LegacySharedImport:
    path: str
    line: int
    import_statement: str
    recommended_replacement: str


def _is_ignored(relative_path: Path, scope: str = "all") -> bool:
    if relative_path in EXPLICIT_TEST_ALLOWLIST:
        return True

    # Use exact path segment matching instead of set intersection
    parts_lower = [part.lower() for part in relative_path.parts]
    for part in parts_lower:
        if part in IGNORED_PATH_PARTS:
            return True

    # Check for shared_import_boundary test files
    if "tests" in parts_lower and "shared_import_boundary" in str(relative_path).lower():
        return True

    # Scope-based filtering using pathlib parts
    top_level = parts_lower[0] if parts_lower else ""

    if scope == "runtime":
        # Include only production runtime (services/ + packages/, excluding tests/)
        if "tests" in parts_lower:
            return True
        if top_level not in {"services", "packages"}:
            return True
    elif scope == "tests":
        # Include only test files
        if "tests" not in parts_lower:
            return True
    elif scope == "executable":
        # Include executable code (services/, packages/, tests/, scripts/)
        # Exclude docs/, reports/, archive/, generated/, prototypes/, experiments/
        excluded_tops = {"docs", "reports", "archive", "generated", "prototypes", "experiments"}
        if top_level in excluded_tops:
            return True
        for part in parts_lower:
            if part in excluded_tops:
                return True
        # Exclude .md files (documentation)
        if relative_path.suffix == ".md":
            return True
    elif scope == "docs":
        # Include only documentation files
        if relative_path.suffix not in (".md", ".rst", ".txt"):
            return True

    return False


def _iter_python_files(repo_root: Path, scope: str = "all") -> list[Path]:
    files: list[Path] = []
    seen: set[Path] = set()

    for root in SCAN_ROOTS:
        absolute_root = repo_root / root
        if not absolute_root.exists():
            continue

        for file_path in absolute_root.rglob("*.py"):
            if file_path in seen:
                continue

            relative_path = file_path.relative_to(repo_root)
            if _is_ignored(relative_path, scope):
                continue

            seen.add(file_path)
            files.append(file_path)

    return sorted(files)


def _build_replacement_for_import(alias: ast.alias) -> str:
    if alias.name == "shared":
        return (
            "Replace with a specific canonical import such as "
            "`from value_fabric.shared.<module> import <symbol>`."
        )

    if alias.name.startswith("shared."):
        target = _remove_prefix(alias.name, "shared.")
        return (
            "Replace with a specific canonical import such as "
            f"`from value_fabric.shared.{target} import <symbol>`."
        )

    raise AssertionError("Unsupported import node passed to replacement builder")


def _build_replacement_for_import_from(node: ast.ImportFrom) -> str:
    if node.module is None:
        return "Replace with a specific canonical import from `value_fabric.shared`."

    if node.module == "shared":
        names = ", ".join(alias.name for alias in node.names)
        return f"Use `from value_fabric.shared import {names}`."

    target = _remove_prefix(node.module, "shared.")
    names = ", ".join(alias.name for alias in node.names)
    return f"Use `from value_fabric.shared.{target} import {names}`."


def _scan_file(file_path: Path, repo_root: Path) -> list[LegacySharedImport]:
    try:
        source = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        source = file_path.read_text(encoding="utf-8", errors="ignore")

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    lines = source.splitlines()
    findings: list[LegacySharedImport] = []
    relative_path = str(file_path.relative_to(repo_root))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "shared" or alias.name.startswith("shared."):
                    findings.append(
                        LegacySharedImport(
                            path=relative_path,
                            line=node.lineno,
                            import_statement=lines[node.lineno - 1].strip(),
                            recommended_replacement=_build_replacement_for_import(alias),
                        )
                    )
                    break

        if isinstance(node, ast.ImportFrom):
            if node.level != 0 or node.module is None:
                continue
            if node.module == "shared" or node.module.startswith("shared."):
                findings.append(
                    LegacySharedImport(
                        path=relative_path,
                        line=node.lineno,
                        import_statement=lines[node.lineno - 1].strip(),
                        recommended_replacement=_build_replacement_for_import_from(node),
                    )
                )

    return findings


def scan(repo_root: Path, scope: str = "all") -> list[LegacySharedImport]:
    findings: list[LegacySharedImport] = []
    for file_path in _iter_python_files(repo_root, scope):
        findings.extend(_scan_file(file_path, repo_root))
    return sorted(findings, key=lambda item: (item.path, item.line, item.import_statement))


def _render_text(findings: list[LegacySharedImport]) -> str:
    lines = [
        "Legacy shared import report",
        f"Findings: {len(findings)}",
        "",
    ]

    for finding in findings:
        lines.extend(
            [
                f"{finding.path}:{finding.line}",
                f"  import: {finding.import_statement}",
                f"  fix:    {finding.recommended_replacement}",
                "",
            ]
        )

    if not findings:
        lines.append("No legacy shared imports found.")

    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Report legacy root-level shared imports.")
    parser.add_argument(
        "--repo-root",
        default=str(REPO_ROOT),
        help="Repository root to scan.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit nonzero when any legacy shared imports are found.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of text.",
    )
    parser.add_argument(
        "--scope",
        choices=["all", "runtime", "tests", "executable", "docs"],
        default="all",
        help="Filter scope: all (default), runtime (production only), tests, executable (runtime+tests), docs",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    findings = scan(repo_root, scope=args.scope)

    if args.json:
        payload = {
            "repo_root": str(repo_root),
            "scope": args.scope,
            "finding_count": len(findings),
            "findings": [asdict(finding) for finding in findings],
        }
        print(json.dumps(payload, indent=2))
    else:
        print(_render_text(findings))

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    sys.exit(main())
