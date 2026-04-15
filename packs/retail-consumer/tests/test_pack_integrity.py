"""Retail & Consumer Value Pack - Integrity Tests

Validates pack structure, JSON validity, and cross-reference integrity.
"""

from pathlib import Path
from typing import Any

import pytest


class TestPackStructure:
    """Verify pack file structure and naming conventions."""

    def test_ontology_json_exists(self, pack_dir: Path) -> None:
        assert (pack_dir / "ontology.json").exists()

    def test_formulas_json_exists(self, pack_dir: Path) -> None:
        assert (pack_dir / "formulas.json").exists()

    def test_variables_json_exists(self, pack_dir: Path) -> None:
        assert (pack_dir / "variables.json").exists()

    def test_workflow_template_json_exists(self, pack_dir: Path) -> None:
        assert (pack_dir / "workflow_template.json").exists()

    def test_readme_exists(self, pack_dir: Path) -> None:
        assert (pack_dir / "README.md").exists()


class TestJsonValidity:
    """Verify all JSON files are valid and well-formed."""

    def test_ontology_json_valid(self, ontology_data: dict[str, Any]) -> None:
        assert isinstance(ontology_data, dict)

    def test_formulas_json_valid(self, formulas_data: dict[str, Any]) -> None:
        assert isinstance(formulas_data, dict)

    def test_variables_json_valid(self, variables_data: dict[str, Any]) -> None:
        assert isinstance(variables_data, dict)

    def test_workflow_template_json_valid(self, workflow_template_data: dict[str, Any]) -> None:
        assert isinstance(workflow_template_data, dict)


class TestPackManifest:
    """Verify pack manifest consistency across all files."""

    def test_ontology_has_pack_id(
        self, pack_files: dict[str, dict[str, Any]], expected_pack_id: str
    ) -> None:
        assert "pack_id" in pack_files["ontology"]
        assert pack_files["ontology"]["pack_id"] == expected_pack_id

    def test_formulas_has_pack_id(
        self, pack_files: dict[str, dict[str, Any]], expected_pack_id: str
    ) -> None:
        assert "pack_id" in pack_files["formulas"]
        assert pack_files["formulas"]["pack_id"] == expected_pack_id

    def test_variables_has_pack_id(
        self, pack_files: dict[str, dict[str, Any]], expected_pack_id: str
    ) -> None:
        assert "pack_id" in pack_files["variables"]
        assert pack_files["variables"]["pack_id"] == expected_pack_id

    def test_workflow_has_pack_id(
        self, pack_files: dict[str, dict[str, Any]], expected_pack_id: str
    ) -> None:
        assert "pack_id" in pack_files["workflow_template"]
        assert pack_files["workflow_template"]["pack_id"] == expected_pack_id

    def test_pack_ids_match(self, pack_files: dict[str, dict[str, Any]]) -> None:
        ids = [
            pack_files["ontology"]["pack_id"],
            pack_files["formulas"]["pack_id"],
            pack_files["variables"]["pack_id"],
            pack_files["workflow_template"]["pack_id"],
        ]
        assert len(set(ids)) == 1, f"Pack IDs do not match: {ids}"


class TestFormulaIntegrity:
    """Verify formula definitions are consistent."""

    # Required fields that every formula must have
    REQUIRED_FIELDS = ["formula_id", "name", "description", "formula_type", "version", "status"]

    def test_formulas_list_exists(self, formulas_data: dict[str, Any]) -> None:
        assert "formulas" in formulas_data
        assert isinstance(formulas_data["formulas"], list)
        assert len(formulas_data["formulas"]) > 0

    def test_all_formulas_have_required_fields(self, formulas_data: dict[str, Any]) -> None:
        for formula in formulas_data["formulas"]:
            for field in self.REQUIRED_FIELDS:
                assert field in formula, f"Formula {formula.get('formula_id', 'unknown')} missing field: {field}"

    def test_formula_ids_unique(self, formulas_data: dict[str, Any]) -> None:
        ids = [f["formula_id"] for f in formulas_data["formulas"]]
        assert len(ids) == len(set(ids)), f"Duplicate formula IDs found: {[x for x in ids if ids.count(x) > 1]}"


class TestVariableIntegrity:
    """Verify variable definitions are consistent."""

    # Required fields that every variable must have
    REQUIRED_FIELDS = ["variable_id", "variable_name", "display_name", "data_type"]

    def test_variables_list_exists(self, variables_data: dict[str, Any]) -> None:
        assert "variables" in variables_data
        assert isinstance(variables_data["variables"], list)

    def test_all_variables_have_required_fields(self, variables_data: dict[str, Any]) -> None:
        for var in variables_data["variables"]:
            for field in self.REQUIRED_FIELDS:
                assert field in var, f"Variable {var.get('variable_id', 'unknown')} missing field: {field}"

    def test_variable_ids_unique(self, variables_data: dict[str, Any]) -> None:
        ids = [v["variable_id"] for v in variables_data["variables"]]
        assert len(ids) == len(set(ids)), f"Duplicate variable IDs found: {[x for x in ids if ids.count(x) > 1]}"

    def test_variable_references_valid_formulas(
        self, variables_data: dict[str, Any], formulas_data: dict[str, Any]
    ) -> None:
        valid_formula_ids = {f["formula_id"] for f in formulas_data["formulas"]}

        for var in variables_data["variables"]:
            if "used_in_formulas" in var:
                for formula_id in var["used_in_formulas"]:
                    assert formula_id in valid_formula_ids, (
                        f"Variable {var.get('variable_id', 'unknown')} references unknown formula: {formula_id}"
                    )
