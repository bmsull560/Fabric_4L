"""Financial Services Value Pack - Integrity Tests

Validates pack structure, JSON validity, and cross-reference integrity.
"""

import json
import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestPackStructure:
    """Verify pack file structure and naming conventions."""

    def test_ontology_json_exists(self):
        """ontology.json must exist."""
        assert (PACK_DIR / "ontology.json").exists()

    def test_formulas_json_exists(self):
        """formulas.json must exist."""
        assert (PACK_DIR / "formulas.json").exists()

    def test_variables_json_exists(self):
        """variables.json must exist."""
        assert (PACK_DIR / "variables.json").exists()

    def test_workflow_template_json_exists(self):
        """workflow_template.json must exist."""
        assert (PACK_DIR / "workflow_template.json").exists()

    def test_readme_exists(self):
        """README.md must exist."""
        assert (PACK_DIR / "README.md").exists()


class TestJsonValidity:
    """Verify all JSON files are valid and well-formed."""

    def test_ontology_json_valid(self):
        """ontology.json must be valid JSON."""
        with open(PACK_DIR / "ontology.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_formulas_json_valid(self):
        """formulas.json must be valid JSON."""
        with open(PACK_DIR / "formulas.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_variables_json_valid(self):
        """variables.json must be valid JSON."""
        with open(PACK_DIR / "variables.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_workflow_template_json_valid(self):
        """workflow_template.json must be valid JSON."""
        with open(PACK_DIR / "workflow_template.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestPackManifest:
    """Verify pack manifest consistency across all files."""

    @pytest.fixture(scope="class")
    def pack_files(self):
        """Load all pack JSON files."""
        files = {}
        for name in ["ontology", "formulas", "variables", "workflow_template"]:
            with open(PACK_DIR / f"{name}.json") as f:
                files[name] = json.load(f)
        return files

    def test_ontology_has_pack_id(self, pack_files):
        """ontology.json must have pack_id."""
        assert "pack_id" in pack_files["ontology"]
        assert pack_files["ontology"]["pack_id"] == "financial-services-v1"

    def test_formulas_has_pack_id(self, pack_files):
        """formulas.json must have pack_id."""
        assert "pack_id" in pack_files["formulas"]
        assert pack_files["formulas"]["pack_id"] == "financial-services-v1"

    def test_variables_has_pack_id(self, pack_files):
        """variables.json must have pack_id."""
        assert "pack_id" in pack_files["variables"]
        assert pack_files["variables"]["pack_id"] == "financial-services-v1"

    def test_workflow_has_pack_id(self, pack_files):
        """workflow_template.json must have pack_id."""
        assert "pack_id" in pack_files["workflow_template"]
        assert pack_files["workflow_template"]["pack_id"] == "financial-services-v1"

    def test_pack_ids_match(self, pack_files):
        """All pack_ids must match across files."""
        ids = [
            pack_files["ontology"]["pack_id"],
            pack_files["formulas"]["pack_id"],
            pack_files["variables"]["pack_id"],
            pack_files["workflow_template"]["pack_id"],
        ]
        assert len(set(ids)) == 1, f"Pack IDs don't match: {ids}"


class TestFormulaIntegrity:
    """Verify formula definitions are consistent."""

    @pytest.fixture(scope="class")
    def formulas_data(self):
        """Load formulas data."""
        with open(PACK_DIR / "formulas.json") as f:
            return json.load(f)

    def test_formulas_list_exists(self, formulas_data):
        """Formulas must have a list."""
        assert "formulas" in formulas_data
        assert isinstance(formulas_data["formulas"], list)
        assert len(formulas_data["formulas"]) > 0

    def test_all_formulas_have_required_fields(self, formulas_data):
        """Each formula must have required fields."""
        required = ["formula_id", "name", "description", "formula_type", "version", "status"]
        for formula in formulas_data["formulas"]:
            for field in required:
                assert field in formula, f"Formula {formula.get('formula_id', 'unknown')} missing {field}"

    def test_formula_ids_unique(self, formulas_data):
        """Formula IDs must be unique."""
        ids = [f["formula_id"] for f in formulas_data["formulas"]]
        assert len(ids) == len(set(ids)), f"Duplicate formula IDs: {ids}"

    def test_formula_types_valid(self, formulas_data):
        """Formula types must be valid."""
        valid_types = ["ROI", "NPV", "IRR", "Payback", "Productivity", "Efficiency", "Cost_Avoidance", "Custom"]
        for formula in formulas_data["formulas"]:
            assert formula["formula_type"] in valid_types, f"Invalid type: {formula['formula_type']}"


class TestVariableIntegrity:
    """Verify variable definitions are consistent."""

    @pytest.fixture(scope="class")
    def variables_data(self):
        """Load variables data."""
        with open(PACK_DIR / "variables.json") as f:
            return json.load(f)

    def test_variables_list_exists(self, variables_data):
        """Variables must have a list."""
        assert "variables" in variables_data
        assert isinstance(variables_data["variables"], list)
        assert len(variables_data["variables"]) > 0

    def test_all_variables_have_required_fields(self, variables_data):
        """Each variable must have required fields."""
        required = ["variable_id", "variable_name", "display_name", "data_type"]
        for var in variables_data["variables"]:
            for field in required:
                assert field in var, f"Variable {var.get('variable_id', 'unknown')} missing {field}"

    def test_variable_ids_unique(self, variables_data):
        """Variable IDs must be unique."""
        ids = [v["variable_id"] for v in variables_data["variables"]]
        assert len(ids) == len(set(ids)), f"Duplicate variable IDs: {ids}"

    def test_variable_references_valid_formulas(self, variables_data):
        """Variables' used_in_formulas must reference valid formulas."""
        with open(PACK_DIR / "formulas.json") as f:
            formulas = json.load(f)
        valid_formula_ids = {f["formula_id"] for f in formulas["formulas"]}
        
        for var in variables_data["variables"]:
            if "used_in_formulas" in var:
                for formula_id in var["used_in_formulas"]:
                    assert formula_id in valid_formula_ids, f"Invalid formula reference: {formula_id}"
