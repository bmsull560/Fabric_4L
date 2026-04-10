"""End-to-end pipeline test for Layer 3 Knowledge Graph.

This test verifies the complete flow from extraction to query:
1. Start Neo4j in Docker
2. Initialize schema (constraints, indexes, vector)
3. Simulate Layer 2 extraction results (or use real data)
4. Ingest entities/relationships via Layer 3 API
5. Verify data in Neo4j
6. Run GraphRAG queries
7. Run hybrid search

Usage:
    pytest tests/test_e2e_pipeline.py -v

Requirements:
    - Docker running locally
    - Neo4j image available
"""

import asyncio
import os
import time
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from neo4j import AsyncGraphDatabase

# Guard: skip entire module if testcontainers is not installed
try:
    from testcontainers.neo4j import Neo4jContainer  # type: ignore
    HAS_TESTCONTAINERS = True
except ImportError:
    HAS_TESTCONTAINERS = False

from src.api.main import app
from src.api.dependencies import (
    get_graph_rag,
    get_hybrid_search,
    get_schema_initializer,
    get_sync_manager,
)
from src.config import Settings, get_settings
from src.ingestion.neo4j_loader import Neo4jLoader
from src.ingestion.sync_manager import SyncManager
from src.schema.initializer import SchemaInitializer
from src.retrieval.graph_rag import GraphRAGEngine
from src.retrieval.hybrid_search import HybridSearch
from src.retrieval.vector_store import VectorStore

# Skip entire module if testcontainers not installed
pytestmark = pytest.mark.skipif(
    not HAS_TESTCONTAINERS,
    reason="testcontainers not installed - run: pip install testcontainers[neo4j]"
)


# Test configuration
TEST_NEO4J_PASSWORD = "test-password"
TEST_EMBEDDING_DIMENSION = 384
REQUIRED_VECTOR_INDEXES = {
    "capability_embedding_idx",
    "usecase_embedding_idx",
    "persona_embedding_idx",
    "valuedriver_embedding_idx",
}


@pytest_asyncio.fixture(scope="module")
async def neo4j_container() -> AsyncGenerator[Neo4jContainer, None]:
    """Start Neo4j container for testing."""
    container = Neo4jContainer(
        image="neo4j:5.15-community",
        password=TEST_NEO4J_PASSWORD,
    ).with_env("NEO4J_PLUGINS", '["apoc", "graph-data-science"]')
    
    container.start()
    
    # Wait for Neo4j to be ready
    max_retries = 30
    for i in range(max_retries):
        try:
            driver = AsyncGraphDatabase.driver(
                container.get_connection_url(),
                auth=("neo4j", TEST_NEO4J_PASSWORD),
            )
            await driver.verify_connectivity()
            await driver.close()
            break
        except Exception:
            if i == max_retries - 1:
                container.stop()
                raise RuntimeError("Neo4j failed to start")
            await asyncio.sleep(1)
    
    yield container
    
    # Cleanup
    container.stop()


@pytest_asyncio.fixture
async def neo4j_driver(neo4j_container: Neo4jContainer) -> AsyncGenerator:
    """Provide Neo4j async driver."""
    driver = AsyncGraphDatabase.driver(
        neo4j_container.get_connection_url(),
        auth=("neo4j", TEST_NEO4J_PASSWORD),
    )
    
    yield driver
    
    await driver.close()


@pytest_asyncio.fixture
async def settings(neo4j_container: Neo4jContainer) -> Settings:
    """Create test settings with Neo4j connection."""
    return Settings(
        neo4j_uri=neo4j_container.get_connection_url(),
        neo4j_user="neo4j",
        neo4j_password=TEST_NEO4J_PASSWORD,
        neo4j_database="neo4j",
        neo4j_max_pool_size=10,
        embedding_dimension=TEST_EMBEDDING_DIMENSION,
    )


@pytest_asyncio.fixture
async def schema_initializer(
    neo4j_driver,
    settings: Settings,
) -> SchemaInitializer:
    """Provide schema initializer."""
    return SchemaInitializer(driver=neo4j_driver, settings=settings)


@pytest_asyncio.fixture
async def initialized_schema(schema_initializer: SchemaInitializer) -> None:
    """Initialize schema before tests."""
    await schema_initializer.initialize_schema(drop_existing=True)


