#!/usr/bin/env python3
"""Report internal imports that still use deprecated compatibility namespaces."""

from __future__ import annotations

import argparse
import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCAN_ROOTS = (Path("services"), Path("value_fabric"), Path("tests"), Path("scripts"))
DEPRECATED_PREFIXES = ("value_fabric.layer1_ingestion", "value_fabric.layer3_knowledge")
BASELINE_PATH = Path("docs/reference/deprecated-namespace-import-baseline.json")
ALLOWLIST = {
    Path("tests/ci/test_deprecated_namespace_imports.py"),
}


@dataclass(frozen=True)
class DeprecatedImport:
    path: str
    line: int
    statement: str
    deprecated_namespace: str


def _iter_python_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for root in SCAN_ROOTS:
        abs_root = repo_root / root
        if not abs_root.exists():
            continue
        for file_path in abs_root.rglob("*.py"):
            rel = file_path.relative_to(repo_root)
            if rel in ALLOWLIST:
                continue
            files.append(file_path)
    return sorted(files)


def _deprecated_target(name: str) -> str | None:
    for prefix in DEPRECATED_PREFIXES:
        if name == prefix or name.startswith(prefix + "."):
            return prefix
    return None


def _scan_file(file_path: Path, repo_root: Path) -> list[DeprecatedImport]:
    source = file_path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError:
        return []

    lines = source.splitlines()
    rel = str(file_path.relative_to(repo_root))
    findings: list[DeprecatedImport] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                prefix = _deprecated_target(alias.name)
                if prefix:
                    findings.append(DeprecatedImport(rel, node.lineno, lines[node.lineno - 1].strip(), prefix))
        elif isinstance(node, ast.ImportFrom) and node.module:
            prefix = _deprecated_target(node.module)
            if prefix:
                findings.append(DeprecatedImport(rel, node.lineno, lines[node.lineno - 1].strip(), prefix))

    return findings


def scan(repo_root: Path) -> list[DeprecatedImport]:
    findings: list[DeprecatedImport] = []
    for file_path in _iter_python_files(repo_root):
        findings.extend(_scan_file(file_path, repo_root))
    return sorted(findings, key=lambda x: (x.path, x.line, x.statement))


def _load_baseline(repo_root: Path, baseline_path: Path) -> set[tuple[str, int, str, str]]:
    abs_path = repo_root / baseline_path
    if not abs_path.exists():
        return set()
    payload = json.loads(abs_path.read_text(encoding="utf-8"))
    return {
        (
            str(item["path"]),
            int(item["line"]),
            str(item["statement"]),
            str(item["deprecated_namespace"]),
        )
        for item in payload
    }


def _subtract_baseline(
    findings: list[DeprecatedImport],
    baseline: set[tuple[str, int, str, str]],
) -> list[DeprecatedImport]:
    return [
        item
        for item in findings
        if (item.path, item.line, item.statement, item.deprecated_namespace) not in baseline
    ]


@dataclass(frozen=True)
class ShimViolation:
    path: str
    line: int
    category: str
    message: str


def _check_shim_violations(repo_root: Path) -> list[ShimViolation]:
    """Detect service wrappers containing non-trivial domain logic."""
    findings: list[ShimViolation] = []
    wrapper_root = repo_root / "services" / "layer3-knowledge" / "src"
    canonical_root = repo_root / "value_fabric" / "layer3"
    if not wrapper_root.exists() or not canonical_root.exists():
        return findings

    # Map canonical files to wrapper files by relative path
    canonical_files = {p.relative_to(canonical_root): p for p in canonical_root.rglob("*.py")}
    for wrapper_file in wrapper_root.rglob("*.py"):
        rel = wrapper_file.relative_to(wrapper_root)
        if rel not in canonical_files:
            continue
        canonical_file = canonical_files[rel]
        wrapper_src = wrapper_file.read_text(encoding="utf-8")
        canonical_src = canonical_file.read_text(encoding="utf-8")
        # If wrapper has more than just imports and re-exports, flag it
        wrapper_lines = [l for l in wrapper_src.splitlines() if l.strip() and not l.strip().startswith("#")]
        canonical_lines = [l for l in canonical_src.splitlines() if l.strip() and not l.strip().startswith("#")]
        # Simple heuristic: wrapper should be mostly imports/re-exports; if it has >30% of canonical's non-trivial lines, flag
        if len(wrapper_lines) > 5 and len(wrapper_lines) > len(canonical_lines) * 0.3:
            findings.append(ShimViolation(
                str(wrapper_file.relative_to(repo_root)), 1,
                "shim_contains_logic",
                f"wrapper file {rel} appears to contain duplicated domain logic (>30% of canonical size)"
            ))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--use-baseline", action="store_true")
    parser.add_argument("--baseline-path", default=str(BASELINE_PATH))
    parser.add_argument("--check-shims", action="store_true", help="Also check for shim logic violations")
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root).resolve()
    findings = scan(repo_root)
    if args.use_baseline:
        baseline = _load_baseline(repo_root, Path(args.baseline_path))
        findings = _subtract_baseline(findings, baseline)

    shim_findings = _check_shim_violations(repo_root) if args.check_shims else []

    if args.json:
        out = {
            "deprecated_imports": [asdict(item) for item in findings],
            "shim_violations": [asdict(item) for item in shim_findings],
        }
        print(json.dumps(out, indent=2))
    else:
        print(f"Deprecated namespace import findings: {len(findings)}")
        for f in findings:
            print(f"{f.path}:{f.line} :: {f.statement} [{f.deprecated_namespace}]")
        if shim_findings:
            print(f"Shim logic violations: {len(shim_findings)}")
            for f in shim_findings:
                print(f"{f.path}:{f.line} :: [{f.category}] {f.message}")

    has_issues = bool(findings) or bool(shim_findings)
    return 1 if args.strict and has_issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
