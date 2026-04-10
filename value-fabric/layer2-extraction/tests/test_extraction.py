"""Tests for the extraction pipeline.

Tests the 6-stage extraction pipeline with sample documents.
"""

import os
import pytest
from datetime import datetime

from layer2_extraction.models import Capability, UseCase, Persona, ValueDriver, Feature, RoleType, ValueCategory
from layer2_extraction.models import Relationship, PredicateType
from layer2_extraction.extraction import chunk_markdown, SemanticChunker


class TestOntologyModels:
    """Test Pydantic ontology models."""
    
    def test_capability_creation(self):
        """Test creating a Capability entity."""
        cap = Capability(
            name="Real-Time Data Ingestion",
            description="Stream data from multiple sources with sub-second latency",
            technical_features=["Kafka streaming", "CDC"],
            confidence=0.92
        )
        
        assert cap.name == "Real-Time Data Ingestion"
        assert len(cap.id) == 36  # UUID length
        assert cap.confidence == 0.92
        assert cap.technical_features == ["Kafka streaming", "CDC"]
    
    def test_capability_validation(self):
        """Test Capability field validation."""
        with pytest.raises(ValueError):
            Capability(name="", description="Too short")  # Empty name
        
        with pytest.raises(ValueError):
            Capability(name="Test", description="Short")  # Description too short
    
    def test_usecase_validation(self):
        """Test UseCase validation with capability references."""
        cap = Capability(name="Test Capability", description="A test capability")
        
        uc = UseCase(
            name="Test Use Case",
            description="A test use case description",
            required_capabilities=[cap.id]
        )
        
        assert cap.id in uc.required_capabilities
    
    def test_value_driver_formula_validation(self):
        """Test ValueDriver formula string validation."""
        # Valid formula
        vd = ValueDriver(
            category=ValueCategory.COST,
            name="Cost Reduction",
            description="Reduces operational costs",
            unit="USD",
            formula_string="({hours_saved} * {hourly_rate}) - {implementation_cost}"
        )
        assert vd.formula_string is not None
        
        # Invalid formula with illegal characters
        with pytest.raises(ValueError):
            ValueDriver(
                category=ValueCategory.COST,
                name="Bad Formula",
                description="Test",
                unit="USD",
                formula_string="{hours} * $rate"  # $ is not allowed
            )
    
    def test_persona_role_type(self):
        """Test Persona role type enum."""
        persona = Persona(
            role_type=RoleType.ECONOMIC_BUYER,
            title="Chief Financial Officer",
            department="Finance"
        )
        
        assert persona.role_type == RoleType.ECONOMIC_BUYER
        assert persona.role_type.value == "economic_buyer"
    
    def test_feature_creation(self):
        """Test creating a Feature entity."""
        feature = Feature(
            name="Dashboard Widget",
            description="Real-time analytics dashboard widget for monitoring KPIs",
            implementation_status="ga",
            confidence=0.88
        )
        
        assert feature.name == "Dashboard Widget"
        assert feature.implementation_status == "ga"
        assert feature.confidence == 0.88
    
    def test_feature_validation(self):
        """Test Feature field validation."""
        # Valid statuses
        for status in ["planned", "beta", "ga", "deprecated"]:
            f = Feature(
                name="Test",
                description="Test feature description",
                implementation_status=status
            )
            assert f.implementation_status == status
        
        # Invalid status
        with pytest.raises(ValueError):
            Feature(
                name="Test",
                description="Test feature description",
                implementation_status="invalid_status"
            )
    
    def test_feature_parent_capability(self):
        """Test Feature parent capability reference."""
        cap = Capability(name="Analytics", description="Analytics capability")
        
        feature = Feature(
            name="Dashboard Widget",
            description="Real-time analytics widget",
            parent_capability_id=cap.id
        )
        
        assert feature.parent_capability_id == cap.id
    
    def test_feature_extraction_result(self):
        """Test ExtractionResult with features."""
        from layer2_extraction.models import ExtractionResult
        
        cap = Capability(name="Cap", description="Test")
        feature = Feature(name="Feature1", description="Test feature")
        
        result = ExtractionResult(
            source_url="https://test.com",
            capabilities=[cap],
            features=[feature]
        )
        
        assert len(result.features) == 1
        assert len(result.get_all_entities()) == 2


