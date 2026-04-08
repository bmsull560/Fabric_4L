"""Tests for RDF ingestion pipeline."""

import pytest
from rdflib import RDF, Graph, Literal, Namespace, URIRef

from src.ingestion import Neo4jLoader, SyncManager


@pytest.fixture
def sample_rdf_graph():
    """Create a sample RDF graph for testing."""
    g = Graph()
    VF = Namespace("https://valuefabric.io/ontology/")

    # Add sample capability
    cap = URIRef("https://valuefabric.io/entity/cap-1")
    g.add((cap, RDF.type, VF.Capability))
    g.add((cap, VF.name, Literal("Real-Time Data Ingestion")))
    g.add((cap, VF.description, Literal("Stream data with low latency")))
    g.add((cap, VF.confidence, Literal(0.95)))

    # Add sample use case
    uc = URIRef("https://valuefabric.io/entity/uc-1")
    g.add((uc, RDF.type, VF.UseCase))
    g.add((uc, VF.name, Literal("Touchless Accounts Payable")))
    g.add((uc, VF.description, Literal("Automated AP processing")))

    # Add relationship
    g.add((cap, VF.ENABLES, uc))

    return g


@pytest.mark.asyncio
async def test_extract_entities_from_rdf(sample_rdf_graph):
    """Test entity extraction from RDF graph."""
    loader = Neo4jLoader()

    entities = loader._extract_entities_from_rdf(sample_rdf_graph)

    assert "Capability" in entities
    assert "UseCase" in entities
    assert len(entities["Capability"]) == 1
    assert len(entities["UseCase"]) == 1

    cap = entities["Capability"][0]
    assert cap["name"] == "Real-Time Data Ingestion"
    assert cap["confidence"] == 0.95


@pytest.mark.asyncio
async def test_extract_relationships_from_rdf(sample_rdf_graph):
    """Test relationship extraction from RDF graph."""
    loader = Neo4jLoader()

    relationships = loader._extract_relationships_from_rdf(sample_rdf_graph)

    assert len(relationships) == 1
    assert relationships[0]["predicate"] == "ENABLES"
    assert "cap-1" in relationships[0]["source_id"]
    assert "uc-1" in relationships[0]["target_id"]


@pytest.mark.asyncio
async def test_load_turtle_string():
    """Test loading Turtle-formatted RDF."""
    turtle_data = '''
    @prefix vf: <https://valuefabric.io/ontology/> .
    @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

    <https://valuefabric.io/entity/cap-1> a vf:Capability ;
        vf:name "Test Capability" ;
        vf:confidence "0.9"^^xsd:float .
    '''

    loader = Neo4jLoader()

    # This would require a real Neo4j instance
    # For unit tests, we just verify parsing works
    try:
        from rdflib import Graph
        g = Graph()
        g.parse(data=turtle_data, format="turtle")
        assert len(g) > 0
    except Exception as e:
        pytest.fail(f"Turtle parsing failed: {e}")
