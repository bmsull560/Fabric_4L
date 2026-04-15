"""AI & Technology Value Pack - Ontology Relationship Tests"""

import json
import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestOntologyStructure:
    """Verify ontology structure and completeness."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_ontology_has_pack_metadata(self, ontology_data):
        assert "pack_id" in ontology_data
        assert "pack_name" in ontology_data
        assert "ontology" in ontology_data

    def test_ontology_has_node_types(self, ontology_data):
        assert "node_types" in ontology_data["ontology"]
        required_types = ["Capability", "UseCase", "Persona", "ValueDriver"]
        for nt in required_types:
            assert nt in ontology_data["ontology"]["node_types"]

    def test_ontology_has_relationships(self, ontology_data):
        assert "relationships" in ontology_data["ontology"]
        required_rels = ["ENABLES", "BENEFITS", "DRIVES"]
        for rel in required_rels:
            assert rel in ontology_data["ontology"]["relationships"]


class TestEntities:
    """Verify entity definitions."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_entities_exist(self, ontology_data):
        assert "entities" in ontology_data
        assert isinstance(ontology_data["entities"], list)

    def test_entities_have_required_fields(self, ontology_data):
        required = ["type", "id", "name", "description"]
        for entity in ontology_data["entities"]:
            for field in required:
                assert field in entity

    def test_entity_ids_unique(self, ontology_data):
        ids = [e["id"] for e in ontology_data["entities"]]
        assert len(ids) == len(set(ids))


class TestAITechnologySpecific:
    """AI Technology domain-specific ontology tests."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_has_mlops_capability(self, ontology_data):
        mlops_caps = [e for e in ontology_data["entities"] 
                     if e["type"] == "Capability" and "mlops" in e["name"].lower()]
        assert len(mlops_caps) > 0

    def test_has_llm_capability(self, ontology_data):
        llm_caps = [e for e in ontology_data["entities"] 
                   if e["type"] == "Capability" and "llm" in e["name"].lower()]
        assert len(llm_caps) > 0

    def test_has_ai_officer_persona(self, ontology_data):
        ai_personas = [e for e in ontology_data["entities"] 
                      if e["type"] == "Persona" and ("ai" in e["name"].lower() or "chief" in e["name"].lower())]
        assert len(ai_personas) > 0
