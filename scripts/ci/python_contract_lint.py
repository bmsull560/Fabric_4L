"""Python Contract Linter for Fabric_4L / Value Fabric.

Phase 3: Enforce Python-side architectural contracts (tenant_id misuse, raw DB connections, etc.)
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable, Pattern


@dataclass
class ContractFinding:
    contract_id: str
    severity: str  # critical, high, medium, low
    path: str
    line: int
    column: int
    message: str
    preferred_pattern: str
    snippet: str | None = None


@dataclass
class LintReport:
    repo_root: str
    files_scanned: int = 0
    findings: list[ContractFinding] = field(default_factory=list)
    exit_code: int = 0


@dataclass(frozen=True)
class RegexCheck:
    contract_id: str
    severity: str
    pattern: Pattern[str]
    description: str
    preferred_pattern: str


CONTRACT_CHECKS: dict[str, dict[str, Any]] = {
    "tenant_context": {
        "severity": "critical",
        "patterns": [
            (r"def\s+\w+.*\(\s*[^)]*tenant_id\s*:", "tenant_id function parameter"),
            (r"request\.headers\[[\x27\x22]x-tenant-id[\x27\x22]\]", "direct header access for tenant"),
            (r"request\.headers\.get\([\x27\x22]x-tenant-id[\x27\x22]", "direct header get for tenant"),
        ],
        "ast_patterns": [
            ("tenant_id", "Arg", "tenant_id parameter in function definition"),
        ],
        "preferred_pattern": "Use get_tenant_context() or middleware-resolved tenant",
    },
    "raw_db_connection": {
        "severity": "critical",
        "patterns": [
            (r"psycopg2\.connect", "psycopg2 direct connect"),
            (r"asyncpg\.connect", "asyncpg direct connect"),
            (r"pymysql\.connect", "pymysql direct connect"),
            (r"create_engine\s*\(", "create_engine outside approved modules"),
            (r"postgresql://[^\s\"']+", "hardcoded postgres URL"),
            (r"mysql://[^\s\"']+", "hardcoded mysql URL"),
        ],
        "preferred_pattern": "Use get_db_from_context() or approved database provider",
    },
    "secret_in_source": {
        "severity": "critical",
        "patterns": [
            (r"['\"]sk-[a-zA-Z0-9]{20,}['\"]", "OpenAI API key pattern"),
            (r"['\"]AKIA[0-9A-Z]{16}['\"]", "AWS access key pattern"),
            (r"['\"][0-9a-f]{32,}['\"].*secret", "hex secret near 'secret' keyword"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "hardcoded password"),
            (r"PASSWORD\s*=\s*['\"][^'\"]+['\"]", "hardcoded PASSWORD"),
            (r"SECRET\s*=\s*['\"][^'\"]+['\"]", "hardcoded SECRET"),
            (r"TOKEN\s*=\s*['\"][^'\"]{8,}['\"]", "hardcoded TOKEN"),
        ],
        "preferred_pattern": "Load from environment variables, ExternalSecrets, or Vault",
    },
    "tool_error_contract": {
        "severity": "high",
        "patterns": [
            (r"raise\s+\w+Error.*inside.*tool", "raise inside tool function"),
            (r"except\s+Exception\s*:\s*pass", "bare except with pass"),
        ],
        "ast_patterns": [
            ("raise", "Raise", "raise statement outside error handler"),
        ],
        "preferred_pattern": "Return ToolResult with status='error' and safe error message",
    },
    "security_todo": {
        "severity": "medium",
        "patterns": [
            (r"#\s*TODO.*auth", "TODO near auth"),
            (r"#\s*TODO.*tenant", "TODO near tenant"),
            (r"#\s*FIXME.*auth", "FIXME near auth"),
            (r"#\s*FIXME.*tenant", "FIXME near tenant"),
            (r"skip.*security.*check", "skip security check"),
            (r"bypass.*auth", "auth bypass"),
            (r"dev.*only.*auth", "dev-only auth"),
        ],
        "preferred_pattern": "Remove or track security-sensitive TODOs before production",
    },
}

REGEX_CHECKS: tuple[RegexCheck, ...] = tuple(
    RegexCheck(
        contract_id=contract_id,
        severity=str(config["severity"]),
        pattern=re.compile(pattern, re.IGNORECASE),
        description=description,
        preferred_pattern=str(config["preferred_pattern"]),
    )
    for contract_id, config in CONTRACT_CHECKS.items()
    for pattern, description in config.get("patterns", [])
)

SCAN_GLOBS = (
    "services/**/*.py",
    "shared/**/*.py",
    "tests/**/*.py",
)

SKIP_PATH_PARTS = frozenset(
    {
        "__pycache__",
        ".eggs",
        "dist",
        "build",
        ".tox",
        ".venv",
        "venv",
        "node_modules",
    }
)


def is_test_or_stub_file(file_path: Path) -> bool:
    """Check if file is a test or stub that might legitimately have certain patterns."""
    name = file_path.name.lower()
    return (
        "test_" in name
        or "_test.py" in name
        or name.startswith("test")
        or "stub" in name
        or "mock" in name
    )


def _is_false_positive(file_path: Path, contract_id: str, line: str) -> bool:
    line_lower = line.lower()
    if "example" in line_lower or "placeholder" in line_lower:
        return True
    if "CHANGE_ME" in line or "fake" in line_lower:
        return True
    if contract_id == "secret_in_source" and "test" in str(file_path).lower():
        return "test" in line_lower or "mock" in line_lower or "example" in line_lower
    return False


def check_file_with_regex(file_path: Path, content: str) -> list[ContractFinding]:
    """Check file using precompiled regex patterns with a single pass over lines."""
    findings: list[ContractFinding] = []

    for line_number, line in enumerate(content.splitlines(), start=1):
        code_part = line.split("#", 1)[0]
        if not code_part and not line.lstrip().startswith(('#', '"', "'")):
            continue

        for check in REGEX_CHECKS:
            match = check.pattern.search(code_part)
            if match is None:
                continue
            if _is_false_positive(file_path, check.contract_id, line):
                continue

            findings.append(
                ContractFinding(
                    contract_id=check.contract_id,
                    severity=check.severity,
                    path=str(file_path),
                    line=line_number,
                    column=match.start(),
                    message=f"Found: {check.description}",
                    preferred_pattern=check.preferred_pattern,
                    snippet=line.strip()[:100],
                )
            )

    return findings


def check_file_with_ast(file_path: Path, content: str) -> list[ContractFinding]:
    """Check file using AST analysis."""
    findings: list[ContractFinding] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return findings  # Skip files with syntax errors

    path_lower = str(file_path).lower()
    is_tool_or_agent = "tool" in path_lower or "agent" in path_lower

    for node in ast.walk(tree):
        # Check for tenant_id parameter
        if isinstance(node, ast.arg) and node.arg == "tenant_id":
            # Check if it's in a service/repository function
            findings.append(
                ContractFinding(
                    contract_id="tenant_context",
                    severity="critical",
                    path=str(file_path),
                    line=getattr(node, "lineno", 0),
                    column=getattr(node, "col_offset", 0),
                    message="tenant_id as function parameter - use get_tenant_context() instead",
                    preferred_pattern="Use get_tenant_context() or middleware-resolved tenant",
                )
            )

        # Check for raise statements in certain contexts
        if is_tool_or_agent and isinstance(node, ast.Raise):
            findings.append(
                ContractFinding(
                    contract_id="tool_error_contract",
                    severity="high",
                    path=str(file_path),
                    line=getattr(node, "lineno", 0),
                    column=getattr(node, "col_offset", 0),
                    message="raise statement in tool/agent code - return structured error instead",
                    preferred_pattern="Return ToolResult with status='error'",
                )
            )

    return findings


def should_scan_file(file_path: Path) -> bool:
    """Determine if a file should be scanned."""
    if file_path.suffix != ".py":
        return False

    path_parts = set(file_path.parts)
    if path_parts & SKIP_PATH_PARTS:
        return False

    return "migrations/versions" not in file_path.as_posix()


def _within_scan_scope(path: Path, repo_root: Path) -> bool:
    """Return True when a path belongs to the same roots used by full scans."""
    try:
        rel = path.relative_to(repo_root).as_posix()
    except ValueError:
        return False
    return rel.startswith(("services/", "shared/", "tests/"))


def _changed_python_files(repo_root: Path) -> list[Path]:
    """Return changed Python files from git when --changed-only is requested."""
    try:
        completed = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    files: list[Path] = []
    for raw_path in completed.stdout.splitlines():
        path = repo_root / raw_path
        if path.exists() and should_scan_file(path) and _within_scan_scope(path, repo_root):
            files.append(path)
    return sorted(set(files))


def _all_python_files(repo_root: Path) -> list[Path]:
    python_files: set[Path] = set()
    for pattern in SCAN_GLOBS:
        python_files.update(path for path in repo_root.glob(pattern) if should_scan_file(path))
    return sorted(python_files)


def _iter_scan_files(repo_root: Path, changed_only: bool) -> Iterable[Path]:
    if changed_only:
        return _changed_python_files(repo_root)
    return _all_python_files(repo_root)


def scan_repository(repo_root: Path, changed_only: bool = False) -> LintReport:
    """Scan repository for contract violations."""
    report = LintReport(repo_root=str(repo_root))

    for file_path in _iter_scan_files(repo_root, changed_only):
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        report.files_scanned += 1
        report.findings.extend(check_file_with_regex(file_path, content))
        report.findings.extend(check_file_with_ast(file_path, content))

    return report


def load_baseline(baseline_path: Path) -> set[str]:
    """Load baseline findings to ignore."""
    if not baseline_path.exists():
        return set()

    try:
        data = json.loads(baseline_path.read_text())
        return set(data.get("findings", []))
    except Exception:
        return set()


def filter_with_baseline(findings: list[ContractFinding], baseline: set[str]) -> list[ContractFinding]:
    """Filter out baseline findings."""
    filtered = []
    for finding in findings:
        key = f"{finding.path}:{finding.line}:{finding.contract_id}"
        if key not in baseline:
            filtered.append(finding)
    return filtered


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Python contract linter for Fabric_4L"
    )
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--strict", action="store_true", help="Fail on any critical/high")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--baseline", help="Path to baseline file")
    parser.add_argument("--changed-only", action="store_true", help="Only scan changed files")

    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()

    # Scan repository
    report = scan_repository(repo_root, args.changed_only)

    # Apply baseline if provided
    if args.baseline:
        baseline = load_baseline(Path(args.baseline))
        report.findings = filter_with_baseline(report.findings, baseline)

    # Determine exit code
    severity_counts = {
        severity: sum(1 for finding in report.findings if finding.severity == severity)
        for severity in ("critical", "high", "medium", "low")
    }
    report.exit_code = 1 if (args.strict and (severity_counts["critical"] or severity_counts["high"])) else 0

    # Output
    if args.json:
        print(
            json.dumps(
                {
                    "repo_root": report.repo_root,
                    "files_scanned": report.files_scanned,
                    "exit_code": report.exit_code,
                    "findings_by_severity": severity_counts,
                    "findings": [asdict(f) for f in report.findings],
                },
                indent=2,
            )
        )
    else:
        print(f"\n{'='*60}")
        print("PYTHON CONTRACT LINT REPORT")
        print(f"{'='*60}")
        print(f"Repository: {report.repo_root}")
        print(f"Files scanned: {report.files_scanned}")
        print(f"Total findings: {len(report.findings)}")

        # Severity breakdown
        for severity in ["critical", "high", "medium", "low"]:
            count = severity_counts[severity]
            if count > 0:
                print(f"  {severity.upper()}: {count}")

        print(f"Exit code: {report.exit_code}")
        print(f"{'='*60}\n")

        if report.findings:
            print("FINDINGS:\n")
            for finding in sorted(report.findings, key=lambda f: (f.severity, f.path)):
                print(f"[{finding.severity.upper()}] {finding.contract_id}")
                print(f"  File: {finding.path}:{finding.line}")
                print(f"  Message: {finding.message}")
                print(f"  Preferred: {finding.preferred_pattern}")
                if finding.snippet:
                    print(f"  Snippet: {finding.snippet}")
                print()

    return report.exit_code


if __name__ == "__main__":
    sys.exit(main())
