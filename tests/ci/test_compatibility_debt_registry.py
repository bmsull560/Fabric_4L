from __future__ import annotations

import datetime as dt
import re
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs/governance/compatibility-debt-registry.md"
RUNTIME_MARKER_PATHS = [
    ROOT / "value_fabric",
    ROOT / "services",
    ROOT / "apps/web/src",
    ROOT / "sdk/python/src",
]
IGNORED_PARTS = {"/tests/", "/test_", "_test.", "/docs/", "/archive/", "/prototypes/"}
IGNORED_DIR_MARKERS = ("/.venv/", "/site-packages/", "/__pycache__/", "/governance/")
IGNORED_SUFFIXES = (".pyc",)

MODULE_PATH = ROOT / "scripts" / "ci" / "compatibility_registry.py"
SPEC = spec_from_file_location("compatibility_registry", MODULE_PATH)
compatibility_registry = module_from_spec(SPEC)
sys.modules[SPEC.name] = compatibility_registry
assert SPEC.loader is not None
SPEC.loader.exec_module(compatibility_registry)


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
            if any(marker in rel for marker in IGNORED_DIR_MARKERS):
                continue
            if rel.endswith(IGNORED_SUFFIXES):
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


def test_registry_entries_include_owner_review_metadata_and_removal_ticket() -> None:
    entries = compatibility_registry.parse_registry(REGISTRY)
    assert entries, "Compatibility registry must contain at least one tracked entry."

    for entry in entries:
        assert entry.owner, f"{entry.shim_id} must include an owner."
        assert entry.target_removal_date, f"{entry.shim_id} must include a target removal date."
        assert entry.review_metadata, f"{entry.shim_id} must include review metadata."
        assert compatibility_registry.has_platform_architecture_approval(entry.review_metadata), (
            f"{entry.shim_id} review metadata must include Platform Architecture approval and an ISO date."
        )
        assert entry.removal_ticket, f"{entry.shim_id} must include a post-launch removal ticket."


def test_runtime_compatibility_markers_have_registry_entries() -> None:
    text = REGISTRY.read_text(encoding="utf-8")
    documented = compatibility_registry.parse_registry(REGISTRY)
    discovered = _iter_runtime_marker_files()

    missing = sorted(
        p for p in discovered
        if p not in _extract_registry_paths(text)
        and not compatibility_registry.path_is_covered(p, documented)
    )

    assert not missing, (
        "Found runtime legacy/compatibility marker paths without registry entries:\n"
        + "\n".join(missing)
    )


def test_registry_target_removal_dates_not_exceeded_without_extension_note() -> None:
    today = dt.date.today()
    overdue: list[str] = []

    text = REGISTRY.read_text(encoding="utf-8")
    for entry in compatibility_registry.parse_registry(REGISTRY):
        shim_id = entry.shim_id
        target = dt.date.fromisoformat(entry.target_removal_date)
        if target >= today:
            continue
        extension_ok = bool(re.search(rf"{re.escape(shim_id)}.*extension", text, flags=re.IGNORECASE))
        if not extension_ok:
            overdue.append(f"{shim_id} (target {target.isoformat()})")

    assert not overdue, (
        "Compatibility shim target removal date exceeded without documented extension note:\n"
        + "\n".join(overdue)
    )