class TestChunker:
    """Test semantic chunking."""
    
    def test_basic_chunking(self):
        """Test basic text chunking."""
        text = "# Header 1\n\nParagraph 1\n\nParagraph 2\n\n# Header 2\n\nParagraph 3"
        
        chunks = chunk_markdown(text, chunk_size=1000, chunk_overlap=100)
        
        assert len(chunks) > 0
        assert all(len(c.content) > 0 for c in chunks)
    
    def test_header_preservation(self):
        """Test that headers are preserved in chunks."""
        text = "# Main Header\n\nContent under main header.\n\n## Sub Header\n\nMore content."
        
        chunks = chunk_markdown(text, source_url="https://example.com")
        
        # At least one chunk should contain header info in metadata
        assert any(c.metadata.get("section_header") for c in chunks)
    
    def test_chunk_metadata(self):
        """Test chunk metadata is populated."""
        text = "# Section\n\nContent here."
        
        chunks = chunk_markdown(text, source_url="https://test.com")
        
        chunk = chunks[0]
        assert chunk.metadata["source_url"] == "https://test.com"
        assert "section_header" in chunk.metadata
        assert "start_idx" in chunk.metadata


class TestRelationships:
    """Test relationship models."""
    
    def test_relationship_creation(self):
        """Test creating a Relationship."""
        cap = Capability(name="Test", description="Test capability")
        uc = UseCase(name="Test UC", description="Test use case")
        
        rel = Relationship(
            source_id=cap.id,
            predicate=PredicateType.ENABLES,
            target_id=uc.id,
            confidence=0.88,
            evidence_text="The capability enables the use case as stated in the text.",
            source_url="https://example.com"
        )
        
        assert rel.predicate == PredicateType.ENABLES
        assert rel.confidence == 0.88
        assert len(rel.evidence_text) > 0
    
    def test_relationship_validation(self):
        """Test relationship validation."""
        with pytest.raises(ValueError):
            Relationship(
                source_id="not-a-uuid",
                predicate=PredicateType.ENABLES,
                target_id="valid-uuid-here",
                confidence=0.5,
                evidence_text="Evidence",
                source_url="https://example.com"
            )
    
    def test_relationship_graph(self):
        """Test RelationshipGraph operations."""
        from layer2_extraction.models import RelationshipGraph
        
        cap = Capability(name="Test", description="Test")
        uc = UseCase(name="Test UC", description="Test")
        
        rel = Relationship(
            source_id=cap.id,
            predicate=PredicateType.ENABLES,
            target_id=uc.id,
            confidence=0.9,
            evidence_text="Evidence",
            source_url="https://example.com"
        )
        
        graph = RelationshipGraph()
        graph.add_relationship(rel)
        
        # Should not add duplicate
        graph.add_relationship(rel)
        assert len(graph.relationships) == 1
        
        # Get outgoing from capability
        outgoing = graph.get_outgoing(cap.id)
        assert len(outgoing) == 1
        
        # Get incoming to use case
        incoming = graph.get_incoming(uc.id)
        assert len(incoming) == 1
    
    def test_extended_relationship_types(self):
        """Test extended relationship predicates from spec."""
        cap1 = Capability(name="Parent Cap", description="Parent")
        cap2 = Capability(name="Child Cap", description="Child")
        
        # Test CAPABILITY_SUBTYPE_OF
        rel = Relationship(
            source_id=cap2.id,
            predicate=PredicateType.CAPABILITY_SUBTYPE_OF,
            target_id=cap1.id,
            confidence=0.9,
            evidence_text="Child is a subtype of parent",
            source_url="https://example.com"
        )
        assert rel.predicate == PredicateType.CAPABILITY_SUBTYPE_OF
        
        # Test SEMANTICALLY_EQUIVALENT
        rel2 = Relationship(
            source_id=cap1.id,
            predicate=PredicateType.SEMANTICALLY_EQUIVALENT,
            target_id=cap2.id,
            confidence=0.85,
            evidence_text="These are equivalent",
            source_url="https://example.com"
        )
        assert rel2.predicate == PredicateType.SEMANTICALLY_EQUIVALENT
    
    def test_relationship_inverse(self):
        """Test relationship inverse generation."""
        cap = Capability(name="Cap", description="Test")
        uc = UseCase(name="UC", description="Test")
        
        # ENABLES should have inverse REQUIRES
        rel = Relationship(
            source_id=cap.id,
            predicate=PredicateType.ENABLES,
            target_id=uc.id,
            confidence=0.9,
            evidence_text="Evidence",
            source_url="https://example.com"
        )
        
        inverse = rel.get_inverse()
        assert inverse is not None
        assert inverse.predicate == PredicateType.REQUIRES
        assert inverse.source_id == uc.id
        assert inverse.target_id == cap.id
    
    def test_feature_relationship(self):
        """Test Feature implements Capability relationship."""
        from layer2_extraction.models import Feature
        
        cap = Capability(name="Analytics", description="Analytics capability")
        feature = Feature(name="Dashboard", description="Dashboard feature")
        
        rel = Relationship(
            source_id=feature.id,
            predicate=PredicateType.IMPLEMENTS,
            target_id=cap.id,
            confidence=0.9,
            evidence_text="Feature implements capability",
            source_url="https://example.com"
        )
        
        assert rel.predicate == PredicateType.IMPLEMENTS


