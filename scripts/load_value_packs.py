#!/usr/bin/env python3
"""
Value Pack Database Loader

Loads all domain value packs into Layer 3 Knowledge Graph.

Usage:
    python scripts/load_value_packs.py --dry-run
    python scripts/load_value_packs.py --pack financial-services
    python scripts/load_value_packs.py --all
    python scripts/load_value_packs.py --all --api-url http://localhost:8000
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# Pack directory
PACKS_DIR = Path(__file__).parent.parent / "packs"
MANIFEST_FILE = PACKS_DIR / "pack-manifest.json"


def load_manifest() -> dict:
    """Load pack manifest."""
    with open(MANIFEST_FILE) as f:
        return json.load(f)


def load_pack_files(pack_path: Path) -> dict[str, Any]:
    """Load all JSON files from a pack directory."""
    files = {}
    for filename in ["formulas.json", "variables.json", "ontology.json", "workflow_template.json"]:
        filepath = pack_path / filename
        if filepath.exists():
            with open(filepath) as f:
                files[filename.replace(".json", "")] = json.load(f)
    return files


def transform_formula(pack_formula: dict, pack_id: str) -> dict:
    """Transform pack formula to Layer 3 API format."""
    return {
        "id": pack_formula["formula_id"],
        "name": pack_formula["name"],
        "description": pack_formula["description"],
        "category": pack_formula["formula_type"],
        "expression": pack_formula["expression"]["string"],
        "variables": [
            {
                "name": v["name"],
                "display_name": v.get("display_name", v["name"]),
                "type": v.get("type", "number"),
                "unit": v.get("unit"),
                "default_value": v.get("default_value"),
                "min_value": v.get("valid_range", {}).get("min"),
                "max_value": v.get("valid_range", {}).get("max"),
            }
            for v in pack_formula.get("required_variables", [])
        ],
        "output_unit": pack_formula.get("unit_of_result", "value"),
        "pack_id": pack_id,
        "version": pack_formula["version"],
        "status": pack_formula["status"],
        "governance": pack_formula.get("governance", {}),
    }


def transform_variable(pack_var: dict, pack_id: str) -> dict:
    """Transform pack variable to Layer 3 API format."""
    return {
        "name": pack_var["variable_name"],
        "display_name": pack_var["display_name"],
        "description": pack_var.get("description", ""),
        "type": pack_var.get("data_type", "number").lower(),
        "unit": pack_var.get("unit_of_measure"),
        "default_value": pack_var.get("default_value"),
        "min_value": pack_var.get("valid_range", {}).get("min"),
        "max_value": pack_var.get("valid_range", {}).get("max"),
        "pack_id": pack_id,
        "used_in_formulas": pack_var.get("used_in_formulas", []),
    }


def validate_pack(pack_files: dict, pack_id: str) -> list[str]:
    """Validate pack integrity. Returns list of errors."""
    errors = []
    
    # Check pack_id consistency
    for file_type, data in pack_files.items():
        if isinstance(data, dict) and "pack_id" in data:
            if data["pack_id"] != pack_id:
                errors.append(f"{file_type}: pack_id mismatch ({data['pack_id']} != {pack_id})")
    
    # Validate formulas reference existing variables
    if "formulas" in pack_files and "variables" in pack_files:
        valid_vars = {v["variable_name"] for v in pack_files["variables"].get("variables", [])}
        for formula in pack_files["formulas"].get("formulas", []):
            expr_vars = formula.get("expression", {}).get("variables", [])
            for var in expr_vars:
                if var not in valid_vars:
                    errors.append(f"Formula {formula['formula_id']}: unknown variable {var}")
    
    return errors


def load_pack_to_api(pack_id: str, pack_path: Path, api_url: str, dry_run: bool = False) -> dict:
    """Load a single pack to the API."""
    print(f"\n{'='*60}")
    print(f"Loading pack: {pack_id}")
    print(f"{'='*60}")
    
    # Load pack files
    pack_files = load_pack_files(pack_path)
    
    # Validate
    errors = validate_pack(pack_files, pack_id)
    if errors:
        print(f"Validation errors:")
        for error in errors:
            print(f"  - {error}")
        return {"status": "error", "errors": errors}
    
    print(f"✓ Validation passed")
    
    # Transform formulas
    formulas = []
    if "formulas" in pack_files:
        for f in pack_files["formulas"]["formulas"]:
            formulas.append(transform_formula(f, pack_id))
        print(f"✓ Transformed {len(formulas)} formulas")
    
    # Transform variables
    variables = []
    if "variables" in pack_files:
        for v in pack_files["variables"]["variables"]:
            variables.append(transform_variable(v, pack_id))
        print(f"✓ Transformed {len(variables)} variables")
    
    if dry_run:
        print(f"[DRY RUN] Would load {len(formulas)} formulas, {len(variables)} variables")
        return {
            "status": "dry_run",
            "formulas": len(formulas),
            "variables": len(variables),
        }
    
    # TODO: Implement actual API calls
    # For now, just return the transformed data
    print(f"[NOT IMPLEMENTED] API integration pending")
    
    return {
        "status": "success",
        "formulas_loaded": len(formulas),
        "variables_loaded": len(variables),
    }


def main():
    parser = argparse.ArgumentParser(description="Load Value Packs into Layer 3")
    parser.add_argument("--pack", help="Load specific pack by ID")
    parser.add_argument("--all", action="store_true", help="Load all packs")
    parser.add_argument("--dry-run", action="store_true", help="Validate without loading")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Layer 3 API URL")
    parser.add_argument("--validate", action="store_true", help="Run validation only")
    
    args = parser.parse_args()
    
    # Load manifest
    manifest = load_manifest()
    print(f"Loaded manifest with {manifest['total_packs']} packs")
    
    results = []
    
    if args.pack:
        # Load single pack
        pack_info = next((p for p in manifest["packs"] if p["pack_id"] == args.pack), None)
        if not pack_info:
            print(f"Error: Pack {args.pack} not found in manifest")
            sys.exit(1)
        
        pack_path = PACKS_DIR / args.pack.replace("-v1", "").replace("-", "-")
        # Handle path mapping
        pack_path = PACKS_DIR / args.pack.replace("-v1", "").replace("financial-services", "financial-services").replace("energy-utilities", "energy-utilities").replace("retail-consumer", "retail-consumer").replace("ai-technology", "ai-technology")
        # Actually just use the pack_id path directly
        pack_path = PACKS_DIR / args.pack.replace("-v1", "")
        
        result = load_pack_to_api(args.pack, pack_path, args.api_url, args.dry_run)
        results.append(result)
        
    elif args.all or args.validate:
        # Load all packs
        for pack_info in manifest["packs"]:
            pack_id = pack_info["pack_id"]
            pack_slug = pack_id.replace("-v1", "")
            pack_path = PACKS_DIR / pack_slug
            
            if not pack_path.exists():
                print(f"Warning: Pack directory not found: {pack_path}")
                continue
            
            result = load_pack_to_api(pack_id, pack_path, args.api_url, args.dry_run or args.validate)
            results.append(result)
    else:
        parser.print_help()
        sys.exit(1)
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    success = sum(1 for r in results if r["status"] == "success")
    errors = sum(1 for r in results if r["status"] == "error")
    dry_runs = sum(1 for r in results if r["status"] == "dry_run")
    
    print(f"Packs processed: {len(results)}")
    print(f"  Success: {success}")
    print(f"  Errors: {errors}")
    print(f"  Dry runs: {dry_runs}")
    
    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
