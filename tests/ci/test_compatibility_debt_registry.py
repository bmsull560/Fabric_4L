from __future__ import annotations

import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/governance/compatibility-debt-registry.md"
RUNTIME_MARKER_PATHS = [
    ROOT / "value_fabric",
    ROOT / "services",
    ROOT / "apps/web/src",
    ROOT / "sdk/python/src",
]
IGNORED_PARTS = {"/tests/", "/test_", "_test.", "/docs/", "/archive/", "/prototypes/"}


def _extract_registry_paths(text: str) -> set[str]:
    return {
        match.group(1)
        for match in re.finditer(r"`([^`]+)`", text)
        if any(token in match.group(1).lower() for token in ("legacy", "compat"))
    }


def _iter_runtime_marker_files() -> set[str]:
    paths: set[str] = set()
    for base in RUNTIME_MARKER_PATHS:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            rel = "/" + path.relative_to(ROOT).as_posix()
            if any(part in rel for part in IGNORED_PARTS):
                continue
            if "legacy" in rel.lower() or "compat" in rel.lower():
                paths.add(rel[1:])
    return paths


def test_registry_exists_and_has_monthly_review_metadata() -> None:
    text = REGISTRY.read_text(encoding="utf-8")

    last_match = re.search(r"\*\*Last reviewed:\*\*\s*(\d{4}-\d{2}-\d{2})", text)
    next_match = re.search(r"\*\*Next review due:\*\*\s*(\d{4}-\d{2}-\d{2})", text)

    assert last_match, "Registry must include a 'Last reviewed' date."
    assert next_match, "Registry must include a 'Next review due' date."

    last_reviewed = dt.date.fromisoformat(last_match.group(1))
    next_due = dt.date.fromisoformat(next_match.group(1))
    today = dt.date.today()

    assert next_due >= today, (
        f"Monthly prune is overdue. Next review due was {next_due.isoformat()}"
    )
    assert (next_due - last_reviewed).days <= 31, "Review cadence must be monthly (<=31 days)."


def test_runtime_compatibility_markers_have_registry_entries() -> None:
    text = REGISTRY.read_text(encoding="utf-8")
    documented = _extract_registry_paths(text)
    discovered = _iter_runtime_marker_files()

    missing = sorted(p for p in discovered if p not in documented)

    assert not missing, (
        "Found runtime legacy/compatibility marker paths without registry entries:\n"
        + "\n".join(missing)
    )
