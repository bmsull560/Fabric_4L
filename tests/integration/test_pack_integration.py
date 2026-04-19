"""Integration Tests for Value Pack Loading and API

Validates that packs load correctly and API endpoints work as expected.
"""

import json
import pytest
from pathlib import Path

PACKS_DIR = Path(__file__).parent.parent.parent / "packs"


class TestPackLoading:
    """Test pack loading from JSON files."""

    def test_all_packs_loadable(self):
        """All packs in manifest must be loadable."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        for pack in manifest["packs"]:
            pack_path = PACKS_DIR / pack["pack_id"].replace("-v1", "")
            assert pack_path.exists(), f"Pack directory missing: {pack_path}"
            
            # Verify all required files exist
            assert (pack_path / "formulas.json").exists()
            assert (pack_path / "variables.json").exists()
            assert (pack_path / "ontology.json").exists()
            assert (pack_path / "workflow_template.json").exists()
            assert (pack_path / "README.md").exists()

    def test_pack_formulas_loadable(self):
        """All pack formulas must load without errors."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        for pack in manifest["packs"]:
            pack_path = PACKS_DIR / pack["pack_id"].replace("-v1", "")
            formulas_file = pack_path / "formulas.json"
            
            with open(formulas_file) as f:
                data = json.load(f)
            
            assert "formulas" in data
            assert len(data["formulas"]) == pack["formula_count"]
            
            # Validate formula structure
            for formula in data["formulas"]:
                assert "formula_id" in formula
                assert "expression" in formula
                assert "string" in formula["expression"]

    def test_pack_variables_loadable(self):
        """All pack variables must load without errors."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        for pack in manifest["packs"]:
            pack_path = PACKS_DIR / pack["pack_id"].replace("-v1", "")
            variables_file = pack_path / "variables.json"
            
            with open(variables_file) as f:
                data = json.load(f)
            
            assert "variables" in data
            assert len(data["variables"]) == pack["variable_count"]


class TestPackConsistency:
    """Test consistency across pack files."""

    def test_pack_ids_consistent(self):
        """Pack IDs must match across all files in each pack."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        for pack in manifest["packs"]:
            pack_id = pack["pack_id"]
            pack_path = PACKS_DIR / pack_id.replace("-v1", "")
            
            # Check each JSON file has correct pack_id
            for filename in ["formulas.json", "variables.json", "ontology.json", "workflow_template.json"]:
                with open(pack_path / filename) as f:
                    data = json.load(f)
                assert data.get("pack_id") == pack_id, f"{filename} has wrong pack_id in {pack_id}"

    def test_formula_variable_references_valid(self):
        """Formula variable references must point to existing variables."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        for pack in manifest["packs"]:
            pack_path = PACKS_DIR / pack["pack_id"].replace("-v1", "")
            
            # Load variables
            with open(pack_path / "variables.json") as f:
                var_data = json.load(f)
            valid_vars = {v["variable_name"] for v in var_data["variables"]}
            
            # Check formulas
            with open(pack_path / "formulas.json") as f:
                formula_data = json.load(f)
            
            for formula in formula_data["formulas"]:
                expr_vars = formula.get("expression", {}).get("variables", [])
                for var in expr_vars:
                    assert var in valid_vars, f"Invalid variable reference: {var} in {formula['formula_id']}"


class TestManifestAccuracy:
    """Test manifest statistics are accurate."""

    def test_manifest_formula_counts(self):
        """Manifest formula counts must match actual files."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        for pack in manifest["packs"]:
            pack_path = PACKS_DIR / pack["pack_id"].replace("-v1", "")
            
            with open(pack_path / "formulas.json") as f:
                data = json.load(f)
            
            actual_count = len(data["formulas"])
            assert actual_count == pack["formula_count"], f"Formula count mismatch in {pack['pack_id']}"

    def test_manifest_variable_counts(self):
        """Manifest variable counts must match actual files."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        for pack in manifest["packs"]:
            pack_path = PACKS_DIR / pack["pack_id"].replace("-v1", "")
            
            with open(pack_path / "variables.json") as f:
                data = json.load(f)
            
            actual_count = len(data["variables"])
            assert actual_count == pack["variable_count"], f"Variable count mismatch in {pack['pack_id']}"

    def test_manifest_statistics(self):
        """Manifest total statistics must be correct."""
        with open(PACKS_DIR / "pack-manifest.json") as f:
            manifest = json.load(f)
        
        stats = manifest["statistics"]
        total_formulas = sum(p["formula_count"] for p in manifest["packs"])
        total_variables = sum(p["variable_count"] for p in manifest["packs"])
        total_entities = sum(p["entity_count"] for p in manifest["packs"])
        
        assert stats["total_formulas"] == total_formulas
        assert stats["total_variables"] == total_variables
        assert stats["total_entities"] == total_entities


class TestPackLoaderIntegration:
    """Test pack loader integration with Layer 3 API."""
    
    def test_pack_loader_imports(self):
        """Pack loader module must be importable."""
        from src.api.routes.pack_loader import (
            load_pack_manifest,
            load_pack_formulas,
            load_pack_variables,
            get_available_packs,
        )

    def test_pack_loader_formulas(self):
        """Pack loader must return correctly formatted formulas."""
        pytest.importorskip("api.routes.pack_loader", reason="Layer 3 API not available")
        
        from api.routes.pack_loader import load_pack_formulas
        
        formulas = load_pack_formulas("financial-services-v1")
        assert len(formulas) > 0
        
        # Check structure
        for formula in formulas:
            assert "id" in formula
            assert "name" in formula
            assert "expression" in formula
            assert "variables" in formula
            assert "pack_id" in formula
            assert formula["pack_id"] == "financial-services-v1"
