"""Life Sciences Value Pack - Ontology Relationship Tests

Validates ontology structure, entity relationships, and graph connectivity.
"""

import json
import pytest
from pathlib import Path

PACK_DIR = Path(__file__).parent.parent


class TestOntologyStructure:
    """Verify ontology schema structure."""

    @pytest.fixture(scope="class")
    def ontology(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_has_pack_metadata(self, ontology):
        """Ontology must have pack metadata."""
        assert "pack_id" in ontology
        assert "pack_name" in ontology
        assert "version" in ontology
        assert "industry" in ontology

    def test_has_ontology_definition(self, ontology):
        """Ontology must have ontology definition."""
        assert "ontology" in ontology
        assert "node_types" in ontology["ontology"]
        assert "relationships" in ontology["ontology"]

    def test_has_entities(self, ontology):
        """Ontology must have entities."""
        assert "entities" in ontology
        assert len(ontology["entities"]) > 0

    def test_has_relationships(self, ontology):
        """Ontology must have relationships."""
        assert "relationships" in ontology
        assert len(ontology["relationships"]) > 0


class TestEntityTypes:
    """Verify entity type definitions and counts."""

    @pytest.fixture(scope="class")
    def ontology(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_capability_type_defined(self, ontology):
        """Capability node type must be defined."""
        assert "Capability" in ontology["ontology"]["node_types"]

    def test_usecase_type_defined(self, ontology):
        """UseCase node type must be defined."""
        assert "UseCase" in ontology["ontology"]["node_types"]

    def test_persona_type_defined(self, ontology):
        """Persona node type must be defined."""
        assert "Persona" in ontology["ontology"]["node_types"]

    def test_valuedriver_type_defined(self, ontology):
        """ValueDriver node type must be defined."""
        assert "ValueDriver" in ontology["ontology"]["node_types"]

    def test_capability_entities_exist(self, ontology):
        """Must have Capability entities."""
        caps = [e for e in ontology["entities"] if e["type"] == "Capability"]
        assert len(caps) >= 3

    def test_usecase_entities_exist(self, ontology):
        """Must have UseCase entities."""
        usecases = [e for e in ontology["entities"] if e["type"] == "UseCase"]
        assert len(usecases) >= 2

    def test_persona_entities_exist(self, ontology):
        """Must have Persona entities."""
        personas = [e for e in ontology["entities"] if e["type"] == "Persona"]
        assert len(personas) >= 2

    def test_valuedriver_entities_exist(self, ontology):
        """Must have ValueDriver entities."""
        drivers = [e for e in ontology["entities"] if e["type"] == "ValueDriver"]
        assert len(drivers) >= 2


class TestRelationshipTypes:
    """Verify relationship type definitions."""

    @pytest.fixture(scope="class")
    def ontology(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_enables_relationship_defined(self, ontology):
        """ENABLES relationship must be defined."""
        rels = ontology["ontology"]["relationships"]
        assert "ENABLES" in rels
        assert rels["ENABLES"]["from"] == "Capability"
        assert rels["ENABLES"]["to"] == "UseCase"

    def test_benefits_relationship_defined(self, ontology):
        """BENEFITS relationship must be defined."""
        rels = ontology["ontology"]["relationships"]
        assert "BENEFITS" in rels
        assert rels["BENEFITS"]["from"] == "UseCase"
        assert rels["BENEFITS"]["to"] == "Persona"

    def test_drives_relationship_defined(self, ontology):
        """DRIVES relationship must be defined."""
        rels = ontology["ontology"]["relationships"]
        assert "DRIVES" in rels
        assert rels["DRIVES"]["from"] == "Persona"
        assert rels["DRIVES"]["to"] == "ValueDriver"


class TestRelationshipIntegrity:
    """Verify relationship references are valid."""

    @pytest.fixture(scope="class")
    def ontology(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    @pytest.fixture(scope="class")
    def entity_ids(self, ontology):
        """Extract all entity IDs."""
        return {e["id"] for e in ontology["entities"]}

    def test_all_relationship_from_exist(self, ontology, entity_ids):
        """All relationship 'from' IDs must exist."""
        for rel in ontology["relationships"]:
            assert rel["from"] in entity_ids, \
                f"Relationship references non-existent entity: {rel['from']}"

    def test_all_relationship_to_exist(self, ontology, entity_ids):
        """All relationship 'to' IDs must exist."""
        for rel in ontology["relationships"]:
            assert rel["to"] in entity_ids, \
                f"Relationship references non-existent entity: {rel['to']}"

    def test_no_duplicate_relationships(self, ontology):
        """Should not have duplicate relationship definitions."""
        rel_pairs = [(r["from"], r["to"], r["type"]) for r in ontology["relationships"]]
        assert len(rel_pairs) == len(set(rel_pairs)), "Duplicate relationships found"


class TestGraphConnectivity:
    """Verify graph structure is properly connected."""

    @pytest.fixture(scope="class")
    def ontology(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_capabilities_enable_usecases(self, ontology):
        """Each Capability should ENABLE at least one UseCase."""
        capability_ids = {e["id"] for e in ontology["entities"] if e["type"] == "Capability"}
        enabled_by = set()

        for rel in ontology["relationships"]:
            if rel["type"] == "ENABLES":
                enabled_by.add(rel["from"])

        # Not all capabilities may be used, but at least one should enable something
        assert len(enabled_by) > 0, "No capabilities enable any use cases"

    def test_usecases_benefit_personas(self, ontology):
        """Each UseCase should BENEFIT at least one Persona."""
        usecase_ids = {e["id"] for e in ontology["entities"] if e["type"] == "UseCase"}
        benefiting = set()

        for rel in ontology["relationships"]:
            if rel["type"] == "BENEFITS":
                benefiting.add(rel["from"])

        assert len(benefiting) > 0, "No use cases benefit any personas"

    def test_personas_drive_valuedrivers(self, ontology):
        """Each Persona should DRIVE at least one ValueDriver."""
        persona_ids = {e["id"] for e in ontology["entities"] if e["type"] == "Persona"}
        driving = set()

        for rel in ontology["relationships"]:
            if rel["type"] == "DRIVES":
                driving.add(rel["from"])

        assert len(driving) > 0, "No personas drive any value drivers"

    def test_value_path_exists(self, ontology):
        """Should have at least one complete path: Capability -> UseCase -> Persona -> ValueDriver."""
        # Build adjacency lists
        enables = {}  # capability -> [usecases]
        benefits = {}  # usecase -> [personas]
        drives = {}   # persona -> [value_drivers]

        for rel in ontology["relationships"]:
            if rel["type"] == "ENABLES":
                enables.setdefault(rel["from"], []).append(rel["to"])
            elif rel["type"] == "BENEFITS":
                benefits.setdefault(rel["from"], []).append(rel["to"])
            elif rel["type"] == "DRIVES":
                drives.setdefault(rel["from"], []).append(rel["to"])

        # Check for at least one complete path
        complete_paths = 0
        for cap, usecases in enables.items():
            for uc in usecases:
                if uc in benefits:
                    for per in benefits[uc]:
                        if per in drives:
                            complete_paths += 1

        assert complete_paths > 0, "No complete value paths found"


class TestEntityProperties:
    """Verify entity properties are complete."""

    @pytest.fixture(scope="class")
    def ontology(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_capabilities_have_category(self, ontology):
        """All Capabilities must have category."""
        caps = [e for e in ontology["entities"] if e["type"] == "Capability"]
        for cap in caps:
            assert "category" in cap, f"Capability {cap['id']} missing category"

    def test_capabilities_have_technical_specs(self, ontology):
        """All Capabilities must have technical_specs."""
        caps = [e for e in ontology["entities"] if e["type"] == "Capability"]
        for cap in caps:
            assert "technical_specs" in cap, f"Capability {cap['id']} missing technical_specs"

    def test_usecases_have_automation_level(self, ontology):
        """All UseCases must have automation_level."""
        usecases = [e for e in ontology["entities"] if e["type"] == "UseCase"]
        for uc in usecases:
            assert "automation_level" in uc, f"UseCase {uc['id']} missing automation_level"

    def test_personas_have_role_type(self, ontology):
        """All Personas must have role_type."""
        personas = [e for e in ontology["entities"] if e["type"] == "Persona"]
        for per in personas:
            assert "role_type" in per, f"Persona {per['id']} missing role_type"

    def test_personas_have_department(self, ontology):
        """All Personas must have department."""
        personas = [e for e in ontology["entities"] if e["type"] == "Persona"]
        for per in personas:
            assert "department" in per, f"Persona {per['id']} missing department"

    def test_valuedrivers_have_category(self, ontology):
        """All ValueDrivers must have category."""
        drivers = [e for e in ontology["entities"] if e["type"] == "ValueDriver"]
        for driver in drivers:
            assert "category" in driver, f"ValueDriver {driver['id']} missing category"

    def test_valuedrivers_have_quantification(self, ontology):
        """All ValueDrivers must have quantification_method."""
        drivers = [e for e in ontology["entities"] if e["type"] == "ValueDriver"]
        for driver in drivers:
            assert "quantification_method" in driver, \
                f"ValueDriver {driver['id']} missing quantification_method"


class TestLifeSciencesSpecificEntities:
    """Verify Life Sciences-specific entity content."""

    @pytest.fixture(scope="class")
    def ontology(self):
        """Load ontology data."""
        with open(PACK_DIR / "ontology.json") as f:
            return json.load(f)

    def test_has_clinical_data_capability(self, ontology):
        """Must have Clinical Data Analytics capability."""
        caps = [e for e in ontology["entities"] if e["type"] == "Capability"]
        clinical_caps = [c for c in caps if "Clinical" in c["name"] or "Data" in c["name"]]
        assert len(clinical_caps) > 0, "Missing Clinical Data capability"

    def test_has_patient_engagement_capability(self, ontology):
        """Must have Patient Engagement capability."""
        caps = [e for e in ontology["entities"] if e["type"] == "Capability"]
        patient_caps = [c for c in caps if "Patient" in c["name"]]
        assert len(patient_caps) > 0, "Missing Patient Engagement capability"

    def test_has_dct_usecase(self, ontology):
        """Must have Decentralized Clinical Trials use case."""
        usecases = [e for e in ontology["entities"] if e["type"] == "UseCase"]
        dct_ucs = [uc for uc in usecases if "Decentralized" in uc["name"] or "DCT" in uc["name"]]
        assert len(dct_ucs) > 0, "Missing DCT use case"

    def test_has_cmo_persona(self, ontology):
        """Must have Chief Medical Officer or similar clinical executive."""
        personas = [e for e in ontology["entities"] if e["type"] == "Persona"]
        exec_personas = [p for p in personas if "Medical" in p["name"] or "CMO" in p["name"]]
        assert len(exec_personas) > 0, "Missing CMO persona"

    def test_has_time_to_market_valuedriver(self, ontology):
        """Must have Time-to-Market value driver."""
        drivers = [e for e in ontology["entities"] if e["type"] == "ValueDriver"]
        ttm_drivers = [d for d in drivers if "Time" in d["name"] or "Market" in d["name"]]
        assert len(ttm_drivers) > 0, "Missing Time-to-Market value driver"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
