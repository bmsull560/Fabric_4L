#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

FIELD_LABELS = (
    "Contract shape impact",
    "Tenant isolation impact",
    "Compatibility shim impact",
)

PLACEHOLDER_VALUES = {"", "tbd", "todo", "pending", "?", "<fill me in>"}


def parse_changed_files(payload: dict[str, object], env_changed: str) -> set[str]:
    pr = payload.get("pull_request") or {}
    changed = {
        str(path).strip()
        for path in pr.get("changed_files_list", [])  # type: ignore[union-attr]
        if str(path).strip()
    }
    if changed:
        return changed
    return {item.strip() for item in env_changed.split() if item.strip()}


def is_relevant_change(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if normalized.startswith("apps/web/"):
        return True
    if normalized.startswith("contracts/openapi/") or normalized.startswith("contracts/jsonschema/"):
        return True
    if normalized.startswith("services/") or normalized.startswith("value_fabric/"):
        return True
    return False


def extract_field_value(body: str, label: str) -> str | None:
    pattern = re.compile(rf"(?mi)^[-*]?\s*\*\*{re.escape(label)}:\*\*\s*(.+?)\s*$")
    match = pattern.search(body)
    if not match:
        return None
    return match.group(1).strip()


def validate_pr_body(body: str) -> list[str]:
    missing: list[str] = []
    for label in FIELD_LABELS:
        value = extract_field_value(body, label)
        if value is None:
            missing.append(f"missing field: {label}")
            continue
        if value.casefold() in PLACEHOLDER_VALUES:
            missing.append(f"placeholder value for field: {label}")
    return missing


def main() -> int:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        print("GITHUB_EVENT_PATH not set; skipping PR governance field check.")
        return 0

    payload = json.loads(Path(event_path).read_text(encoding="utf-8"))
    if "pull_request" not in payload:
        print("No pull_request payload found; skipping PR governance field check.")
        return 0

    changed_files = parse_changed_files(payload, os.environ.get("CHANGED_FILES", ""))
    relevant = sorted(path for path in changed_files if is_relevant_change(path))
    if not relevant:
        print("No backend/frontend/API file changes detected; skipping PR governance field check.")
        return 0

    body = str((payload.get("pull_request") or {}).get("body") or "")
    failures = validate_pr_body(body)
    if failures:
        print("ERROR: PR description is missing required governance impact fields for backend/frontend/API changes:")
        for failure in failures:
            print(f"- {failure}")
        print("Relevant changed files:")
        for path in relevant[:20]:
            print(f"- {path}")
        return 1

    print("PR governance impact fields present for backend/frontend/API changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