@pytest_asyncio.fixture
async def neo4j_loader(
    neo4j_driver,
    settings: Settings,
) -> Neo4jLoader:
    """Provide Neo4j loader."""
    return Neo4jLoader(driver=neo4j_driver, settings=settings)


@pytest.mark.asyncio
class TestSchemaInitialization:
    """Test Neo4j schema initialization."""
    
    async def test_initialize_schema(
        self,
        schema_initializer: SchemaInitializer,
        neo4j_driver,
    ):
        """Test schema initialization creates constraints and indexes."""
        # Initialize schema
        await schema_initializer.initialize_schema(drop_existing=True)
        
        # Verify constraints exist
        async with neo4j_driver.session() as session:
            result = await session.run(
                "SHOW CONSTRAINTS YIELD name, type RETURN count(*) as count"
            )
            record = await result.single()
            assert record["count"] > 0, "No constraints created"
        
        # Verify indexes exist
        async with neo4j_driver.session() as session:
            result = await session.run(
                "SHOW INDEXES YIELD name, type RETURN count(*) as count"
            )
            record = await result.single()
            assert record["count"] > 0, "No indexes created"

            vector_result = await session.run(
                "SHOW INDEXES YIELD name, type WHERE type = 'VECTOR' RETURN collect(name) AS names"
            )
            vector_record = await vector_result.single()
            vector_names = set(vector_record["names"] if vector_record else [])
            assert REQUIRED_VECTOR_INDEXES.issubset(vector_names)
    
    async def test_idempotent_schema_init(
        self,
        schema_initializer: SchemaInitializer,
    ):
        """Test schema initialization is idempotent."""
        # Run twice - should not error
        await schema_initializer.initialize_schema(drop_existing=False)
        await schema_initializer.initialize_schema(drop_existing=False)
    
    async def test_health_check(
        self,
        schema_initializer: SchemaInitializer,
    ):
        """Test health check returns healthy status."""
        health = await schema_initializer.health_check()
        assert health["status"] == "healthy"
        assert health["database"] == "neo4j"


@pytest.mark.asyncio
class TestEntityIngestion:
    """Test entity ingestion from extraction results."""
    
    async def test_ingest_single_entity(
        self,
        neo4j_loader: Neo4jLoader,
        initialized_schema,
        neo4j_driver,
    ):
        """Test ingesting a single entity."""
        from rdflib import Graph, Namespace, Literal, URIRef
        from rdflib.namespace import RDF, RDFS
        
        VF = Namespace("http://valuefabric.io/ontology/")
        
        # Create minimal RDF graph with one capability
        rdf_graph = Graph()
        rdf_graph.bind("vf", VF)
        
        cap_uri = URIRef("http://valuefabric.io/entity/cap-001")
        rdf_graph.add((cap_uri, RDF.type, VF.Capability))
        rdf_graph.add((cap_uri, VF.id, Literal("cap-001")))
        rdf_graph.add((cap_uri, VF.name, Literal("Real-time Analytics")))
        rdf_graph.add((cap_uri, VF.description, Literal("Process data in real-time")))
        rdf_graph.add((cap_uri, VF.confidence, Literal("0.85")))
        
        # Ingest
        stats = await neo4j_loader.load_rdf_graph(
            rdf_graph=rdf_graph,
            source_id="test-source",
            extraction_job_id="test-job-001",
        )
        
        assert stats["entities_loaded"] >= 1
        
        # Verify in Neo4j
        async with neo4j_driver.session() as session:
            result = await session.run(
                "MATCH (n:Capability {id: 'cap-001'}) "
                "RETURN n.name as name, n.embedding as embedding"
            )
            record = await result.single()
            assert record is not None
            assert record["name"] == "Real-time Analytics"
            assert isinstance(record["embedding"], list)
            assert len(record["embedding"]) > 0
    
    async def test_ingest_with_relationships(
        self,
        neo4j_loader: Neo4jLoader,
        initialized_schema,
        neo4j_driver,
    ):
        """Test ingesting entities with relationships."""
        from rdflib import Graph, Namespace, Literal, URIRef
        from rdflib.namespace import RDF
        
        VF = Namespace("http://valuefabric.io/ontology/")
        
        rdf_graph = Graph()
        rdf_graph.bind("vf", VF)
        
        # Create capability
        cap_uri = URIRef("http://valuefabric.io/entity/cap-002")
        rdf_graph.add((cap_uri, RDF.type, VF.Capability))
        rdf_graph.add((cap_uri, VF.id, Literal("cap-002")))
        rdf_graph.add((cap_uri, VF.name, Literal("AI Prediction")))
        
        # Create use case
        uc_uri = URIRef("http://valuefabric.io/entity/uc-001")
        rdf_graph.add((uc_uri, RDF.type, VF.UseCase))
        rdf_graph.add((uc_uri, VF.id, Literal("uc-001")))
        rdf_graph.add((uc_uri, VF.name, Literal("Demand Forecasting")))
        
        # Create relationship: Capability enables UseCase
        rdf_graph.add((cap_uri, VF.enables, uc_uri))
        
        # Ingest
        stats = await neo4j_loader.load_rdf_graph(
            rdf_graph=rdf_graph,
            source_id="test-source",
            extraction_job_id="test-job-002",
        )
        
        assert stats["entities_loaded"] >= 2
        assert stats["relationships_loaded"] >= 1
        
        # Verify relationship in Neo4j
        async with neo4j_driver.session() as session:
            result = await session.run("""
                MATCH (c:Capability {id: 'cap-002'})-[r:enables]->(u:UseCase {id: 'uc-001'})
                RETURN count(r) as count
            """)
            record = await result.single()
            assert record["count"] == 1