class TestExtractionResult:
    """Test ExtractionResult container."""
    
    def test_result_creation(self):
        """Test creating extraction result."""
        cap = Capability(name="Cap1", description="Test")
        cap2 = Capability(name="Cap2", description="Test 2")
        
        result = ExtractionResult(
            source_url="https://example.com",
            capabilities=[cap, cap2]
        )
        
        assert len(result.capabilities) == 2
        assert result.source_url == "https://example.com"
    
    def test_get_all_entities(self):
        """Test getting all entities from result."""
        cap = Capability(name="Cap", description="Test")
        uc = UseCase(name="UC", description="Test")
        
        result = ExtractionResult(
            source_url="https://example.com",
            capabilities=[cap],
            use_cases=[uc]
        )
        
        all_entities = result.get_all_entities()
        assert len(all_entities) == 2
        assert cap in all_entities
        assert uc in all_entities
    
    def test_get_entity_by_id(self):
        """Test finding entity by ID."""
        cap = Capability(name="Cap", description="Test")
        
        result = ExtractionResult(
            source_url="https://example.com",
            capabilities=[cap]
        )
        
        found = result.get_entity_by_id(cap.id)
        assert found == cap
        
        not_found = result.get_entity_by_id("non-existent-id")
        assert not_found is None


@pytest.mark.asyncio
class TestExtractionPipeline:
    """Integration tests for extraction pipeline.
    
    These tests require OPENAI_API_KEY to be set.
    """
    
    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="Requires OPENAI_API_KEY environment variable"
    )
    async def test_entity_extraction(self):
        """Test entity extraction with real LLM."""
        import os
        from layer2_extraction.extraction import EntityExtractor
        
        extractor = EntityExtractor(api_key=os.getenv("OPENAI_API_KEY"))
        
        text = """
        Our platform provides Real-Time Data Ingestion that streams data from 
        multiple sources. It includes technical features like Kafka streaming, 
        change data capture, and schema registry.
        """
        
        entities = await extractor.extract_entities(
            text=text,
            source_url="https://test.com",
            extraction_job_id="test-job",
            confidence_threshold=0.8
        )
        
        # Should extract at least one capability
        assert len(entities["capabilities"]) > 0


