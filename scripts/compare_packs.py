#!/usr/bin/env python3
"""
Value Pack Comparison Tool

Compares formulas and variables across domain packs to identify:
- Shared formula categories
- Common variable patterns
- Divergent approaches
- Cross-pack opportunities

Usage:
    python scripts/compare_packs.py
    python scripts/compare_packs.py --category ROI
    python scripts/compare_packs.py --variable-template
"""

import argparse
import json
from collections import defaultdict
from pathlib import Path

PACKS_DIR = Path(__file__).parent.parent / "packs"
MANIFEST_FILE = PACKS_DIR / "pack-manifest.json"


def load_all_packs() -> dict:
    """Load all pack data."""
    with open(MANIFEST_FILE) as f:
        manifest = json.load(f)
    
    packs = {}
    for pack_info in manifest["packs"]:
        pack_id = pack_info["pack_id"]
        pack_slug = pack_id.replace("-v1", "")
        pack_path = PACKS_DIR / pack_slug
        
        if not pack_path.exists():
            continue
        
        pack_data = {"info": pack_info}
        
        # Load formulas
        formulas_file = pack_path / "formulas.json"
        if formulas_file.exists():
            with open(formulas_file) as f:
                pack_data["formulas"] = json.load(f)
        
        # Load variables
        variables_file = pack_path / "variables.json"
        if variables_file.exists():
            with open(variables_file) as f:
                pack_data["variables"] = json.load(f)
        
        packs[pack_id] = pack_data
    
    return packs


def compare_formulas_by_category(packs: dict) -> dict:
    """Group formulas by category across packs."""
    categories = defaultdict(list)
    
    for pack_id, pack_data in packs.items():
        if "formulas" not in pack_data:
            continue
        
        for formula in pack_data["formulas"].get("formulas", []):
            category = formula.get("formula_type", "Unknown")
            categories[category].append({
                "pack": pack_id,
                "formula_id": formula["formula_id"],
                "name": formula["name"],
                "status": formula.get("status", "unknown"),
            })
    
    return dict(categories)


def find_common_variables(packs: dict) -> dict:
    """Find variables that appear in multiple packs."""
    variable_packs = defaultdict(set)
    variable_details = {}
    
    for pack_id, pack_data in packs.items():
        if "variables" not in pack_data:
            continue
        
        for var in pack_data["variables"].get("variables", []):
            var_name = var["variable_name"]
            variable_packs[var_name].add(pack_id)
            
            if var_name not in variable_details:
                variable_details[var_name] = {
                    "display_name": var["display_name"],
                    "data_type": var.get("data_type"),
                    "unit": var.get("unit_of_measure"),
                }
    
    # Find variables in 3+ packs
    common = {
        var: {
            "packs": list(packs_set),
            "count": len(packs_set),
            "details": variable_details[var],
        }
        for var, packs_set in variable_packs.items()
        if len(packs_set) >= 3
    }
    
    return dict(sorted(common.items(), key=lambda x: x[1]["count"], reverse=True))


def compare_formula_patterns(packs: dict) -> dict:
    """Compare formula calculation patterns."""
    patterns = defaultdict(list)
    
    for pack_id, pack_data in packs.items():
        if "formulas" not in pack_data:
            continue
        
        for formula in pack_data["formulas"].get("formulas", []):
            expr = formula.get("expression", {}).get("string", "")
            formula_type = formula.get("formula_type", "Unknown")
            
            # Categorize by structure
            if "ROI" in formula_type or ("/" in expr and "* 100" in expr):
                pattern = "ROI_calculation"
            elif " - " in expr and (" + " in expr or expr.count(" - ") > 1):
                pattern = "Net_value"
            elif " * " in expr:
                pattern = "Multiplicative"
            else:
                pattern = "Other"
            
            patterns[pattern].append({
                "pack": pack_id,
                "formula_id": formula["formula_id"],
                "name": formula["name"],
            })
    
    return dict(patterns)


