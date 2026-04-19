"""
Standalone Pack Loader — importable without Layer 3 API dependencies.
This module provides the same interface as pack_loader.py but has zero
external dependencies (no neo4j, no FastAPI, no agents). Safe to import
in any context including CI/CD test environments without a running database.
"""
import json
from pathlib import Path
from typing import Any

PACKS_DIR = Path(__file__).parent.parent.parent.parent.parent.parent / "packs"
MANIFEST_FILE = PACKS_DIR / "pack-manifest.json"


def load_pack_manifest() -> dict[str, Any] | None:
    if not MANIFEST_FILE.exists():
        return None
    with open(MANIFEST_FILE) as f:
        return json.load(f)


def load_pack_formulas(pack_id: str) -> list[dict]:
    pack_slug = pack_id.replace("-v1", "").replace("-v2", "").replace("-v3", "")
    formulas_file = PACKS_DIR / pack_slug / "formulas.json"
    if not formulas_file.exists():
        return []
    with open(formulas_file) as f:
        data = json.load(f)
    return [
        {
            "id": f.get("formula_id"),
            "name": f.get("name", ""),
            "expression": f.get("expression", {}).get("string", ""),
            "variables": f.get("expression", {}).get("variables", []),
            "pack_id": pack_id,
        }
        for f in data.get("formulas", [])
    ]


def load_pack_variables(pack_id: str) -> list[dict]:
    pack_slug = pack_id.replace("-v1", "").replace("-v2", "").replace("-v3", "")
    variables_file = PACKS_DIR / pack_slug / "variables.json"
    if not variables_file.exists():
        return []
    with open(variables_file) as f:
        data = json.load(f)
    return data.get("variables", [])


def get_available_packs() -> list[dict]:
    manifest = load_pack_manifest()
    if not manifest:
        return []
    return manifest.get("packs", [])