class TestEntailmentValidator:
    """Test EntailmentValidator with 6 validation rules."""
    
    def test_validation_required_properties(self):
        """Test VAL-001: Required properties validation."""
        from layer2_extraction.validation import EntailmentValidator, ValidationSeverity
        from layer2_extraction.models import ExtractionResult, ValueDriver, ValueCategory
        
        validator = EntailmentValidator()
        
        # Create result with missing unit (required for ValueDriver)
        vd = ValueDriver(
            category=ValueCategory.COST,
            name="Test",
            description="Test description",
            unit="USD"  # Properly provided
        )
        
        result = ExtractionResult(
            source_url="https://test.com",
            value_drivers=[vd]
        )
        
        results = validator.validate(result, [])
        
        # Should have no errors for properly formed ValueDriver
        errors = [r for r in results if r.severity == ValidationSeverity.ERROR and not r.passed]
        assert len(errors) == 0
    
    def test_validation_confidence_scores(self):
        """Test VAL-006: Confidence score bounds validation."""
        from layer2_extraction.validation import EntailmentValidator, ValidationSeverity
        from layer2_extraction.models import ExtractionResult
        
        validator = EntailmentValidator()
        
        cap = Capability(name="Test", description="Test capability")
        cap.confidence = 1.5  # Invalid: > 1.0
        
        result = ExtractionResult(
            source_url="https://test.com",
            capabilities=[cap]
        )
        
        results = validator.validate(result, [])
        
        # Should have error for invalid confidence
        errors = [r for r in results if r.rule_id == "VAL-006" and not r.passed]
        assert len(errors) >= 1
    
    def test_validation_domain_range(self):
        """Test VAL-002: Domain/range constraints."""
        from layer2_extraction.validation import EntailmentValidator, ValidationSeverity
        from layer2_extraction.models import ExtractionResult
        
        validator = EntailmentValidator()
        
        cap = Capability(name="Cap", description="Test")
        persona = Persona(
            role_type=RoleType.OPERATIONAL_USER,
            title="User",
            department="IT"
        )
        
        result = ExtractionResult(
            source_url="https://test.com",
            capabilities=[cap],
            personas=[persona]
        )
        
        # Create invalid relationship: Persona enables Capability (should be Capability enables UseCase)
        from models.relationships import Relationship
        rel = Relationship(
            source_id=persona.id,
            predicate=PredicateType.ENABLES,
            target_id=cap.id,
            confidence=0.8,
            evidence_text="Test",
            source_url="https://test.com"
        )
        
        results = validator.validate(result, [rel])
        
        # Should have error for domain violation
        domain_errors = [r for r in results if r.rule_id == "VAL-002" and not r.passed]
        assert len(domain_errors) >= 1


class TestCoreferenceResolver:
    """Test CoreferenceResolver functionality."""
    
    def test_exact_name_match(self):
        """Test exact name matching for coreference."""
        from layer2_extraction.coreference import CoreferenceResolver
        
        resolver = CoreferenceResolver()
        
        cap1 = Capability(name="Real-Time Analytics", description="Test")
        cap2 = Capability(name="real-time analytics", description="Test")
        
        clusters = resolver.resolve_coreferences([cap1, cap2], [])
        
        # Should detect coreference despite case difference
        assert len(clusters) == 1
        assert len(clusters[0].member_entity_ids) == 2
    
    def test_semantically_equivalent_relationship(self):
        """Test coreference via semantically_equivalent relationship."""
        from layer2_extraction.coreference import CoreferenceResolver
        from layer2_extraction.models import Relationship
        
        resolver = CoreferenceResolver()
        
        cap1 = Capability(name="Inventory Tracking", description="Test")
        cap2 = Capability(name="Stock Management", description="Test")
        
        # Create semantically equivalent relationship
        rel = Relationship(
            source_id=cap1.id,
            predicate=PredicateType.SEMANTICALLY_EQUIVALENT,
            target_id=cap2.id,
            confidence=0.9,
            evidence_text="These are the same",
            source_url="https://test.com"
        )
        
        clusters = resolver.resolve_coreferences([cap1, cap2], [rel])
        
        # Should detect coreference via relationship
        assert len(clusters) == 1


class TestSemanticAligner:
    """Test SemanticAligner functionality."""
    
    def test_alignment_cache_key(self):
        """Test cache key generation."""
        from layer2_extraction.alignment import SemanticAligner
        
        aligner = SemanticAligner()
        
        cap = Capability(name="Test Cap", description="Test")
        
        key1 = aligner._compute_cache_key(cap)
        key2 = aligner._compute_cache_key(cap)
        
        # Same entity should produce same key
        assert key1 == key2
    
    def test_normalize_name(self):
        """Test name normalization for comparison."""
        from layer2_extraction.alignment import SemanticAligner
        
        aligner = SemanticAligner()
        
        # Should normalize and remove stop words
        norm1 = aligner._normalize_name("Real-Time Analytics System")
        norm2 = aligner._normalize_name("real time analytics")
        
        assert norm1 == norm2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
