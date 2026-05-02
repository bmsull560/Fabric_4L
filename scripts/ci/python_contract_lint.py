"""Python Contract Linter for Fabric_4L / Value Fabric.

Phase 3: Enforce Python-side architectural contracts (tenant_id misuse, raw DB connections, etc.)
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


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


CONTRACT_CHECKS = {
    "tenant_context": {
        "severity": "critical",
        "patterns": [
            (r"def\s+\w+.*\(\s*[^)]*tenant_id\s*:", "tenant_id function parameter"),
            (r'request\.headers\[[\'"]x-tenant-id[\'"]\]', "direct header access for tenant"),
            (r"request\.headers\.get\([\'"]x-tenant-id[\'"]", "direct header get for tenant"),
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


def is_test_or_stub_file(file_path: Path) -> bool:
    """Check if file is a test or stub that might legitimately have certain patterns."""
    name = file_path.name.lower()
    return (
        "test_" in name or
        "_test.py" in name or
        name.startswith("test") or
        "stub" in name or
        "mock" in name
    )


def check_file_with_regex(file_path: Path, content: str) -> list[ContractFinding]:
    """Check file using regex patterns."""
    findings = []
    lines = content.split("\n")

    for contract_id, config in CONTRACT_CHECKS.items():
        patterns = config.get("patterns", [])

        for pattern, description in patterns:
            for i, line in enumerate(lines, start=1):
                # Skip comments and strings that contain patterns
                code_part = line.split("#")[0]  # Remove comments

                if re.search(pattern, code_part, re.IGNORECASE):
                    # Skip some false positives
                    if "example" in line.lower() or "placeholder" in line.lower():
                        continue
                    if "CHANGE_ME" in line or "fake" in line.lower():
                        continue
                    if contract_id == "secret_in_source" and "test" in str(file_path).lower():
                        # Allow test fixtures to have fake secrets
                        if "test" in line.lower() or "mock" in line.lower() or "example" in line.lower():
                            continue

                    findings.append(ContractFinding(
                        contract_id=contract_id,
                        severity=config["severity"],
                        path=str(file_path),
                        line=i,
                        column=line.find(re.search(pattern, code_part).group()) if re.search(pattern, code_part) else 0,
                        message=f"Found: {description}",
                        preferred_pattern=config["preferred_pattern"],
                        snippet=line.strip()[:100],
                    ))

    return findings


def check_file_with_ast(file_path: Path, content: str) -> list[ContractFinding]:
    """Check file using AST analysis."""
    findings = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return findings  # Skip files with syntax errors

    for node in ast.walk(tree):
        # Check for tenant_id parameter
        if isinstance(node, ast.arg) and node.arg == "tenant_id":
            # Check if it's in a service/repository function
            findings.append(ContractFinding(
                contract_id="tenant_context",
                severity="critical",
                path=str(file_path),
                line=getattr(node, "lineno", 0),
                column=getattr(node, "col_offset", 0),
                message="tenant_id as function parameter - use get_tenant_context() instead",
                preferred_pattern="Use get_tenant_context() or middleware-resolved tenant",
            ))

        # Check for raise statements in certain contexts
        if isinstance(node, ast.Raise):
            # Check if we're in a tool-related file
            if "tool" in str(file_path).lower() or "agent" in str(file_path).lower():
                findings.append(ContractFinding(
                    contract_id="tool_error_contract",
                    severity="high",
                    path=str(file_path),
                    line=getattr(node, "lineno", 0),
                    column=getattr(node, "col_offset", 0),
                    message="raise statement in tool/agent code - return structured error instead",
                    preferred_pattern="Return ToolResult with status='error'",
                ))

    return findings


def should_scan_file(file_path: Path) -> bool:
    """Determine if a file should be scanned."""
    if not file_path.suffix == ".py":
        return False

    # Skip generated files
    skip_patterns = [
        "__pycache__",
        ".eggs",
        "dist",
        "build",
        ".tox",
        ".venv",
        "venv",
        "node_modules",
        "migrations/versions",  # Alembic migrations
    ]

    for pattern in skip_patterns:
        if pattern in str(file_path):
            return False

    return True


def scan_repository(repo_root: Path, changed_only: bool = False) -> LintReport:
    """Scan repository for contract violations."""
    report = LintReport(repo_root=str(repo_root))

    if changed_only:
        # TODO: Implement git diff scanning
        pass

    # Find all Python files
    python_files = []
    for pattern in [
        "value-fabric/**/*.py",
        "shared/**/*.py",
        "tests/**/*.py",
    ]:
        python_files.extend(repo_root.glob(pattern))

    for file_path in python_files:
        if not should_scan_file(file_path):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        report.files_scanned += 1

        # Run checks
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


def main():
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
    critical_high = [f for f in report.findings if f.severity in ("critical", "high")]
    report.exit_code = 1 if (args.strict and critical_high) else 0

    # Output
    if args.json:
        print(json.dumps({
            "repo_root": report.repo_root,
            "files_scanned": report.files_scanned,
            "exit_code": report.exit_code,
            "findings_by_severity": {
                "critical": len([f for f in report.findings if f.severity == "critical"]),
                "high": len([f for f in report.findings if f.severity == "high"]),
                "medium": len([f for f in report.findings if f.severity == "medium"]),
                "low": len([f for f in report.findings if f.severity == "low"]),
            },
            "findings": [asdict(f) for f in report.findings],
        }, indent=2))
    else:
        print(f"\n{'='*60}")
        print("PYTHON CONTRACT LINT REPORT")
        print(f"{'='*60}")
        print(f"Repository: {report.repo_root}")
        print(f"Files scanned: {report.files_scanned}")
        print(f"Total findings: {len(report.findings)}")

        # Severity breakdown
        for severity in ["critical", "high", "medium", "low"]:
            count = len([f for f in report.findings if f.severity == severity])
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
