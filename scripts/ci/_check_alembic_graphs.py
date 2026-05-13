#!/usr/bin/env python3
"""Quick check: inspect Alembic revision graphs without running env.py."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

SERVICES = {
    "layer1-ingestion": REPO_ROOT / "services" / "layer1-ingestion",
    "layer2-extraction": REPO_ROOT / "services" / "layer2-extraction",
    "layer4-agents": REPO_ROOT / "services" / "layer4-agents",
    "layer5-ground-truth": REPO_ROOT / "services" / "layer5-ground-truth",
}


def _find_versions_dir(service_dir: Path) -> Path | None:
    candidates = [
        service_dir / "migrations" / "versions",
        service_dir / "src" / "layer5_ground_truth" / "migrations" / "versions",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _literal_string_or_collection(value: ast.AST) -> str | tuple[str, ...] | None:
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


def _normalize_parent_refs(value: str | tuple[str, ...] | None) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    return value


def _extract_revisions(versions_dir: Path) -> tuple[dict[str, dict], dict[str, list[str]]]:
    revisions: dict[str, dict] = {}
    revision_files: dict[str, list[str]] = {}

    for file_path in sorted(versions_dir.glob("*.py")):
        if file_path.name.startswith(("__", ".")):
            continue

        source = file_path.read_text(encoding="utf-8", errors="ignore")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue

        parsed_fields: dict[str, str | tuple[str, ...] | None] = {
            "revision": None,
            "down_revision": None,
            "branch_labels": None,
            "depends_on": None,
        }

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
                parsed_fields[target_name] = _literal_string_or_collection(value_node)

        revision = parsed_fields["revision"]
        if isinstance(revision, str):
            revision_files.setdefault(revision, []).append(file_path.name)
            revisions[revision] = {
                "file": file_path.name,
                "down_revision": _normalize_parent_refs(parsed_fields["down_revision"]),
                "branch_labels": parsed_fields["branch_labels"],
                "depends_on": parsed_fields["depends_on"],
                "parsed_fields": parsed_fields,
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

        revisions, revision_files = _extract_revisions(versions_dir)
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
            errors.append(f"{name}: MULTI-HEAD detected ({len(heads)} heads: {heads})")

        for revision, files in revision_files.items():
            if len(files) > 1:
                errors.append(f"{name}: DUPLICATE revision ID '{revision}' in files: {files}")

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
