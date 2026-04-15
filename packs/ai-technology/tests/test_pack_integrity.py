"""AI & Technology Value Pack - Integrity Tests

Validates pack structure, JSON validity, and cross-reference integrity.

NOTE (P1-4): File handle verification - fixtures use scope="class" which may
hold files open longer. Monitor for FD exhaustion under high concurrency.
See: cat /proc/sys/fs/file-nr or lsof -p <pid> during load testing.
"""

import json
import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestPackStructure:
    """Verify pack file structure and naming conventions."""

    def test_ontology_json_exists(self):
        assert (PACK_DIR / "ontology.json").exists()

    def test_formulas_json_exists(self):
        assert (PACK_DIR / "formulas.json").exists()

    def test_variables_json_exists(self):
        assert (PACK_DIR / "variables.json").exists()

    def test_workflow_template_json_exists(self):
        assert (PACK_DIR / "workflow_template.json").exists()

    def test_readme_exists(self):
        assert (PACK_DIR / "README.md").exists()


class TestJsonValidity:
    """Verify all JSON files are valid and well-formed."""

    def test_ontology_json_valid(self):
        with open(PACK_DIR / "ontology.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_formulas_json_valid(self):
        with open(PACK_DIR / "formulas.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_variables_json_valid(self):
        with open(PACK_DIR / "variables.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)

    def test_workflow_template_json_valid(self):
        with open(PACK_DIR / "workflow_template.json") as f:
            data = json.load(f)
        assert isinstance(data, dict)


class TestPackManifest:
    """Verify pack manifest consistency across all files."""

    @pytest.fixture(scope="class")
    def pack_files(self):
        files = {}
        for name in ["ontology", "formulas", "variables", "workflow_template"]:
            with open(PACK_DIR / f"{name}.json") as f:
                files[name] = json.load(f)
        return files

    def test_ontology_has_pack_id(self, pack_files):
        assert "pack_id" in pack_files["ontology"]
        assert pack_files["ontology"]["pack_id"] == "ai-technology-v1"

    def test_formulas_has_pack_id(self, pack_files):
        assert "pack_id" in pack_files["formulas"]
        assert pack_files["formulas"]["pack_id"] == "ai-technology-v1"

    def test_variables_has_pack_id(self, pack_files):
        assert "pack_id" in pack_files["variables"]
        assert pack_files["variables"]["pack_id"] == "ai-technology-v1"

    def test_workflow_has_pack_id(self, pack_files):
        assert "pack_id" in pack_files["workflow_template"]
        assert pack_files["workflow_template"]["pack_id"] == "ai-technology-v1"

    def test_pack_ids_match(self, pack_files):
        ids = [
            pack_files["ontology"]["pack_id"],
            pack_files["formulas"]["pack_id"],
            pack_files["variables"]["pack_id"],
            pack_files["workflow_template"]["pack_id"],
        ]
        assert len(set(ids)) == 1


class TestFormulaIntegrity:
    """Verify formula definitions are consistent."""

    @pytest.fixture(scope="class")
    def formulas_data(self):
        with open(PACK_DIR / "formulas.json") as f:
            return json.load(f)

    def test_formulas_list_exists(self, formulas_data):
        assert "formulas" in formulas_data
        assert isinstance(formulas_data["formulas"], list)

    def test_all_formulas_have_required_fields(self, formulas_data):
        required = ["formula_id", "name", "description", "formula_type", "version", "status"]
        for formula in formulas_data["formulas"]:
            for field in required:
                assert field in formula

    def test_formula_ids_unique(self, formulas_data):
        ids = [f["formula_id"] for f in formulas_data["formulas"]]
        assert len(ids) == len(set(ids))


class TestVariableIntegrity:
    """Verify variable definitions are consistent."""

    @pytest.fixture(scope="class")
    def variables_data(self):
        with open(PACK_DIR / "variables.json") as f:
            return json.load(f)

    def test_variables_list_exists(self, variables_data):
        assert "variables" in variables_data
        assert isinstance(variables_data["variables"], list)

    def test_all_variables_have_required_fields(self, variables_data):
        required = ["variable_id", "variable_name", "display_name", "data_type"]
        for var in variables_data["variables"]:
            for field in required:
                assert field in var

    def test_variable_ids_unique(self, variables_data):
        ids = [v["variable_id"] for v in variables_data["variables"]]
        assert len(ids) == len(set(ids))