def generate_variable_template(packs: dict) -> dict:
    """Generate a standardized variable template from all packs."""
    all_vars = defaultdict(lambda: {"count": 0, "types": set(), "units": set(), "packs": []})
    
    for pack_id, pack_data in packs.items():
        if "variables" not in pack_data:
            continue
        
        for var in pack_data["variables"].get("variables", []):
            var_name = var["variable_name"]
            all_vars[var_name]["count"] += 1
            all_vars[var_name]["types"].add(var.get("data_type", "unknown"))
            all_vars[var_name]["units"].add(var.get("unit_of_measure", "unknown"))
            all_vars[var_name]["packs"].append(pack_id)
    
    # Create template for common variables
    template = {}
    for var_name, data in all_vars.items():
        if data["count"] >= 2:  # Variable appears in 2+ packs
            template[var_name] = {
                "standardized_name": var_name,
                "display_name": var_name.replace("_", " ").title(),
                "data_type": "CURRENCY" if "USD" in data["units"] else "NUMBER",
                "common_unit": list(data["units"])[0] if len(data["units"]) == 1 else "VARIES",
                "appears_in": data["packs"],
                "recommended_for_new_packs": data["count"] >= 4,
            }
    
    return template


def print_comparison_report(packs: dict, category_filter: str = None):
    """Print a formatted comparison report."""
    print("=" * 80)
    print("VALUE PACK COMPARISON REPORT")
    print("=" * 80)
    
    # Pack summary
    print(f"\n📦 PACKS ANALYZED ({len(packs)})")
    print("-" * 80)
    for pack_id, pack_data in packs.items():
        info = pack_data.get("info", {})
        formula_count = len(pack_data.get("formulas", {}).get("formulas", []))
        var_count = len(pack_data.get("variables", {}).get("variables", []))
        print(f"  {pack_id:30} | Formulas: {formula_count:2} | Variables: {var_count:2} | {info.get('industry', 'Unknown')}")
    
    # Formula categories
    print(f"\n📊 FORMULA CATEGORIES")
    print("-" * 80)
    categories = compare_formulas_by_category(packs)
    
    if category_filter:
        categories = {k: v for k, v in categories.items() if k == category_filter}
    
    for category, formulas in sorted(categories.items()):
        print(f"\n  {category} ({len(formulas)} formulas):")
        for f in sorted(formulas, key=lambda x: x["pack"])[:10]:  # Show first 10
            status_icon = "✓" if f["status"] == "active" else "○" if f["status"] == "draft" else "✗"
            print(f"    [{status_icon}] {f['pack']:30} | {f['formula_id']:15} | {f['name'][:40]}")
        if len(formulas) > 10:
            print(f"    ... and {len(formulas) - 10} more")
    
    # Common variables
    print(f"\n🔗 COMMON VARIABLES (appearing in 3+ packs)")
    print("-" * 80)
    common_vars = find_common_variables(packs)
    
    for var_name, data in list(common_vars.items())[:15]:
        print(f"  {var_name:35} | {data['count']} packs | {', '.join(data['packs'])[:50]}")
    
    if len(common_vars) > 15:
        print(f"\n  ... and {len(common_vars) - 15} more common variables")
    
    # Formula patterns
    print(f"\n🧮 FORMULA PATTERNS")
    print("-" * 80)
    patterns = compare_formula_patterns(packs)
    for pattern, formulas in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
        print(f"  {pattern:20} | {len(formulas):2} formulas")
    
    print("\n" + "=" * 80)


def main():
    parser = argparse.ArgumentParser(description="Compare Value Packs")
    parser.add_argument("--category", help="Filter by formula category")
    parser.add_argument("--variable-template", action="store_true", help="Generate variable template")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    # Load all packs
    packs = load_all_packs()
    
    if args.variable_template:
        template = generate_variable_template(packs)
        if args.json:
            print(json.dumps(template, indent=2))
        else:
            print("\n📋 STANDARDIZED VARIABLE TEMPLATE")
            print("=" * 80)
            for var_name, data in sorted(template.items()):
                rec = "⭐" if data["recommended_for_new_packs"] else "  "
                print(f"  {rec} {var_name:35} | {data['common_unit']:10} | {len(data['appears_in'])} packs")
    else:
        if args.json:
            # Output comparison data as JSON
            output = {
                "packs": list(packs.keys()),
                "categories": compare_formulas_by_category(packs),
                "common_variables": find_common_variables(packs),
                "patterns": compare_formula_patterns(packs),
            }
            print(json.dumps(output, indent=2))
        else:
            print_comparison_report(packs, args.category)


if __name__ == "__main__":
    main()
