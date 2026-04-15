"""Value Pack Loader for Layer 3 API.

Loads domain value packs from JSON files into the formula registry.
"""

import json
from pathlib import Path
from typing import Any

# Pack directory relative to project root
PACKS_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "packs"
MANIFEST_FILE = PACKS_DIR / "pack-manifest.json"


def load_pack_manifest() -> dict[str, Any] | None:
    """Load pack manifest if available."""
    if not MANIFEST_FILE.exists():
        return None
    
    with open(MANIFEST_FILE) as f:
        return json.load(f)


def load_pack_formulas(pack_id: str) -> list[dict]:
    """Load formulas from a specific pack.
    
    Args:
        pack_id: Pack identifier (e.g., 'financial-services-v1')
        
    Returns:
        List of formula definitions in Layer 3 format
    """
    pack_slug = pack_id.replace("-v1", "")
    formulas_file = PACKS_DIR / pack_slug / "formulas.json"
    
    if not formulas_file.exists():
        return []
    
    with open(formulas_file) as f:
        data = json.load(f)
    
    formulas = []
    for f in data.get("formulas", []):
        # Transform to Layer 3 format
        formula = {
            "id": f["formula_id"],
            "name": f["name"],
            "description": f["description"],
            "category": f["formula_type"],
            "expression": f.get("expression", {}).get("string", ""),
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
                for v in f.get("required_variables", [])
            ],
            "output_unit": f.get("unit_of_result", "value"),
            "pack_id": pack_id,
            "version": f["version"],
            "status": f["status"],
            "governance": f.get("governance", {}),
        }
        formulas.append(formula)
    
    return formulas


def load_pack_variables(pack_id: str) -> list[dict]:
    """Load variables from a specific pack.
    
    Args:
        pack_id: Pack identifier (e.g., 'financial-services-v1')
        
    Returns:
        List of variable definitions in Layer 3 format
    """
    pack_slug = pack_id.replace("-v1", "")
    variables_file = PACKS_DIR / pack_slug / "variables.json"
    
    if not variables_file.exists():
        return []
    
    with open(variables_file) as f:
        data = json.load(f)
    
    variables = []
    for v in data.get("variables", []):
        variable = {
            "name": v["variable_name"],
            "display_name": v["display_name"],
            "description": v.get("description", ""),
            "type": v.get("data_type", "number").lower(),
            "unit": v.get("unit_of_measure"),
            "default_value": v.get("default_value"),
            "min_value": v.get("valid_range", {}).get("min"),
            "max_value": v.get("valid_range", {}).get("max"),
            "pack_id": pack_id,
            "used_in_formulas": v.get("used_in_formulas", []),
        }
        variables.append(variable)
    
    return variables


def get_available_packs() -> list[dict]:
    """Get list of available value packs.
    
    Returns:
        List of pack metadata dictionaries
    """
    manifest = load_pack_manifest()
    if not manifest:
        return []
    
    return [
        {
            "pack_id": p["pack_id"],
            "name": p["name"],
            "industry": p["industry"],
            "description": p["description"],
            "formula_count": p["formula_count"],
            "variable_count": p["variable_count"],
        }
        for p in manifest.get("packs", [])
    ]


def load_all_pack_formulas() -> list[dict]:
    """Load formulas from all available packs.
    
    Returns:
        Combined list of all pack formulas
    """
    all_formulas = []
    
    manifest = load_pack_manifest()
    if not manifest:
        return all_formulas
    
    for pack in manifest.get("packs", []):
        pack_id = pack["pack_id"]
        formulas = load_pack_formulas(pack_id)
        all_formulas.extend(formulas)
    
    return all_formulas


def load_all_pack_variables() -> list[dict]:
    """Load variables from all available packs.
    
    Returns:
        Combined list of all pack variables
    """
    all_variables = []
    
    manifest = load_pack_manifest()
    if not manifest:
        return all_variables
    
    for pack in manifest.get("packs", []):
        pack_id = pack["pack_id"]
        variables = load_pack_variables(pack_id)
        all_variables.extend(variables)
    
    return all_variables


# Module-level caches
_formula_cache: list[dict] | None = None
_variable_cache: list[dict] | None = None
_pack_cache: list[dict] | None = None


def get_cached_formulas() -> list[dict]:
    """Get cached formulas (load if not cached)."""
    global _formula_cache
    if _formula_cache is None:
        _formula_cache = load_all_pack_formulas()
    return _formula_cache


def get_cached_variables() -> list[dict]:
    """Get cached variables (load if not cached)."""
    global _variable_cache
    if _variable_cache is None:
        _variable_cache = load_all_pack_variables()
    return _variable_cache


def get_cached_packs() -> list[dict]:
    """Get cached pack list (load if not cached)."""
    global _pack_cache
    if _pack_cache is None:
        _pack_cache = get_available_packs()
    return _pack_cache


def invalidate_cache():
    """Invalidate all caches (useful for reloading)."""
    global _formula_cache, _variable_cache, _pack_cache
    _formula_cache = None
    _variable_cache = None
    _pack_cache = None
