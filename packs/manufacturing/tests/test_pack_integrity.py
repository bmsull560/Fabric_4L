"""Pack integrity tests - validate JSON structure and cross-references."""

import pytest
from . import load_pack_file


class TestOntologyIntegrity:
    """Validate ontology.json structure and content."""

    def test_ontology_has_required_fields(self):
        """Ontology must have pack metadata and entity definitions."""
        ontology = load_pack_file("ontology.json")
        assert "pack_id" in ontology
        assert "pack_name" in ontology
        assert "ontology" in ontology
        assert "entities" in ontology
        assert "relationships" in ontology

    def test_ontology_pack_id_format(self):
        """Pack ID should follow naming convention."""
        ontology = load_pack_file("ontology.json")
        assert ontology["pack_id"] == "manufacturing-v1"
        assert ontology["industry"] == "Manufacturing"

    def test_entities_have_required_fields(self):
        """All entities must have id, type, name, description."""
        ontology = load_pack_file("ontology.json")
        for entity in ontology["entities"]:
            assert "id" in entity, f"Entity missing id: {entity}"
            assert "type" in entity, f"Entity {entity.get('id', 'unknown')} missing type"
            assert "name" in entity, f"Entity {entity.get('id', 'unknown')} missing name"
            assert "description" in entity, f"Entity {entity.get('id', 'unknown')} missing description"

    def test_entity_ids_are_unique(self):
        """All entity IDs must be unique."""
        ontology = load_pack_file("ontology.json")
        ids = [e["id"] for e in ontology["entities"]]
        assert len(ids) == len(set(ids)), f"Duplicate entity IDs found: {ids}"

    def test_entity_types_are_valid(self):
        """Entity types must be from allowed set."""
        ontology = load_pack_file("ontology.json")
        valid_types = {"Capability", "UseCase", "Persona", "ValueDriver"}
        for entity in ontology["entities"]:
            assert entity["type"] in valid_types, f"Invalid type: {entity['type']}"


class TestFormulasIntegrity:
    """Validate formulas.json structure and content."""

    def test_formulas_array_exists(self):
        """Formulas file must contain formulas array."""
        formulas_data = load_pack_file("formulas.json")
        assert "pack_id" in formulas_data
        assert "formulas" in formulas_data
        assert isinstance(formulas_data["formulas"], list)

    def test_formula_count_meets_requirement(self):
        """Must have 5-7 formulas per acceptance criteria."""
        formulas_data = load_pack_file("formulas.json")
        count = len(formulas_data["formulas"])
        assert 5 <= count <= 7, f"Expected 5-7 formulas, found {count}"

    def test_formulas_have_required_fields(self):
        """All formulas must have governance and expression."""
        formulas_data = load_pack_file("formulas.json")
        for formula in formulas_data["formulas"]:
            assert "formula_id" in formula
            assert "name" in formula
            assert "formula_type" in formula
            assert "expression" in formula
            assert "governance" in formula
            assert "required_variables" in formula

    def test_formula_ids_follow_convention(self):
        """Formula IDs must follow mfg-f-NNN pattern."""
        formulas_data = load_pack_file("formulas.json")
        for formula in formulas_data["formulas"]:
            assert formula["formula_id"].startswith("mfg-f-"), \
                f"Invalid formula ID: {formula['formula_id']}"

    def test_formula_governance_complete(self):
        """Active formulas must have complete governance metadata."""
        formulas_data = load_pack_file("formulas.json")
        for formula in formulas_data["formulas"]:
            gov = formula["governance"]
            assert "owner" in gov
            assert "review_cycle" in gov
            assert "approval_status" in gov
            if formula["status"] == "active":
                assert "last_reviewed" in gov, \
                    f"Active formula {formula['formula_id']} missing last_reviewed"

    def test_formula_variables_exist_in_catalog(self):
        """All formula variables must be defined in variables.json."""
        formulas_data = load_pack_file("formulas.json")
        variables_data = load_pack_file("variables.json")
        
        var_ids = {v["variable_id"] for v in variables_data["variables"]}
        var_names = {v["variable_name"] for v in variables_data["variables"]}
        
        for formula in formulas_data["formulas"]:
            for var in formula["required_variables"]:
                var_name = var["name"]
                assert var_name in var_names, \
                    f"Formula {formula['formula_id']} references undefined variable: {var_name}"


class TestVariablesIntegrity:
    """Validate variables.json structure and content."""

    def test_variables_array_exists(self):
        """Variables file must contain variables array."""
        variables_data = load_pack_file("variables.json")
        assert "pack_id" in variables_data
        assert "variables" in variables_data
        assert isinstance(variables_data["variables"], list)

    def test_variables_cover_manufacturing_kpis(self):
        """Must include OEE, throughput, downtime KPIs."""
        variables_data = load_pack_file("variables.json")
        var_names = {v["variable_name"].lower() for v in variables_data["variables"]}
        
        # Check for OEE-related
        assert any("oee" in name for name in var_names), "Missing OEE variable"
        
        # Check for throughput-related  
        assert any("throughput" in name for name in var_names), "Missing throughput variable"
        
        # Check for downtime-related
        assert any("downtime" in name for name in var_names), "Missing downtime variable"

    def test_variables_have_required_fields(self):
        """All variables must have complete metadata."""
        variables_data = load_pack_file("variables.json")
        for var in variables_data["variables"]:
            assert "variable_id" in var
            assert "variable_name" in var
            assert "data_type" in var
            assert "source_type" in var
            assert "description" in var

    def test_variable_ids_follow_convention(self):
        """Variable IDs must follow mfg-var-NNN pattern."""
        variables_data = load_pack_file("variables.json")
        for var in variables_data["variables"]:
            assert var["variable_id"].startswith("mfg-var-"), \
                f"Invalid variable ID: {var['variable_id']}"

    def test_variable_data_types_valid(self):
        """Data types must be from allowed set."""
        variables_data = load_pack_file("variables.json")
        valid_types = {"INTEGER", "FLOAT", "CURRENCY", "PERCENTAGE", "BOOLEAN", "STRING"}
        for var in variables_data["variables"]:
            assert var["data_type"] in valid_types, f"Invalid data type: {var['data_type']}"


class TestWorkflowIntegrity:
    """Validate workflow_template.json structure."""

    def test_workflow_has_required_fields(self):
        """Workflow must have complete metadata."""
        workflow = load_pack_file("workflow_template.json")
        assert "pack_id" in workflow
        assert "template_id" in workflow
        assert "template_name" in workflow
        assert "phases" in workflow

    def test_workflow_phases_have_tasks(self):
        """Each phase must contain tasks."""
        workflow = load_pack_file("workflow_template.json")
        for phase in workflow["phases"]:
            assert "phase_id" in phase
            assert "name" in phase
            assert "tasks" in phase
            assert len(phase["tasks"]) > 0

    def test_workflow_task_dependencies_valid(self):
        """Task dependencies must reference existing tasks."""
        workflow = load_pack_file("workflow_template.json")
        all_task_ids = set()
        
        for phase in workflow["phases"]:
            for task in phase["tasks"]:
                all_task_ids.add(task["task_id"])
        
        for phase in workflow["phases"]:
            for task in phase["tasks"]:
                for dep in task.get("dependencies", []):
                    assert dep in all_task_ids, f"Invalid dependency: {dep} in task {task['task_id']}"
