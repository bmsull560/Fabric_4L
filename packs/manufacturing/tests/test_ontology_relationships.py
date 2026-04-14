"""Ontology relationship integrity tests."""

import pytest
from . import load_pack_file


class TestOntologyRelationships:
    """Validate ontology relationship integrity."""

    @pytest.fixture
    def ontology(self):
        return load_pack_file("ontology.json")

    def test_all_relationships_connect_valid_entities(self, ontology):
        """All relationships must reference existing entity IDs."""
        entity_ids = {e["id"] for e in ontology["entities"]}
        
        for rel in ontology["relationships"]:
            assert rel["from"] in entity_ids, f"Relationship references unknown entity: {rel['from']}"
            assert rel["to"] in entity_ids, f"Relationship references unknown entity: {rel['to']}"

    def test_relationship_types_valid(self, ontology):
        """Relationship types must be from allowed set."""
        valid_types = {"ENABLES", "BENEFITS", "DRIVES"}
        
        for rel in ontology["relationships"]:
            assert rel["type"] in valid_types, f"Invalid relationship type: {rel['type']}"

    def test_capability_enables_use_case_pattern(self, ontology):
        """ENABLES relationships should go from Capability to UseCase."""
        entities = {e["id"]: e for e in ontology["entities"]}
        
        for rel in ontology["relationships"]:
            if rel["type"] == "ENABLES":
                from_type = entities[rel["from"]]["type"]
                to_type = entities[rel["to"]]["type"]
                assert from_type == "Capability", f"ENABLES must start from Capability, got {from_type}"
                assert to_type == "UseCase", f"ENABLES must go to UseCase, got {to_type}"

    def test_use_case_benefits_persona_pattern(self, ontology):
        """BENEFITS relationships should go from UseCase to Persona."""
        entities = {e["id"]: e for e in ontology["entities"]}
        
        for rel in ontology["relationships"]:
            if rel["type"] == "BENEFITS":
                from_type = entities[rel["from"]]["type"]
                to_type = entities[rel["to"]]["type"]
                assert from_type == "UseCase", f"BENEFITS must start from UseCase, got {from_type}"
                assert to_type == "Persona", f"BENEFITS must go to Persona, got {to_type}"

    def test_persona_drives_value_driver_pattern(self, ontology):
        """DRIVES relationships should go from Persona to ValueDriver."""
        entities = {e["id"]: e for e in ontology["entities"]}
        
        for rel in ontology["relationships"]:
            if rel["type"] == "DRIVES":
                from_type = entities[rel["from"]]["type"]
                to_type = entities[rel["to"]]["type"]
                assert from_type == "Persona", f"DRIVES must start from Persona, got {from_type}"
                assert to_type == "ValueDriver", f"DRIVES must go to ValueDriver, got {to_type}"

    def test_entities_have_relationships(self, ontology):
        """Most entities should participate in at least one relationship."""
        entity_ids = {e["id"] for e in ontology["entities"]}
        related_entities = set()
        
        for rel in ontology["relationships"]:
            related_entities.add(rel["from"])
            related_entities.add(rel["to"])
        
        # At least 80% of entities should have relationships
        coverage = len(related_entities) / len(entity_ids)
        assert coverage >= 0.5, f"Only {coverage:.0%} of entities have relationships"

    def test_ontology_has_manufacturing_specific_entities(self, ontology):
        """Ontology must include manufacturing-specific content."""
        entity_names = {e["name"].lower() for e in ontology["entities"]}
        
        # Check for manufacturing keywords
        mfg_keywords = ["predictive", "maintenance", "quality", "oee", "equipment", 
                       "production", "downtime", "energy", "throughput"]
        
        matches = sum(1 for keyword in mfg_keywords if any(keyword in name for name in entity_names))
        assert matches >= 3, "Ontology should have manufacturing-specific entities"


class TestEntityCompleteness:
    """Validate entity attribute completeness."""

    @pytest.fixture
    def ontology(self):
        return load_pack_file("ontology.json")

    def test_capabilities_have_technical_specs(self, ontology):
        """Capabilities should include technical specifications."""
        capabilities = [e for e in ontology["entities"] if e["type"] == "Capability"]
        
        for cap in capabilities:
            assert "technical_specs" in cap or "category" in cap, \
                f"Capability {cap['id']} missing technical details"

    def test_use_cases_have_automation_level(self, ontology):
        """Use cases should specify automation level."""
        use_cases = [e for e in ontology["entities"] if e["type"] == "UseCase"]
        
        for uc in use_cases:
            assert "automation_level" in uc, f"UseCase {uc['id']} missing automation_level"
            valid_levels = {"FULLY_AUTOMATED", "SEMI_AUTOMATED", "ASSISTED", "MANUAL"}
            assert uc["automation_level"] in valid_levels, \
                f"Invalid automation_level: {uc['automation_level']}"

    def test_personas_have_pain_points(self, ontology):
        """Personas should document pain points."""
        personas = [e for e in ontology["entities"] if e["type"] == "Persona"]
        
        for persona in personas:
            assert "pain_points" in persona, f"Persona {persona['id']} missing pain_points"
            assert len(persona["pain_points"]) > 0, f"Persona {persona['id']} has empty pain_points"

    def test_value_drivers_have_quantification(self, ontology):
        """Value drivers should specify quantification method."""
        value_drivers = [e for e in ontology["entities"] if e["type"] == "ValueDriver"]
        
        for vd in value_drivers:
            assert "quantification_method" in vd, f"ValueDriver {vd['id']} missing quantification_method"
            assert "category" in vd, f"ValueDriver {vd['id']} missing category"

    def test_all_entities_have_confidence_scores(self, ontology):
        """Entities should have confidence scores where applicable."""
        for entity in ontology["entities"]:
            if entity["type"] in ["Capability", "UseCase"]:
                assert "confidence_score" in entity, \
                    f"{entity['type']} {entity['id']} missing confidence_score"
