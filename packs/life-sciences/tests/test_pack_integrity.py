"""Life Sciences Value Pack - Integrity Tests

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
        assert pack_files["ontology"]["pack_id"] == "life-sciences-v1"

    def test_formulas_has_pack_id(self, pack_files):
        """formulas.json must have pack_id."""
        assert "pack_id" in pack_files["formulas"]
        assert pack_files["formulas"]["pack_id"] == "life-sciences-v1"

    def test_variables_has_pack_id(self, pack_files):
        """variables.json must have pack_id."""
        assert "pack_id" in pack_files["variables"]
        assert pack_files["variables"]["pack_id"] == "life-sciences-v1"

    def test_workflow_has_pack_id(self, pack_files):
        """workflow_template.json must have pack_id."""
        assert "pack_id" in pack_files["workflow_template"]
        assert pack_files["workflow_template"]["pack_id"] == "life-sciences-v1"

    def test_pack_id_consistency(self, pack_files):
        """All files must have the same pack_id."""
        pack_ids = {name: data["pack_id"] for name, data in pack_files.items()}
        assert len(set(pack_ids.values())) == 1, f"Inconsistent pack_ids: {pack_ids}"


class TestNamingConventions:
    """Verify ID naming conventions are followed."""

    @pytest.fixture(scope="class")
    def pack_data(self):
        """Load all pack data."""
        with open(PACK_DIR / "ontology.json") as f:
            ontology = json.load(f)
        with open(PACK_DIR / "formulas.json") as f:
            formulas = json.load(f)
        with open(PACK_DIR / "variables.json") as f:
            variables = json.load(f)
        return {"ontology": ontology, "formulas": formulas, "variables": variables}

    def test_entity_ids_follow_convention(self, pack_data):
        """Entity IDs must follow ls-{type}-{number} pattern."""
        for entity in pack_data["ontology"]["entities"]:
            entity_id = entity["id"]
            assert entity_id.startswith("ls-"), f"Entity {entity_id} doesn't start with ls-"
            parts = entity_id.split("-")
            assert len(parts) == 3, f"Entity {entity_id} doesn't have 3 parts"
            assert parts[2].isdigit(), f"Entity {entity_id} doesn't end with number"

    def test_formula_ids_follow_convention(self, pack_data):
        """Formula IDs must follow ls-f-{number} pattern."""
        for formula in pack_data["formulas"]["formulas"]:
            formula_id = formula["formula_id"]
            assert formula_id.startswith("ls-f-"), f"Formula {formula_id} doesn't start with ls-f-"
            assert formula_id.split("-")[2].isdigit(), f"Formula {formula_id} doesn't end with number"

    def test_variable_ids_follow_convention(self, pack_data):
        """Variable IDs must follow ls-var-{number} pattern."""
        for variable in pack_data["variables"]["variables"]:
            var_id = variable["variable_id"]
            assert var_id.startswith("ls-var-"), f"Variable {var_id} doesn't start with ls-var-"
            assert var_id.split("-")[2].isdigit(), f"Variable {var_id} doesn't end with number"


class TestFormulaVariableReferences:
    """Verify formulas reference existing variables."""

    @pytest.fixture(scope="class")
    def pack_data(self):
        """Load all pack data."""
        with open(PACK_DIR / "formulas.json") as f:
            formulas = json.load(f)
        with open(PACK_DIR / "variables.json") as f:
            variables = json.load(f)
        variable_names = {v["variable_name"] for v in variables["variables"]}
        return {"formulas": formulas, "variable_names": variable_names}

    def test_formula_variables_exist(self, pack_data):
        """All formula variables must exist in variables.json."""
        for formula in pack_data["formulas"]["formulas"]:
            formula_id = formula["formula_id"]
            for var in formula["expression"]["variables"]:
                assert var in pack_data["variable_names"], \
                    f"Formula {formula_id} references unknown variable: {var}"

    def test_required_variables_have_definitions(self, pack_data):
        """All required_variables must be defined in the formula."""
        for formula in pack_data["formulas"]["formulas"]:
            if "required_variables" in formula:
                required_names = {rv["name"] for rv in formula["required_variables"]}
                expr_vars = set(formula["expression"]["variables"])
                # Required variables should be subset of expression variables
                assert required_names.issubset(expr_vars), \
                    f"Formula {formula['formula_id']} has required_variables not in expression"


class TestOntologyRelationships:
    """Verify ontology relationship integrity."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_all_relationships_reference_existing_entities(self, ontology_data):
        """All relationship from/to IDs must exist in entities."""
        entity_ids = {e["id"] for e in ontology_data["entities"]}
        for rel in ontology_data["relationships"]:
            assert rel["from"] in entity_ids, f"Relationship references unknown entity: {rel['from']}"
            assert rel["to"] in entity_ids, f"Relationship references unknown entity: {rel['to']}"

    def test_relationship_types_valid(self, ontology_data):
        """All relationships must use valid relationship types."""
        valid_types = set(ontology_data["ontology"]["relationships"].keys())
        for rel in ontology_data["relationships"]:
            assert rel["type"] in valid_types, f"Invalid relationship type: {rel['type']}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
