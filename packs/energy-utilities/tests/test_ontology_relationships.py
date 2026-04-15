"""Energy & Utilities Value Pack - Ontology Relationship Tests

Validates entity relationships and ontology structure.
"""

import json
import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestOntologyStructure:
    """Verify ontology structure and completeness."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_ontology_has_pack_metadata(self, ontology_data):
        """Ontology must have pack metadata."""
        assert "pack_id" in ontology_data
        assert "pack_name" in ontology_data
        assert "version" in ontology_data
        assert "ontology" in ontology_data

    def test_ontology_has_node_types(self, ontology_data):
        """Ontology must define node types."""
        assert "node_types" in ontology_data["ontology"]
        node_types = ontology_data["ontology"]["node_types"]
        
        required_types = ["Capability", "UseCase", "Persona", "ValueDriver"]
        for nt in required_types:
            assert nt in node_types, f"Missing node type: {nt}"

    def test_ontology_has_relationships(self, ontology_data):
        """Ontology must define relationships."""
        assert "relationships" in ontology_data["ontology"]
        rels = ontology_data["ontology"]["relationships"]
        
        required_rels = ["ENABLES", "BENEFITS", "DRIVES"]
        for rel in required_rels:
            assert rel in rels, f"Missing relationship: {rel}"


class TestEntities:
    """Verify entity definitions."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_entities_exist(self, ontology_data):
        """Entities list must exist."""
        assert "entities" in ontology_data
        assert isinstance(ontology_data["entities"], list)
        assert len(ontology_data["entities"]) > 0

    def test_entities_have_required_fields(self, ontology_data):
        """Each entity must have required fields."""
        required = ["type", "id", "name", "description"]
        for entity in ontology_data["entities"]:
            for field in required:
                assert field in entity, f"Entity {entity.get('id', 'unknown')} missing {field}"

    def test_entity_types_valid(self, ontology_data):
        """Entity types must be valid node types."""
        valid_types = set(ontology_data["ontology"]["node_types"].keys())
        for entity in ontology_data["entities"]:
            assert entity["type"] in valid_types, f"Invalid entity type: {entity['type']}"

    def test_entity_ids_unique(self, ontology_data):
        """Entity IDs must be unique."""
        ids = [e["id"] for e in ontology_data["entities"]]
        assert len(ids) == len(set(ids)), f"Duplicate entity IDs: {ids}"


class TestRelationships:
    """Verify relationship definitions."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_relationships_exist(self, ontology_data):
        """Relationships list must exist."""
        assert "relationships" in ontology_data
        assert isinstance(ontology_data["relationships"], list)
        assert len(ontology_data["relationships"]) > 0

    def test_relationships_have_required_fields(self, ontology_data):
        """Each relationship must have required fields."""
        required = ["type", "from", "to"]
        for rel in ontology_data["relationships"]:
            for field in required:
                assert field in rel, f"Relationship missing {field}"

    def test_relationship_types_valid(self, ontology_data):
        """Relationship types must be valid."""
        valid_types = set(ontology_data["ontology"]["relationships"].keys())
        for rel in ontology_data["relationships"]:
            assert rel["type"] in valid_types, f"Invalid relationship type: {rel['type']}"

    def test_relationship_references_valid_entities(self, ontology_data):
        """Relationships must reference valid entities."""
        valid_ids = {e["id"] for e in ontology_data["entities"]}
        
        for rel in ontology_data["relationships"]:
            assert rel["from"] in valid_ids, f"Relationship references unknown entity: {rel['from']}"
            assert rel["to"] in valid_ids, f"Relationship references unknown entity: {rel['to']}"


class TestEnergyUtilitiesSpecific:
    """Energy & Utilities domain-specific ontology tests."""

    @pytest.fixture(scope="class")
    def ontology_data(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_has_smart_grid_capability(self, ontology_data):
        """Must have smart grid capability."""
        grid_caps = [e for e in ontology_data["entities"] 
                    if e["type"] == "Capability" and ("grid" in e["name"].lower() or "ami" in e["name"].lower())]
        assert len(grid_caps) > 0, "Missing smart grid capability"

    def test_has_renewable_capability(self, ontology_data):
        """Must have renewable energy capability."""
        renewable_caps = [e for e in ontology_data["entities"] 
                         if e["type"] == "Capability" and "renewable" in e["name"].lower()]
        assert len(renewable_caps) > 0, "Missing renewable energy capability"

    def test_has_grid_operations_persona(self, ontology_data):
        """Must have grid operations persona."""
        grid_personas = [e for e in ontology_data["entities"] 
                        if e["type"] == "Persona" and 
                        ("grid" in e["name"].lower() or "operations" in e["name"].lower())]
        assert len(grid_personas) > 0, "Missing grid operations persona"

    def test_has_saidi_driver(self, ontology_data):
        """Must have SAIDI value driver."""
        saidi_drivers = [e for e in ontology_data["entities"] 
                        if e["type"] == "ValueDriver" and 
                        ("saidi" in e["name"].lower() or "outage" in e["name"].lower() or "duration" in e["name"].lower())]
        assert len(saidi_drivers) > 0, "Missing SAIDI/outage value driver"
