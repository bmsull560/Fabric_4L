"""Retail & Consumer Value Pack - Ontology Relationship Tests"""

from collections import Counter
from typing import Any

import pytest

# Local constants (pytest conftest discovery works for fixtures, not module globals)
REQUIRED_ONTOLOGY_NODE_TYPES: list[str] = ["Capability", "UseCase", "Persona", "ValueDriver"]
REQUIRED_ONTOLOGY_RELATIONSHIPS: list[str] = ["ENABLES", "BENEFITS", "DRIVES"]
REQUIRED_ENTITY_FIELDS: list[str] = ["type", "id", "name", "description"]


class TestOntologyStructure:
    """Verify ontology structure and completeness."""

    def test_ontology_has_pack_metadata(self, ontology_data: dict[str, Any]) -> None:
        assert "pack_id" in ontology_data, "Missing pack_id in ontology"
        assert "pack_name" in ontology_data, "Missing pack_name in ontology"
        assert "ontology" in ontology_data, "Missing ontology section"

    def test_ontology_has_node_types(self, ontology_data: dict[str, Any]) -> None:
        assert "node_types" in ontology_data["ontology"], "Missing node_types"
        for nt in REQUIRED_ONTOLOGY_NODE_TYPES:
            assert nt in ontology_data["ontology"]["node_types"], f"Missing node type: {nt}"

    def test_ontology_has_relationships(self, ontology_data: dict[str, Any]) -> None:
        assert "relationships" in ontology_data["ontology"], "Missing relationships"
        for rel in REQUIRED_ONTOLOGY_RELATIONSHIPS:
            assert rel in ontology_data["ontology"]["relationships"], f"Missing relationship: {rel}"


class TestEntities:
    """Verify entity definitions."""

    def test_entities_exist(self, ontology_data: dict[str, Any]) -> None:
        assert "entities" in ontology_data, "Missing entities section"
        assert isinstance(ontology_data["entities"], list), "Entities should be a list"

    def test_entities_have_required_fields(self, ontology_data: dict[str, Any]) -> None:
        for entity in ontology_data["entities"]:
            for field in REQUIRED_ENTITY_FIELDS:
                assert field in entity, f"Entity {entity.get('id', 'unknown')} missing field: {field}"

    def test_entity_ids_unique(self, ontology_data: dict[str, Any]) -> None:
        ids = [e["id"] for e in ontology_data["entities"]]
        id_counts = Counter(ids)
        duplicates = [id for id, count in id_counts.items() if count > 1]
        assert len(duplicates) == 0, f"Duplicate entity IDs found: {duplicates}"


class TestRetailConsumerSpecific:
    """Retail & Consumer domain-specific ontology tests."""

    def test_has_omnichannel_capability(self, ontology_data: dict[str, Any]) -> None:
        omni_caps = [
            e for e in ontology_data["entities"]
            if e["type"] == "Capability" and "omnichannel" in e["name"].lower()
        ]
        assert len(omni_caps) > 0, "No omnichannel capability found in ontology"

    def test_has_merchandising_persona(self, ontology_data: dict[str, Any]) -> None:
        merch_personas = [
            e for e in ontology_data["entities"]
            if e["type"] == "Persona" and "merchandis" in e["name"].lower()
        ]
        assert len(merch_personas) > 0, "No merchandising persona found in ontology"
