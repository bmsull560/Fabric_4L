#!/usr/bin/env python3
"""Comprehensive audit and fix of all pack variable references."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Allow importing sibling _lib without a package __init__.py
_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _lib import resolve_repo_root  # type: ignore[import-not-found]


def get_formula_variables(formula: dict[str, object]) -> set[str]:
    """Extract variable names from formula expression."""
    expression = formula.get("expression", {})
    if isinstance(expression, dict):
        return set(expression.get("variables", []))  # type: ignore[arg-type]
    return set()


def get_pack_prefix(pack_name: str, existing_variables: list[dict[str, object]]) -> str:
    """Derive pack prefix from existing variable IDs (e.g., 'ai-var-001' -> 'ai').

    Falls back to first two chars of pack name if no variables exist.
    """
    if existing_variables:
        first_var_id = existing_variables[0].get("variable_id", "")
        if isinstance(first_var_id, str) and "-var-" in first_var_id:
            return first_var_id.split("-var-")[0]
    return pack_name[:2].replace("-", "")


def _load_json(path: Path) -> dict[str, object]:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)  # type: ignore[no-any-return]


def _save_json(path: Path, data: dict[str, object]) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="repository root (default: auto-detected)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print changes without writing files",
    )
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve() if args.repo_root else resolve_repo_root()
    packs_dir = repo_root / "packs"
    manifest_path = packs_dir / "pack-manifest.json"

    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    manifest = _load_json(manifest_path)
    packs = manifest.get("packs", [])
    if not isinstance(packs, list):
        print("ERROR: manifest 'packs' is not a list", file=sys.stderr)
        return 1

    total_added = 0

    for pack in packs:
        if not isinstance(pack, dict):
            continue
        pack_id = pack.get("pack_id", "")
        pack_name = re.sub(r"-v\d+$", "", str(pack_id))
        pack_path = packs_dir / pack_name

        print(f"\n{'=' * 60}")
        print(f"Processing: {pack_id}")
        print("=" * 60)

        # Load variables
        variables_path = pack_path / "variables.json"
        if not variables_path.exists():
            print(f"  SKIP: {variables_path} not found")
            continue
        var_data = _load_json(variables_path)
        variables = var_data.get("variables", [])
        if not isinstance(variables, list):
            print(f"  ERROR: 'variables' is not a list in {variables_path}")
            continue

        # Load formulas
        formulas_path = pack_path / "formulas.json"
        if not formulas_path.exists():
            print(f"  SKIP: {formulas_path} not found")
            continue
        formula_data = _load_json(formulas_path)
        formulas = formula_data.get("formulas", [])
        if not isinstance(formulas, list):
            print(f"  ERROR: 'formulas' is not a list in {formulas_path}")
            continue

        # Validate: check for formula references to non-existent variables
        valid_formula_ids = {f["formula_id"] for f in formulas if isinstance(f, dict)}
        referenced_vars: set[str] = set()
        for formula in formulas:
            if not isinstance(formula, dict):
                continue
            refs = get_formula_variables(formula)
            expression = formula.get("expression", {})
            if isinstance(expression, dict):
                for ref_formula_id in expression.get("sub_formulas", []):
                    if ref_formula_id not in valid_formula_ids:
                        print(
                            f"  Formula '{formula.get('formula_id', '?')}' "
                            f"references non-existent sub-formula '{ref_formula_id}'"
                        )
            referenced_vars.update(refs)

        existing_vars = {v["variable_name"] for v in variables if isinstance(v, dict)}
        missing = referenced_vars - existing_vars

        if missing:
            print(f"Missing variables: {missing}")

            next_id = (
                max(
                    (
                        int(str(v["variable_id"]).split("-")[-1])
                        for v in variables
                        if isinstance(v, dict) and str(v.get("variable_id", "")).split("-")[-1].isdigit()
                    ),
                    default=0,
                )
                + 1
            )
            pack_prefix = get_pack_prefix(pack_name, variables)

            for var_name in missing:
                var: dict[str, object] = {
                    "variable_id": f"{pack_prefix}-var-{next_id:03d}",
                    "variable_name": var_name,
                    "display_name": var_name.replace("_", " "),
                    "description": f"Auto-generated variable for {var_name}",
                    "data_type": "CURRENCY",
                    "unit_of_measure": "USD",
                    "valid_range": {"min": 0, "max": 100000000},
                    "default_value": 1000000,
                    "source_type": "USER_INPUT",
                    "validation_rules": [{"type": "range", "min": 0, "max": 100000000}],
                    "tags": ["auto-generated"],
                    "used_in_formulas": [],
                    "canonicalName": var_name,
                    "name": var_name.replace("_", " "),
                }

                for formula in formulas:
                    if var_name in get_formula_variables(formula):
                        used = var.get("used_in_formulas", [])
                        if isinstance(used, list):
                            used.append(formula.get("formula_id", ""))

                variables.append(var)
                next_id += 1
                total_added += 1
                print(f"  Added: {var_name} ({var['variable_id']})")

            if not args.dry_run:
                _save_json(variables_path, var_data)
            pack["variable_count"] = len(variables)
            print(f"  Updated count: {pack['variable_count']} variables")
        else:
            print("All formula references valid")

    total_vars = sum(p.get("variable_count", 0) for p in packs if isinstance(p, dict))
    manifest["statistics"] = manifest.get("statistics", {})
    if isinstance(manifest["statistics"], dict):
        manifest["statistics"]["total_variables"] = total_vars

    if not args.dry_run:
        _save_json(manifest_path, manifest)

    print(f"\n{'=' * 60}")
    print(f"SUMMARY: Added {total_added} variables across all packs")
    print(f"Total variables in ecosystem: {total_vars}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