@pytest.mark.asyncio
class TestGraphRAGQueries:
    """Test GraphRAG retrieval."""
    
    async def test_graph_rag_query(
        self,
        neo4j_driver,
        settings: Settings,
        initialized_schema,
    ):
        """Test GraphRAG query execution."""
        # Create test data
        async with neo4j_driver.session() as session:
            await session.run("""
                CREATE (c:Capability {id: 'cap-003', name: 'Data Pipeline', confidence: 0.9})
                CREATE (u:UseCase {id: 'uc-002', name: 'ETL Processing', confidence: 0.85})
                CREATE (c)-[:enables {confidence: 0.9}]->(u)
            """)
        
        # Initialize GraphRAG
        graph_rag = GraphRAGEngine(driver=neo4j_driver, settings=settings)
        
        # Execute query
        result = await graph_rag.query(
            query_text="ETL Processing",
            max_hops=2,
            max_results=5,
        )
        
        assert result is not None
        assert len(result.entities) > 0
    
    async def test_multi_hop_traversal(
        self,
        neo4j_driver,
        settings: Settings,
        initialized_schema,
    ):
        """Test multi-hop graph traversal."""
        # Create chain: Capability -> UseCase -> Persona
        async with neo4j_driver.session() as session:
            await session.run("""
                CREATE (c:Capability {id: 'cap-004', name: 'ML Platform', confidence: 0.9})
                CREATE (u:UseCase {id: 'uc-003', name: 'AutoML', confidence: 0.85})
                CREATE (p:Persona {id: 'pers-001', name: 'Data Scientist', confidence: 0.9})
                CREATE (c)-[:enables {confidence: 0.9}]->(u)
                CREATE (u)-[:involves {confidence: 0.85}]->(p)
            """)
        
        graph_rag = GraphRAGEngine(driver=neo4j_driver, settings=settings)
        
        # Query from Capability to find reachable Persona
        result = await graph_rag.query(
            query_text="ML Platform",
            max_hops=3,
            max_results=10,
        )
        
        assert result is not None
        # Should find at least 3 entities in the chain
        assert len(result.entities) >= 3


@pytest.mark.asyncio
class TestHybridSearch:
    """Test hybrid (vector + graph) search."""
    
    async def test_hybrid_search_basic(
        self,
        neo4j_driver,
        settings: Settings,
        initialized_schema,
    ):
        """Test basic hybrid search functionality."""
        # Create test data with embeddings
        async with neo4j_driver.session() as session:
            await session.run("""
                CREATE (c:Capability {
                    id: 'cap-005',
                    name: 'Stream Processing',
                    description: 'Real-time data stream processing',
                    confidence: 0.9,
                    embedding: range(0, 767)
                })
            """)
        
        # Initialize hybrid search (without vector store - uses Neo4j only)
        hybrid_search = HybridSearch(driver=neo4j_driver, settings=settings)
        
        # Search
        results = await hybrid_search.search(
            query="stream processing",
            limit=5,
        )
        
        # Verify results structure
        assert isinstance(results, list)


