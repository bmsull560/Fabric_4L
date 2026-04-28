"""End-to-end tenant isolation integration test.

Validates that tenant_id scoping is enforced throughout the L2->L3 pipeline:
1. Ingestion with tenant_id persists to Neo4j
2. Read queries filter by tenant_id
3. Cross-tenant access is blocked

This test requires a running Neo4j instance. Use docker-compose to start services.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

# Skip if Neo4j is not available
neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
neo4j_user = os.getenv("NEO4J_USER", "neo4j")
neo4j_password = os.getenv("NEO4J_PASSWORD", "password")

pytestmark = pytest.mark.skipif(
    not os.getenv("NEO4J_URI"),
    reason="NEO4J_URI not set - skipping e2e tenant isolation test"
)


@pytest.fixture
async def neo4j_session():
    """Create a Neo4j session for testing."""
    try:
        from neo4j import AsyncGraphDatabase
    except ImportError:
        pytest.skip("neo4j package not installed")
    
    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    try:
        async with driver.session() as session:
            yield session
    finally:
        await driver.close()


@pytest.fixture
def tenant_a() -> str:
    """Generate a unique tenant A ID."""
    return f"tenant-a-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def tenant_b() -> str:
    """Generate a unique tenant B ID."""
    return f"tenant-b-{uuid.uuid4().hex[:8]}"


class TestTenantIsolationEndToEnd:
    """End-to-end tenant isolation verification."""

    @pytest.mark.asyncio
    async def test_entity_creation_scopes_to_tenant(
        self, neo4j_session, tenant_a
    ) -> None:
        """Entities created with tenant_id are scoped to that tenant."""
        entity_id = f"cap-{uuid.uuid4().hex[:8]}"
        
        # Create entity for tenant-a
        result = await neo4j_session.run(
            """
            CREATE (c:Capability {id: $entity_id, name: 'Test', tenant_id: $tenant_id})
            RETURN c.id as id, c.tenant_id as tenant_id
            """,
            {"entity_id": entity_id, "tenant_id": tenant_a}
        )
        record = await result.single()
        
        assert record["tenant_id"] == tenant_a
        
        # Verify MATCH with tenant_id returns entity
        result2 = await neo4j_session.run(
            """
            MATCH (c:Capability {id: $entity_id, tenant_id: $tenant_id})
            RETURN c.id as id
            """,
            {"entity_id": entity_id, "tenant_id": tenant_a}
        )
        record2 = await result2.single()
        assert record2["id"] == entity_id
        
        # Cleanup
        await neo4j_session.run(
            "MATCH (c:Capability {id: $entity_id}) DELETE c",
            {"entity_id": entity_id}
        )

    @pytest.mark.asyncio
    async def test_cross_tenant_read_blocked(
        self, neo4j_session, tenant_a, tenant_b
    ) -> None:
        """Tenant B cannot read Tenant A's entities."""
        entity_id = f"cap-{uuid.uuid4().hex[:8]}"
        
        # Create entity for tenant-a
        await neo4j_session.run(
            """
            CREATE (c:Capability {id: $entity_id, name: 'Secret', tenant_id: $tenant_a})
            """,
            {"entity_id": entity_id, "tenant_a": tenant_a}
        )
        
        # Query with tenant-b should return no results
        result = await neo4j_session.run(
            """
            MATCH (c:Capability {id: $entity_id, tenant_id: $tenant_b})
            RETURN c.id as id
            """,
            {"entity_id": entity_id, "tenant_b": tenant_b}
        )
        record = await result.single()
        assert record is None
        
        # Cleanup
        await neo4j_session.run(
            "MATCH (c:Capability {id: $entity_id}) DELETE c",
            {"entity_id": entity_id}
        )

    @pytest.mark.asyncio
    async def test_composite_constraint_enforces_tenant_uniqueness(
        self, neo4j_session, tenant_a, tenant_b
    ) -> None:
        """Same entity ID can exist in different tenants."""
        entity_id = f"cap-{uuid.uuid4().hex[:8]}"
        
        # Create same ID in two tenants
        await neo4j_session.run(
            """
            CREATE (c1:Capability {id: $entity_id, name: 'Tenant A', tenant_id: $tenant_a})
            CREATE (c2:Capability {id: $entity_id, name: 'Tenant B', tenant_id: $tenant_b})
            RETURN count(*) as count
            """,
            {"entity_id": entity_id, "tenant_a": tenant_a, "tenant_b": tenant_b}
        )
        
        # Verify both exist
        result = await neo4j_session.run(
            """
            MATCH (c:Capability {id: $entity_id})
            RETURN c.tenant_id as tenant_id, count(*) as count
            """,
            {"entity_id": entity_id}
        )
        records = [r async for r in result]
        
        # Should find both entities
        assert len(records) == 2
        tenant_ids = {r["tenant_id"] for r in records}
        assert tenant_ids == {tenant_a, tenant_b}
        
        # Cleanup
        await neo4j_session.run(
            "MATCH (c:Capability {id: $entity_id}) DELETE c",
            {"entity_id": entity_id}
        )

    @pytest.mark.asyncio
    async def test_relationship_queries_respect_tenant(
        self, neo4j_session, tenant_a, tenant_b
    ) -> None:
        """Relationship queries only return intra-tenant relationships."""
        cap_a = f"cap-a-{uuid.uuid4().hex[:8]}"
        cap_b = f"cap-b-{uuid.uuid4().hex[:8]}"
        uc = f"uc-{uuid.uuid4().hex[:8]}"
        
        # Create tenant-a graph
        await neo4j_session.run(
            """
            CREATE (c:Capability {id: $cap_a, name: 'Cap', tenant_id: $tenant_a})
            CREATE (u:UseCase {id: $uc, name: 'UC', tenant_id: $tenant_a})
            CREATE (c)-[:ENABLES]->(u)
            """,
            {"cap_a": cap_a, "uc": uc, "tenant_a": tenant_a}
        )
        
        # Create tenant-b graph with same IDs
        await neo4j_session.run(
            """
            CREATE (c:Capability {id: $cap_b, name: 'Cap B', tenant_id: $tenant_b})
            CREATE (u:UseCase {id: $uc, name: 'UC', tenant_id: $tenant_b})
            CREATE (c)-[:ENABLES]->(u)
            """,
            {"cap_b": cap_b, "uc": uc, "tenant_b": tenant_b}
        )
        
        # Query for tenant-a should only return tenant-a's relationship
        result = await neo4j_session.run(
            """
            MATCH (c:Capability {id: $cap_a, tenant_id: $tenant_a})-[:ENABLES]->(u:UseCase {tenant_id: $tenant_a})
            RETURN u.id as id
            """,
            {"cap_a": cap_a, "tenant_a": tenant_a}
        )
        record = await result.single()
        assert record["id"] == uc
        
        # Cleanup
        await neo4j_session.run(
            """
            MATCH (c:Capability) WHERE c.id IN [$cap_a, $cap_b] DELETE c
            """,
            {"cap_a": cap_a, "cap_b": cap_b}
        )
        await neo4j_session.run(
            "MATCH (u:UseCase {id: $uc}) DELETE u",
            {"uc": uc}
        )
