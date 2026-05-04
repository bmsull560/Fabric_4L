#!/usr/bin/env python3
"""CI gate script to check for overdue deprecations.

Fails when any target_removal date has passed unless
DEPRECATION_ALLOW_OVERDUE=true is set.

Usage:
    python3 scripts/ci/check_deprecations.py
    DEPRECATION_ALLOW_OVERDUE=true python3 scripts/ci/check_deprecations.py
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_deprecation_register(path: Path) -> dict:
    """Load and validate the deprecation register."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _register_items(register: dict) -> list[dict]:
    """Return deprecation items from either legacy or governance register shape."""
    items = register.get("items")
    if isinstance(items, list):
        return items
    deprecations = register.get("deprecations")
    if isinstance(deprecations, list):
        return deprecations
    return []


def _target_removal(item: dict) -> str | None:
    """Return target-removal date from either camelCase or snake_case field names."""
    value = item.get("targetRemoval") or item.get("target_removal")
    return str(value) if value else None


def check_deprecations(register: dict) -> tuple[list[dict], list[dict]]:
    """Check for overdue and upcoming deprecations.

    Returns:
        Tuple of (overdue_items, upcoming_items)
    """
    now = datetime.now(timezone.utc)
    overdue = []
    upcoming = []

    for item in _register_items(register):
        target_removal = _target_removal(item)
        if not target_removal:
            continue

        try:
            removal_date = datetime.fromisoformat(target_removal.replace("Z", "+00:00"))
            if removal_date.tzinfo is None:
                removal_date = removal_date.replace(tzinfo=timezone.utc)
        except ValueError:
            print(f"Warning: Invalid date format for {item.get('feature') or item.get('pattern') or item.get('id', 'unknown')}: {target_removal}")
            continue

        if removal_date <= now:
            overdue.append(item)
        else:
            days_until = (removal_date - now).days
            if days_until <= 30:
                upcoming.append({**item, "days_until_removal": days_until})

    return overdue, upcoming


def format_item(item: dict) -> str:
    """Format a deprecation item for display."""
    name = item.get("feature") or item.get("pattern") or item.get("id", "unknown")
    path = item.get("path") or ", ".join(item.get("blockedPaths", [])) or "N/A"
    introduced = item.get("deprecated_since") or item.get("introduced", "N/A")
    target_removal = _target_removal(item) or "N/A"
    return (
        f"  - {name}\n"
        f"    Path: {path}\n"
        f"    Deprecated since: {introduced}\n"
        f"    Target removal: {target_removal}\n"
        f"    Owner: {item.get('owner', 'N/A')}"
    )


def main() -> int:
    """Main entry point. Returns exit code."""
    repo_root = Path(__file__).parent.parent.parent
    candidate_paths = [
        repo_root / "docs" / "governance" / "deprecations.json",
        repo_root / "docs" / "deprecation_register.json",
    ]
    register_path = next((path for path in candidate_paths if path.exists()), None)

    if register_path is None:
        rendered_paths = ", ".join(str(path) for path in candidate_paths)
        print(f"Error: Deprecation register not found at any canonical path: {rendered_paths}")
        return 1

    try:
        register = load_deprecation_register(register_path)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in deprecation register: {e}")
        return 1

    overdue, upcoming = check_deprecations(register)

    # Print summary
    print("Deprecation Check")
    print("=" * 50)
    print(f"Register: {register_path}")
    print(f"Total deprecations: {len(_register_items(register))}")
    print(f"Overdue: {len(overdue)}")
    print(f"Upcoming (≤30 days): {len(upcoming)}")
    print()

    # Print upcoming items (informational)
    if upcoming:
        print("Upcoming Removals (≤30 days):")
        for item in upcoming:
            print(format_item(item))
            print(f"    Days until removal: {item['days_until_removal']}")
            print()

    # Handle overdue items
    if overdue:
        allow_overdue = os.environ.get("DEPRECATION_ALLOW_OVERDUE", "").lower() in (
            "true",
            "1",
            "yes",
        )

        print("Overdue Deprecations:")
        for item in overdue:
            print(format_item(item))
            print()

        if allow_overdue:
            print("Warning: Overdue deprecations detected but allowed via DEPRECATION_ALLOW_OVERDUE")
            print()
            # Still exit 0 but with warning
            return 0
        else:
            print("Error: Overdue deprecations detected. Either:")
            print("  1. Remove the deprecated feature")
            print("  2. Extend the target_removal date")
            print("  3. Set DEPRECATION_ALLOW_OVERDUE=true to bypass (not recommended)")
            return 1

    print("All deprecation checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