@pytest.mark.asyncio
class TestAPIEndpoints:
    """Test Layer 3 API endpoints."""
    
    @pytest_asyncio.fixture
    async def api_client(self) -> AsyncGenerator[AsyncClient, None]:
        """Provide HTTP client for API testing."""
        schema_initializer = AsyncMock()
        schema_initializer.health_check.return_value = {
            "status": "healthy",
            "database": "neo4j",
            "uri": "bolt://localhost:7687",
        }
        schema_initializer.verify_schema.return_value = {
            "constraints": {"expected": 0, "found": 0, "missing": []},
            "indexes": {"expected": 0, "found": 0, "missing": []},
            "valid": True,
        }
        app.dependency_overrides[get_schema_initializer] = lambda: schema_initializer
        transport = ASGITransport(app=app)
        try:
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                yield client
        finally:
            app.dependency_overrides.pop(get_schema_initializer, None)
    
    async def test_health_endpoint(self, api_client: AsyncClient):
        """Test health check endpoint."""
        response = await api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "unhealthy")
    
    async def test_detailed_health_endpoint(self, api_client: AsyncClient):
        """Test detailed health check endpoint."""
        response = await api_client.get("/health/detailed")
        assert response.status_code == 200
        data = response.json()
        assert "dependencies" in data
        assert "schema_status" in data

    async def test_alias_and_legacy_routes_with_real_neo4j(
        self,
        neo4j_driver,
        settings: Settings,
        schema_initializer: SchemaInitializer,
    ):
        """Verify ingest/query/search alias routes and legacy routes against real Neo4j data."""
        await schema_initializer.initialize_schema(drop_existing=True)

        loader = Neo4jLoader(driver=neo4j_driver, settings=settings)
        sync_manager = SyncManager(loader=loader, driver=neo4j_driver, settings=settings)
        vector_store = VectorStore(driver=neo4j_driver, settings=settings)
        graph_rag = GraphRAGEngine(
            driver=neo4j_driver,
            vector_store=vector_store,
            settings=settings,
        )
        hybrid = HybridSearch(
            driver=neo4j_driver,
            vector_store=vector_store,
            graph_engine=graph_rag,
            settings=settings,
        )

        app.dependency_overrides[get_sync_manager] = lambda: sync_manager
        app.dependency_overrides[get_graph_rag] = lambda: graph_rag
        app.dependency_overrides[get_hybrid_search] = lambda: hybrid

        rdf_data = """
            @prefix vf: <http://valuefabric.io/ontology/> .
            @prefix ex: <http://valuefabric.io/entity/> .
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

            ex:cap-alias-001 rdf:type vf:Capability ;
                vf:id "cap-alias-001" ;
                vf:name "Predictive Maintenance" ;
                vf:description "AI-powered equipment monitoring" ;
                vf:confidence "0.90" .

            ex:uc-alias-001 rdf:type vf:UseCase ;
                vf:id "uc-alias-001" ;
                vf:name "Factory Optimization" ;
                vf:description "Optimize factory operations" ;
                vf:confidence "0.88" .

            ex:cap-alias-001 vf:enables ex:uc-alias-001 .
        """

        try:
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                ingest_resp = await client.post(
                    "/v1/ingest",
                    json={
                        "rdf_data": rdf_data,
                        "source_id": "alias-source-001",
                        "extraction_job_id": "alias-job-001",
                    },
                )
                assert ingest_resp.status_code == 200
                ingest_data = ingest_resp.json()
                assert ingest_data["status"] == "success"
                assert ingest_data["entities_loaded"] >= 2

                graph_payload = {
                    "query": "Predictive Maintenance",
                    "max_hops": 2,
                    "top_k": 10,
                }

                alias_query_resp = await client.post("/v1/query/graph", json=graph_payload)
                assert alias_query_resp.status_code == 200
                alias_query_data = alias_query_resp.json()
                assert len(alias_query_data["entities"]) > 0

                legacy_query_resp = await client.post("/v1/query", json=graph_payload)
                assert legacy_query_resp.status_code == 200

                search_payload = {
                    "query": "predictive maintenance",
                    "search_type": "hybrid",
                    "top_k": 5,
                }
                alias_search_resp = await client.post("/v1/search/hybrid", json=search_payload)
                assert alias_search_resp.status_code == 200
                alias_search_data = alias_search_resp.json()
                assert alias_search_data["total_results"] > 0

                legacy_search_resp = await client.post("/v1/search", json=search_payload)
                assert legacy_search_resp.status_code == 200
        finally:
            app.dependency_overrides.clear()


