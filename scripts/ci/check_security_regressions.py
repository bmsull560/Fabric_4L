#!/usr/bin/env python3
"""Security regression gate: fail if known vulnerable patterns reappear.

Checks for:
- debug_info leaked in exception responses
- infrastructure URIs (neo4j_uri) in health-check JSON
- fake health checks that claim healthy without I/O
- Redis KEYS in production code paths
- broad DeprecationWarning suppression in pytest configs
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SCAN_ROOTS = (
    REPO_ROOT / "value_fabric",
    REPO_ROOT / "services",
    REPO_ROOT / "tests",
    REPO_ROOT / "scripts",
)

SKIP_DIRS = {"__pycache__", ".venv", ".uv-cache-local", ".venv-verify", ".hypothesis", ".git", "node_modules", ".tmp-local", ".tox"}


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    category: str
    message: str


# ── Pattern definitions ──

# 1. Debug info leak: "debug_info" key in JSON response construction near exception handling
DEBUG_INFO_RE = re.compile(r'"debug_info"\s*:', re.IGNORECASE)

# 2. Infrastructure URI leak in health responses
# Match "uri": settings.neo4j_uri or similar in dependency/health JSON
INFRA_URI_RE = re.compile(r'"uri"\s*:\s*(?:settings\.neo4j_uri|settings\.[a-z_]*_uri)', re.IGNORECASE)

# 3. Fake health check: pattern that sets start_time, calculates response_time, but has no I/O between
# We look for start_time = time.time() followed by response_time = (time.time() - start_time) * 1000
# with no actual network call, db call, or subprocess in between.
FAKE_HEALTH_RE = re.compile(
    r"start_time\s*=\s*time\.time\(\)[\s\S]{0,400}?response_time\s*=\s*\(time\.time\(\)\s*-\s*start_time\)\s*\*\s*1000",
    re.DOTALL,
)

# 4. Redis KEYS usage (not SCAN)
REDIS_KEYS_RE = re.compile(r"redis_client\.keys\(")

# 5. Broad deprecation warning suppression in pytest configs
BROAD_DEPRECATION_RE = re.compile(
    r"ignore::(?:DeprecationWarning|PendingDeprecationWarning)\s*$",
    re.MULTILINE,
)

# Allowlist: patterns that are genuinely safe or test-only
ALLOWLIST: dict[str, set[tuple[str, int]]] = {
    # This script's own literal regex definitions trigger false positives
    "infra_uri_leak": {("scripts/ci/check_security_regressions.py", 0)},
    "fake_health_check": {("scripts/ci/check_security_regressions.py", 0)},
}


def _iter_source_files():
    import os
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            # Prune skip directories in-place
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for fname in filenames:
                if fname.endswith(".py") or fname.endswith(".ini"):
                    yield Path(dirpath) / fname


def _is_allowlisted(finding: Finding) -> bool:
    allowed = ALLOWLIST.get(finding.category, set())
    normalized_path = finding.path.replace("\\", "/")
    for path_sub, line in allowed:
        if path_sub in normalized_path and (line == 0 or line == finding.line):
            return True
    return False


def scan() -> list[Finding]:
    findings: list[Finding] = []

    for path in _iter_source_files():
        rel = str(path.relative_to(REPO_ROOT))
        source = path.read_text(encoding="utf-8", errors="ignore")
        lines = source.splitlines()

        if path.suffix == ".py":
            # Helper: skip matches inside regex literal definitions (r"..." or re.compile(...))
            def _in_regex_literal(pos: int) -> bool:
                line_start = source.rfind("\n", 0, pos)
                line_text = source[line_start + 1 : pos]
                return line_text.strip().startswith("r\"") or "re.compile(" in line_text

            # 1. debug_info leak
            for m in DEBUG_INFO_RE.finditer(source):
                line_num = source[: m.start()].count("\n") + 1
                if _in_regex_literal(m.start()):
                    continue
                context = "\n".join(lines[max(0, line_num - 5) : line_num + 2])
                if "except" in context or "error" in context.lower() or "JSONResponse" in context:
                    findings.append(Finding(rel, line_num, "debug_info_leak", "debug_info key in error response JSON construction"))

            # 2. infra URI leak
            for m in INFRA_URI_RE.finditer(source):
                line_num = source[: m.start()].count("\n") + 1
                if _in_regex_literal(m.start()):
                    continue
                findings.append(Finding(rel, line_num, "infra_uri_leak", "infrastructure URI exposed in JSON response details"))

            # 3. fake health check
            for m in FAKE_HEALTH_RE.finditer(source):
                snippet = m.group(0)
                if _in_regex_literal(m.start()):
                    continue
                io_markers = ("await ", "client.get", "httpx", "requests.", "driver", "session.run", "health_check")
                if not any(marker in snippet for marker in io_markers):
                    line_num = source[: m.start()].count("\n") + 1
                    findings.append(Finding(rel, line_num, "fake_health_check", "health check reports timing without actual I/O"))

            # 4. Redis KEYS
            for m in REDIS_KEYS_RE.finditer(source):
                line_num = source[: m.start()].count("\n") + 1
                if _in_regex_literal(m.start()):
                    continue
                if "/tests/" not in rel:
                    findings.append(Finding(rel, line_num, "redis_keys", "Redis KEYS usage detected; prefer SCAN for production"))

        elif path.suffix == ".ini":
            # 5. broad deprecation suppression
            for m in BROAD_DEPRECATION_RE.finditer(source):
                line_num = source[: m.start()].count("\n") + 1
                # Only flag if not already scoped to a specific module
                line_text = lines[line_num - 1] if line_num <= len(lines) else ""
                if ":" not in line_text.split("#")[0]:
                    findings.append(Finding(rel, line_num, "broad_deprecation_suppression", "blanket deprecation warning suppression in pytest config"))

    # Deduplicate
    seen = set()
    deduped = []
    for f in findings:
        key = (f.path, f.line, f.category, f.message)
        if key not in seen and not _is_allowlisted(f):
            seen.add(key)
            deduped.append(f)

    return deduped


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on any finding")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON")
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    args = parser.parse_args(argv)

    findings = scan()

    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        print(f"Security regression findings: {len(findings)}")
        for f in findings:
            print(f"  [{f.category}] {f.path}:{f.line} :: {f.message}")

    return 1 if args.strict and findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
