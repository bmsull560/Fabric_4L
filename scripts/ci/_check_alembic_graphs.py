#!/usr/bin/env python3
"""Quick check: inspect Alembic revision graphs without running env.py."""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

SERVICES = {
    "layer1-ingestion": REPO_ROOT / "services" / "layer1-ingestion",
    "layer2-extraction": REPO_ROOT / "services" / "layer2-extraction",
    "layer4-agents": REPO_ROOT / "services" / "layer4-agents",
    "layer5-ground-truth": REPO_ROOT / "services" / "layer5-ground-truth",
}

REVISION_FIELDS = ("revision", "down_revision", "branch_labels", "depends_on")
RevisionValue = str | tuple[str, ...] | None


def _find_versions_dir(service_dir: Path) -> Path | None:
    candidates = [
        service_dir / "migrations" / "versions",
        service_dir / "src" / "layer5_ground_truth" / "migrations" / "versions",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _literal_string_or_collection(value: ast.AST) -> RevisionValue:
    if isinstance(value, ast.Constant):
        if isinstance(value.value, str):
            return value.value
        if value.value is None:
            return None
    if isinstance(value, (ast.Tuple, ast.List)):
        items: list[str] = []
        for elt in value.elts:
            if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                items.append(elt.value)
            else:
                return None
        return tuple(items)
    return None


def _normalize_collection(value: RevisionValue) -> RevisionValue:
    if value is None or isinstance(value, str):
        return value
    return tuple(value)


def _normalize_parent_refs(value: RevisionValue) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return tuple(value)


def _format_fields(fields: dict[str, RevisionValue]) -> str:
    return ", ".join(f"{field}={fields[field]!r}" for field in REVISION_FIELDS)


def _extract_revision_entries(versions_dir: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []

    for file_path in sorted(versions_dir.glob("*.py")):
        if file_path.name.startswith(("__", ".")):
            continue

        source = file_path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        parsed_fields: dict[str, RevisionValue] = {field: None for field in REVISION_FIELDS}

        for node in tree.body:
            target_name = None
            value_node = None
            if isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    target_name = node.targets[0].id
                    value_node = node.value
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                target_name = node.target.id
                value_node = node.value

            if target_name in parsed_fields and value_node is not None:
                parsed_fields[target_name] = _normalize_collection(_literal_string_or_collection(value_node))

        revision = parsed_fields["revision"]
        if isinstance(revision, str):
            entries.append(
                {
                    "revision": revision,
                    "file": file_path.name,
                    "down_revision": _normalize_parent_refs(parsed_fields["down_revision"]),
                    "branch_labels": parsed_fields["branch_labels"],
                    "depends_on": parsed_fields["depends_on"],
                    "parsed_fields": parsed_fields,
                }
            )

    return entries


def _extract_revisions(versions_dir: Path) -> tuple[dict[str, dict], dict[str, list[str]]]:
    revisions: dict[str, dict] = {}
    revision_files: dict[str, list[str]] = {}

    for entry in _extract_revision_entries(versions_dir):
        revision = entry["revision"]
        revision_files.setdefault(revision, []).append(entry["file"])
        revisions[revision] = {
            "file": entry["file"],
            "down_revision": entry["down_revision"],
            "branch_labels": entry["branch_labels"],
            "depends_on": entry["depends_on"],
            "parsed_fields": entry["parsed_fields"],
        }

    return revisions, revision_files


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    for name, service_dir in SERVICES.items():
        versions_dir = _find_versions_dir(service_dir)
        if not versions_dir:
            errors.append(f"{name}: no versions directory found")
            continue

        revision_entries = _extract_revision_entries(versions_dir)
        revisions: dict[str, dict] = {}
        revision_files: dict[str, list[str]] = {}
        revision_entries_by_id: dict[str, list[dict[str, Any]]] = {}
        for entry in revision_entries:
            revision = entry["revision"]
            revision_files.setdefault(revision, []).append(entry["file"])
            revision_entries_by_id.setdefault(revision, []).append(entry)
            revisions[revision] = {
                "file": entry["file"],
                "down_revision": entry["down_revision"],
                "branch_labels": entry["branch_labels"],
                "depends_on": entry["depends_on"],
                "parsed_fields": entry["parsed_fields"],
            }
        if not revisions:
            warnings.append(f"{name}: no migration revisions found")
            continue

        children: dict[str, list[str]] = {}
        for revision, info in revisions.items():
            for parent in info["down_revision"]:
                children.setdefault(parent, []).append(revision)

        heads = [revision for revision in revisions if revision not in children]
        roots = [revision for revision, info in revisions.items() if not info["down_revision"]]

        print(f"\n{name}: {len(revisions)} revisions, {len(heads)} head(s), {len(roots)} root(s)")
        for revision in heads:
            print(f"  HEAD: {revision} ({revisions[revision]['file']})")
        for revision in roots:
            print(f"  ROOT: {revision} ({revisions[revision]['file']})")

        if len(heads) > 1:
            head_diagnostics = "; ".join(
                f"{revision} [{revisions[revision]['file']}: {_format_fields(revisions[revision]['parsed_fields'])}]"
                for revision in heads
            )
            errors.append(f"{name}: MULTI-HEAD detected ({len(heads)} heads: {heads}) :: {head_diagnostics}")

        for revision, files in revision_files.items():
            if len(files) > 1:
                duplicate_diagnostics = "; ".join(
                    f"{entry['file']}: {_format_fields(entry['parsed_fields'])}"
                    for entry in revision_entries_by_id[revision]
                )
                errors.append(
                    f"{name}: DUPLICATE revision ID '{revision}' in files: {files} :: {duplicate_diagnostics}"
                )

        for revision, info in revisions.items():
            parsed = info["parsed_fields"]
            if parsed["down_revision"] is not None and not info["down_revision"]:
                warnings.append(
                    f"{name}: parsed metadata for {info['file']} "
                    f"(revision={revision}, down_revision={parsed['down_revision']}, "
                    f"branch_labels={parsed['branch_labels']}, depends_on={parsed['depends_on']})"
                )

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"  - {warning}")

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("\nAll Alembic revision graphs are clean.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