@pytest.mark.asyncio
class TestE2ECompletePipeline:
    """Complete end-to-end pipeline test."""
    
    async def test_full_pipeline(
        self,
        neo4j_driver,
        neo4j_loader: Neo4jLoader,
        settings: Settings,
        schema_initializer: SchemaInitializer,
    ):
        """Test complete extraction → ingestion → query pipeline."""
        # 1. Initialize schema
        await schema_initializer.initialize_schema(drop_existing=True)
        
        # 2. Simulate extraction result (in real scenario, this comes from Layer 2)
        from rdflib import Graph, Namespace, Literal, URIRef
        from rdflib.namespace import RDF
        
        VF = Namespace("http://valuefabric.io/ontology/")
        
        rdf_graph = Graph()
        rdf_graph.bind("vf", VF)
        
        # Create realistic value fabric data
        entities = [
            ("cap-006", "Capability", "Predictive Maintenance", "AI-powered equipment monitoring"),
            ("uc-004", "UseCase", "Factory Optimization", "Optimize factory operations"),
            ("pers-002", "Persona", "Plant Manager", "Manufacturing plant manager"),
            ("vd-001", "ValueDriver", "Cost Reduction", "Reduce maintenance costs"),
        ]
        
        for entity_id, entity_type, name, description in entities:
            uri = URIRef(f"http://valuefabric.io/entity/{entity_id}")
            type_class = getattr(VF, entity_type)
            rdf_graph.add((uri, RDF.type, type_class))
            rdf_graph.add((uri, VF.id, Literal(entity_id)))
            rdf_graph.add((uri, VF.name, Literal(name)))
            rdf_graph.add((uri, VF.description, Literal(description)))
            rdf_graph.add((uri, VF.confidence, Literal("0.85")))
        
        # Add relationships
        cap_uri = URIRef("http://valuefabric.io/entity/cap-006")
        uc_uri = URIRef("http://valuefabric.io/entity/uc-004")
        pers_uri = URIRef("http://valuefabric.io/entity/pers-002")
        vd_uri = URIRef("http://valuefabric.io/entity/vd-001")
        
        rdf_graph.add((cap_uri, VF.enables, uc_uri))
        rdf_graph.add((uc_uri, VF.involves, pers_uri))
        rdf_graph.add((uc_uri, VF.delivers, vd_uri))
        
        # 3. Ingest to Neo4j
        stats = await neo4j_loader.load_rdf_graph(
            rdf_graph=rdf_graph,
            source_id="e2e-test",
            extraction_job_id="e2e-job-001",
        )
        
        assert stats["entities_loaded"] >= 4
        assert stats["relationships_loaded"] >= 3
        
        # 4. Query with GraphRAG
        graph_rag = GraphRAGEngine(driver=neo4j_driver, settings=settings)
        
        result = await graph_rag.query(
            query_text="Predictive Maintenance",
            max_hops=3,
            max_results=10,
        )
        
        # Should find the capability and related entities
        entity_names = [e.get("name", "") for e in result.entities]
        assert "Predictive Maintenance" in entity_names
        
        # 5. Verify data integrity in Neo4j
        async with neo4j_driver.session() as session:
            # Count entities
            result = await session.run(
                "MATCH (n) WHERE n.id STARTS WITH 'cap-' OR n.id STARTS WITH 'uc-' "
                "RETURN count(n) as count"
            )
            record = await result.single()
            assert record["count"] >= 2
            
            # Verify relationships
            result = await session.run(
                "MATCH ()-[r]->() RETURN count(r) as count"
            )
            record = await result.single()
            assert record["count"] >= 3


@pytest.mark.skipif(
    not os.getenv("RUN_INTEGRATION_TESTS"),
    reason="Integration tests require Docker and RUN_INTEGRATION_TESTS env var",
)
class TestIntegrationWithLayer2:
    """Integration tests with Layer 2 extraction."""
    
    # These tests would require Layer 2 to be running
    # They test the actual Layer 2 -> Layer 3 integration
    
    async def test_layer2_to_layer3_integration(self):
        """Test actual Layer 2 extraction → Layer 3 ingestion."""
        # This would call Layer 2 /extract-and-ingest endpoint
        # and verify data appears in Layer 3
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
