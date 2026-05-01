#!/usr/bin/env python3
"""
Frontend-Backend Contract Drift Detection Script

Run in CI to detect drift between frontend expectations and backend OpenAPI specs.

Usage:
    python scripts/check_frontend_backend_contracts.py \
        --frontend-contract docs/contracts/frontend-backend-contract-map.md \
        --openapi-dir contracts/openapi/

Exit codes:
    0 - No drift detected (or only orphans)
    1 - Drift detected (mismatched or missing endpoints)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class ContractEntry:
    frontend_module: str
    query_key: str
    backend_owner: str
    canonical_endpoint: str
    method: str
    status: str
    notes: str = ""


@dataclass
class OpenApiEndpoint:
    path: str
    method: str
    spec_file: str
    parameters: list[dict[str, Any]] = field(default_factory=list)
    responses: dict[str, Any] = field(default_factory=dict)


@dataclass
class DriftResult:
    matched: list[tuple[ContractEntry, OpenApiEndpoint]] = field(default_factory=list)
    mismatched: list[tuple[ContractEntry, str]] = field(default_factory=list)
    missing: list[ContractEntry] = field(default_factory=list)
    orphaned: list[OpenApiEndpoint] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Frontend contract parsing
# ---------------------------------------------------------------------------


def parse_contract_map(path: Path) -> list[ContractEntry]:
    """Parse the markdown contract map and extract endpoint rows."""
    entries: list[ContractEntry] = []
    text = path.read_text(encoding="utf-8")

    # Find all table rows that look like contract rows.
    # We look for lines starting with "| " that have enough columns.
    for line in text.splitlines():
        if not line.startswith("|"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts = [p for p in parts if p]
        # Expect at least 11 columns for the full contract table
        if len(parts) < 11:
            continue
        # Skip header rows and legend rows
        if parts[0] in ("Frontend Module", "Field", "Aspect", "Column", "UI Step", "Source", "Route Family"):
            continue
        if "---" in parts[0]:
            continue

        # Strip markdown backticks and bold markers from cells
        cleaned = [p.strip().strip("`").strip("*").strip() for p in parts]

        # Map columns by position (robust to minor formatting differences)
        # Column order: Frontend Module | Query Key | Backend Owner | Canonical Endpoint | HTTP Method | Request Params | Request Body Schema | Response Schema | Auth / Tenant | Current Status | Notes
        entries.append(
            ContractEntry(
                frontend_module=cleaned[0],
                query_key=cleaned[1] if len(cleaned) > 1 else "",
                backend_owner=cleaned[2] if len(cleaned) > 2 else "",
                canonical_endpoint=cleaned[3] if len(cleaned) > 3 else "",
                method=cleaned[4] if len(cleaned) > 4 else "",
                status=cleaned[9] if len(cleaned) > 9 else "unknown",
                notes=cleaned[10] if len(cleaned) > 10 else "",
            )
        )

    return entries


# ---------------------------------------------------------------------------
# OpenAPI spec loading
# ---------------------------------------------------------------------------


def load_openapi_specs(directory: Path) -> list[OpenApiEndpoint]:
    """Load all OpenAPI JSON specs and flatten into endpoint list."""
    endpoints: list[OpenApiEndpoint] = []
    if not directory.exists():
        print(f"[WARN] OpenAPI directory not found: {directory}")
        return endpoints

    for spec_file in sorted(directory.glob("*.json")):
        try:
            data = json.loads(spec_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[WARN] Failed to parse {spec_file}: {exc}")
            continue

        paths = data.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                method = method.upper()
                if method in ("PARAMETERS", "SUMMARY", "DESCRIPTION"):
                    continue
                parameters = details.get("parameters", []) if isinstance(details, dict) else []
                responses = details.get("responses", {}) if isinstance(details, dict) else {}
                endpoints.append(
                    OpenApiEndpoint(
                        path=path,
                        method=method,
                        spec_file=spec_file.name,
                        parameters=parameters,
                        responses=responses,
                    )
                )

    return endpoints


# ---------------------------------------------------------------------------
# Path matching logic
# ---------------------------------------------------------------------------


def normalize_path(path: str) -> str:
    """Strip host, query params, and trailing slashes for comparison."""
    path = path.split("?")[0]
    path = path.split("#")[0]
    path = path.rstrip("/")
    # Collapse multiple slashes
    path = re.sub(r"/+", "/", path)
    return path


def path_to_pattern(path: str) -> str:
    """Convert a path with {params} to a regex pattern."""
    # Escape literal segments, replace {param} with regex capture
    pattern = re.sub(r"\{[^}]+\}", r"[^/]+", path)
    return f"^{pattern}$"


def paths_match(frontend_path: str, backend_path: str) -> bool:
    """Check if a frontend path expectation matches a backend OpenAPI path."""
    fp = normalize_path(frontend_path)
    bp = normalize_path(backend_path)

    # Direct equality
    if fp == bp:
        return True

    # Try regex matching both directions
    try:
        if re.match(path_to_pattern(bp), fp):
            return True
        if re.match(path_to_pattern(fp), bp):
            return True
    except re.error:
        pass

    return False


def method_matches(expected: str, actual: str) -> bool:
    """Case-insensitive HTTP method comparison."""
    return expected.upper().strip() == actual.upper().strip()


# ---------------------------------------------------------------------------
# Alias resolution
# ---------------------------------------------------------------------------


def resolve_frontend_to_backend_path(frontend_path: str, layer: str) -> str | None:
    """
    Apply known gateway/proxy rewrite rules to translate a frontend path
    to the expected backend canonical path.
    """
    fp = normalize_path(frontend_path)

    # Known rewrite mappings based on vite.config.ts and gateway config
    rewrites: dict[str, list[tuple[str, str]]] = {
        "l1": [
            ("/api/v1/ingestion/", "/api/v1/ingestion/"),
            ("/api/v1/ingest/", "/api/v1/ingestion/"),
        ],
        "l2": [
            ("/api/v1/extract/", "/v1/"),
            ("/api/extract/", "/v1/"),
        ],
        "l3": [
            ("/api/v1/graph/", "/v1/"),
            ("/api/graph/", "/v1/"),
        ],
        "l4": [
            ("/api/v1/agents/", "/v1/"),
            ("/api/agents/", "/v1/"),
        ],
        "l5": [
            ("/api/v1/truths/", "/api/v1/"),
            ("/api/truths/", "/api/v1/"),
        ],
        "l6": [
            ("/api/v1/benchmarks/", "/v1/"),
            ("/api/benchmarks/", "/v1/"),
        ],
    }

    rules = rewrites.get(layer.lower(), [])
    for prefix, replacement in rules:
        if fp.startswith(prefix):
            resolved = replacement + fp[len(prefix):]
            return normalize_path(resolved)

    # If no rule matched, return as-is (may be already canonical)
    return fp


# ---------------------------------------------------------------------------
# Drift detection engine
# ---------------------------------------------------------------------------


def detect_drift(entries: list[ContractEntry], endpoints: list[OpenApiEndpoint]) -> DriftResult:
    result = DriftResult()
    used_backend: set[int] = set()

    for entry in entries:
        # Skip entries that are clearly not endpoint rows
        if not entry.canonical_endpoint or entry.canonical_endpoint in ("Canonical Endpoint", "—", "-"):
            continue
        if not entry.method or entry.method in ("HTTP Method", "—", "-"):
            continue

        layer = entry.backend_owner.lower().replace("l", "").strip()
        if not layer.isdigit():
            layer = ""

        resolved = resolve_frontend_to_backend_path(entry.canonical_endpoint, f"l{layer}")
        if resolved is None:
            resolved = normalize_path(entry.canonical_endpoint)

        matched = False
        candidates = [resolved, normalize_path(entry.canonical_endpoint)]
        for candidate in candidates:
            if matched:
                break
            for idx, ep in enumerate(endpoints):
                if paths_match(candidate, ep.path) and method_matches(entry.method, ep.method):
                    result.matched.append((entry, ep))
                    used_backend.add(idx)
                    matched = True
                    break

        if not matched:
            # Distinguish mismatch vs missing based on status annotation
            if "mismatch" in entry.status.lower() or entry.status.lower() == "broken":
                result.mismatched.append((entry, f"No backend match for {resolved} {entry.method}"))
            elif entry.status.lower() in ("missing", "stubbed"):
                result.missing.append(entry)
            else:
                # Default: treat unverified as potential mismatch
                result.mismatched.append((entry, f"No backend match for {resolved} {entry.method}"))

    # Orphans = backend endpoints with no frontend consumer
    for idx, ep in enumerate(endpoints):
        if idx not in used_backend:
            result.orphaned.append(ep)

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def print_report(result: DriftResult, fail_on_missing: bool = False) -> int:
    print("=" * 80)
    print("Frontend-Backend Contract Drift Report")
    print("=" * 80)
    print()

    print(f"  Matched:     {len(result.matched)}")
    print(f"  Mismatched:  {len(result.mismatched)}")
    print(f"  Missing:     {len(result.missing)}")
    print(f"  Orphaned:    {len(result.orphaned)}")
    print()

    if result.mismatched:
        print("-" * 80)
        print("MISMATCHED (frontend expects endpoint not found in backend specs)")
        print("-" * 80)
        for entry, reason in result.mismatched:
            print(f"  [{entry.backend_owner}] {entry.method} {entry.canonical_endpoint}")
            print(f"    Query Key: {entry.query_key}")
            print(f"    Reason:    {reason}")
            if entry.notes:
                print(f"    Notes:     {entry.notes}")
            print()

    if result.missing:
        print("-" * 80)
        print("MISSING (frontend expects endpoint explicitly marked missing/stubbed)")
        print("-" * 80)
        for entry in result.missing:
            print(f"  [{entry.backend_owner}] {entry.method} {entry.canonical_endpoint}")
            print(f"    Query Key: {entry.query_key}")
            print()

    if result.orphaned:
        print("-" * 80)
        print("ORPHANED (backend endpoints with no frontend consumer — informational)")
        print("-" * 80)
        # Show first 20 to avoid spam
        for ep in result.orphaned[:20]:
            print(f"  [{ep.spec_file}] {ep.method} {ep.path}")
        if len(result.orphaned) > 20:
            print(f"  ... and {len(result.orphaned) - 20} more")
        print()

    print("=" * 80)

    has_drift = bool(result.mismatched) or (fail_on_missing and bool(result.missing))
    if has_drift:
        print("RESULT: FAIL — drift detected")
        return 1

    print("RESULT: PASS — no drift detected")
    return 0


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------


def load_allowlist(path: Path) -> list[dict[str, Any]]:
    """Load drift allowlist from YAML file."""
    if not path.exists():
        return []
    if not YAML_AVAILABLE:
        print(f"[WARN] PyYAML not installed, cannot load allowlist: {path}")
        return []
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data.get("allowed_mismatches", []) if isinstance(data, dict) else []
    except Exception as exc:
        print(f"[WARN] Failed to load allowlist: {exc}")
        return []


def is_allowed_mismatch(entry: ContractEntry, allowlist: list[dict[str, Any]]) -> bool:
    """Check if a mismatched entry is in the allowlist."""
    entry_layer = entry.backend_owner.lower().strip()
    entry_path = entry.canonical_endpoint.strip()
    entry_method = entry.method.upper().strip()

    for rule in allowlist:
        rule_layer = str(rule.get("layer", "")).lower().strip()
        rule_path = str(rule.get("path", "")).strip()
        rule_method = str(rule.get("method", "")).upper().strip()

        # Match layer
        if rule_layer != "all" and rule_layer != entry_layer:
            continue

        # Match path (normalize)
        if normalize_path(rule_path) != normalize_path(entry_path):
            continue

        # Match method (optional)
        if rule_method and rule_method != entry_method:
            continue

        return True
    return False


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Detect drift between frontend contract map and backend OpenAPI specs")
    parser.add_argument(
        "--frontend-contract",
        type=Path,
        default=Path("docs/contracts/frontend-backend-contract-map.md"),
        help="Path to frontend-backend-contract-map.md",
    )
    parser.add_argument(
        "--openapi-dir",
        type=Path,
        default=Path("contracts/openapi"),
        help="Directory containing backend OpenAPI JSON specs",
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=Path("contracts/drift-allowlist.yaml"),
        help="Path to drift allowlist YAML file",
    )
    parser.add_argument(
        "--fail-on-missing",
        action="store_true",
        help="Treat 'missing' contract entries as failures (default: only mismatched are failures)",
    )
    args = parser.parse_args()

    if not args.frontend_contract.exists():
        print(f"[ERROR] Frontend contract file not found: {args.frontend_contract}")
        return 1

    entries = parse_contract_map(args.frontend_contract)
    endpoints = load_openapi_specs(args.openapi_dir)
    allowlist = load_allowlist(args.allowlist)

    print(f"Loaded {len(entries)} contract entries from {args.frontend_contract}")
    print(f"Loaded {len(endpoints)} backend endpoints from {args.openapi_dir}")
    if allowlist:
        print(f"Loaded {len(allowlist)} allowed mismatch rules from {args.allowlist}")
    print()

    result = detect_drift(entries, endpoints)

    # Filter allowed mismatches
    if allowlist:
        allowed: list[tuple[ContractEntry, str]] = []
        blocked: list[tuple[ContractEntry, str]] = []
        for entry, reason in result.mismatched:
            if is_allowed_mismatch(entry, allowlist):
                allowed.append((entry, reason))
            else:
                blocked.append((entry, reason))
        result.mismatched = blocked
        if allowed:
            print(f"[INFO] {len(allowed)} mismatched entries excluded by allowlist")
            print()

    return print_report(result, fail_on_missing=args.fail_on_missing)


if __name__ == "__main__":
    sys.exit(main())
