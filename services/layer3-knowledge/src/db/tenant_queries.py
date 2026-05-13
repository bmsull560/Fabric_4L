"""
Tenant-aware Neo4j query helpers.

This module provides helper functions for querying Neo4j with mandatory tenant_id
filtering to prevent cross-tenant data leakage. All functions require an explicit
tenant_id parameter and will raise ValueError if not provided.

Security Model:
- All MATCH clauses include explicit tenant_id predicates
- No fallback to unscoped queries
- Composite constraints on (id, tenant_id) provide defense-in-depth
- Explicit filtering is the primary security control

Usage:
    from db.tenant_queries import get_entity_by_id, get_relationships_for_entity
    
    entity = await get_entity_by_id(session, entity_id="abc123", tenant_id="tenant-1")
    rels = await get_relationships_for_entity(session, entity_id="abc123", tenant_id="tenant-1")
"""

from typing import Any

from neo4j import AsyncSession
from value_fabric.shared.models.typed_dict import TypedDictModel

from schema.constraints import get_relationship_types


class get_entity_contextResult(TypedDictModel):
    center: Any
    neighbors: list[Any]
    relationships: list[Any]

class count_entity_relationshipsResult(TypedDictModel):
    incoming: int
    outgoing: int
    total: int

_ALLOWED_RELATIONSHIP_TYPES = frozenset(get_relationship_types()) | {
    rel.upper() for rel in get_relationship_types()
}


def _validate_relationship_types(relationship_types: list[str] | None) -> list[str]:
    """Validate relationship filters before they reach Cypher."""
    if not relationship_types:
        return []

    invalid = [rel for rel in relationship_types if rel not in _ALLOWED_RELATIONSHIP_TYPES]
    if invalid:
        raise ValueError(f"Invalid relationship type(s): {', '.join(invalid)}")
    return list(dict.fromkeys(relationship_types))


async def get_entity_by_id(
    session: AsyncSession,
    entity_id: str,
    tenant_id: str,
    include_properties: bool = True,
) -> dict[str, Any] | None:
    """
    Retrieve a single entity by ID with mandatory tenant filtering.
    
    Args:
        session: Active Neo4j async session
        entity_id: Entity identifier
        tenant_id: Tenant identifier (required, no default)
        include_properties: Whether to include the properties JSONB field
        
    Returns:
        Entity dict or None if not found
        
    Raises:
        ValueError: If tenant_id is None or empty
        
    Security:
        - Enforces tenant_id in MATCH clause
        - No fallback to unscoped query
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for get_entity_by_id")
    
    if include_properties:
        query = """
            MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
            RETURN e {
                .id, .name, .entity_type, .domain, .status,
                .confidence, .confidence_label, .description,
                .updated_at, .source_name, .extraction_job_id,
                .created_at, .created_by, .properties,
                .validation_errors, .last_validated_at, .tenant_id
            } as entity
        """
    else:
        query = """
            MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
            RETURN e {
                .id, .name, .entity_type, .domain, .status,
                .confidence, .confidence_label, .description,
                .updated_at, .source_name, .extraction_job_id,
                .created_at, .created_by, .tenant_id
            } as entity
        """
    
    result = await session.run(query, {"entity_id": entity_id, "tenant_id": tenant_id})
    record = await result.single()
    
    return record["entity"] if record else None


async def get_relationships_for_entity(
    session: AsyncSession,
    entity_id: str,
    tenant_id: str,
    direction: str = "both",
    limit: int = 100,
) -> dict[str, list[dict[str, Any]]]:
    """
    Retrieve relationships for an entity with mandatory tenant filtering.
    
    Args:
        session: Active Neo4j async session
        entity_id: Entity identifier
        tenant_id: Tenant identifier (required, no default)
        direction: "outgoing", "incoming", or "both"
        limit: Maximum relationships to return per direction
        
    Returns:
        Dict with "outgoing" and "incoming" relationship lists
        
    Raises:
        ValueError: If tenant_id is None or empty, or invalid direction
        
    Security:
        - Both source and target entities must have matching tenant_id
        - No cross-tenant relationship traversal
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for get_relationships_for_entity")
    
    if direction not in ("outgoing", "incoming", "both"):
        raise ValueError(f"Invalid direction: {direction}. Must be 'outgoing', 'incoming', or 'both'")
    
    result = {"outgoing": [], "incoming": []}
    
    if direction in ("outgoing", "both"):
        outgoing_query = """
            MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})-[r]->(target:Entity {tenant_id: $tenant_id})
            RETURN type(r) as rel_type, 
                   target.id as target_id,
                   target.name as target_name, 
                   target.entity_type as target_type,
                   target.confidence as target_confidence
            LIMIT $limit
        """
        outgoing_result = await session.run(
            outgoing_query, 
            {"entity_id": entity_id, "tenant_id": tenant_id, "limit": limit}
        )
        result["outgoing"] = [dict(record) async for record in outgoing_result]
    
    if direction in ("incoming", "both"):
        incoming_query = """
            MATCH (source:Entity {tenant_id: $tenant_id})-[r]->(e:Entity {id: $entity_id, tenant_id: $tenant_id})
            RETURN type(r) as rel_type, 
                   source.id as source_id,
                   source.name as source_name, 
                   source.entity_type as source_type,
                   source.confidence as source_confidence
            LIMIT $limit
        """
        incoming_result = await session.run(
            incoming_query, 
            {"entity_id": entity_id, "tenant_id": tenant_id, "limit": limit}
        )
        result["incoming"] = [dict(record) async for record in incoming_result]
    
    return result


async def search_entities(
    session: AsyncSession,
    tenant_id: str,
    entity_types: list[str] | None = None,
    min_confidence: float = 0.0,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Search entities with mandatory tenant filtering.
    
    Args:
        session: Active Neo4j async session
        tenant_id: Tenant identifier (required, no default)
        entity_types: Optional list of entity types to filter
        min_confidence: Minimum confidence score (0.0 to 1.0)
        limit: Maximum entities to return
        offset: Pagination offset
        
    Returns:
        List of entity dicts
        
    Raises:
        ValueError: If tenant_id is None or empty
        
    Security:
        - All entities must have matching tenant_id
        - No cross-tenant search results
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for search_entities")
    
    # Build type filter
    type_filter = ""
    params: dict[str, Any] = {
        "tenant_id": tenant_id,
        "min_confidence": min_confidence,
        "limit": limit,
        "offset": offset,
    }
    
    if entity_types:
        type_filter = "AND e.entity_type IN $entity_types"
        params["entity_types"] = entity_types
    
    query = f"""
        MATCH (e:Entity {{tenant_id: $tenant_id}})
        WHERE e.confidence >= $min_confidence
        {type_filter}
        RETURN e {{
            .id, .name, .entity_type, .domain, .status,
            .confidence, .confidence_label, .description,
            .created_at, .updated_at, .tenant_id
        }} as entity
        ORDER BY e.confidence DESC, e.created_at DESC
        SKIP $offset
        LIMIT $limit
    """
    
    result = await session.run(query, params)
    return [record["entity"] async for record in result]


async def get_entity_context(
    session: AsyncSession,
    entity_id: str,
    tenant_id: str,
    hops: int = 2,
    min_confidence: float = 0.0,
    relationship_types: list[str] | None = None,
) -> dict[str, Any]:
    """
    Get entity with N-hop neighborhood context, tenant-scoped.
    
    Args:
        session: Active Neo4j async session
        entity_id: Entity identifier
        tenant_id: Tenant identifier (required, no default)
        hops: Number of relationship hops (1-3)
        min_confidence: Minimum confidence for included entities
        relationship_types: Optional list of relationship types to traverse
        
    Returns:
        Dict with center entity, neighbors, and relationships
        
    Raises:
        ValueError: If tenant_id is None or empty, or hops out of range
        
    Security:
        - All nodes in path must have matching tenant_id
        - No cross-tenant graph traversal
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for get_entity_context")
    
    if not (1 <= hops <= 3):
        raise ValueError(f"hops must be between 1 and 3, got {hops}")
    
    # Build relationship type filter
    rel_filter = ""
    params: dict[str, Any] = {
        "entity_id": entity_id,
        "tenant_id": tenant_id,
        "min_confidence": min_confidence,
    }
    
    validated_relationship_types = _validate_relationship_types(relationship_types)
    if validated_relationship_types:
        rel_filter = "AND ALL(r IN relationships(path) WHERE type(r) IN $relationship_types)"
        params["relationship_types"] = validated_relationship_types
    
    query = f"""
        MATCH path = (center {{id: $entity_id, tenant_id: $tenant_id}})-[*1..{hops}]-(connected {{tenant_id: $tenant_id}})
        WHERE ALL(node IN nodes(path) WHERE node.confidence >= $min_confidence)
        {rel_filter}
        WITH center, 
             collect(DISTINCT connected) as neighbors,
             collect(DISTINCT relationships(path)) as all_rels
        RETURN center, neighbors, all_rels
    """
    
    result = await session.run(query, params)
    record = await result.single()
    
    if not record:
        return get_entity_contextResult.model_validate({"center": None, "neighbors": [], "relationships": []})
    
    # Serialize results
    center = dict(record["center"]) if record["center"] else None
    neighbors = [dict(n) for n in record["neighbors"]]
    
    # Flatten relationship lists
    relationships = []
    for rel_list in record["all_rels"]:
        if isinstance(rel_list, list):
            relationships.extend([dict(r) for r in rel_list])
        else:
            relationships.append(dict(rel_list))
    
    return get_entity_contextResult.model_validate({
        "center": center,
        "neighbors": neighbors,
        "relationships": relationships,
    })


async def count_entity_relationships(
    session: AsyncSession,
    entity_id: str,
    tenant_id: str,
) -> dict[str, int]:
    """
    Count outgoing and incoming relationships for an entity.
    
    Args:
        session: Active Neo4j async session
        entity_id: Entity identifier
        tenant_id: Tenant identifier (required, no default)
        
    Returns:
        Dict with "outgoing", "incoming", and "total" counts
        
    Raises:
        ValueError: If tenant_id is None or empty
        
    Security:
        - Only counts relationships where both entities have matching tenant_id
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for count_entity_relationships")
    
    query = """
        MATCH (e:Entity {id: $entity_id, tenant_id: $tenant_id})
        OPTIONAL MATCH (e)-[r1]->(:Entity {tenant_id: $tenant_id})
        OPTIONAL MATCH (e)<-[r2]-(:Entity {tenant_id: $tenant_id})
        RETURN count(r1) as outgoing, count(r2) as incoming
    """
    
    result = await session.run(query, {"entity_id": entity_id, "tenant_id": tenant_id})
    record = await result.single()
    
    if not record:
        return count_entity_relationshipsResult.model_validate({"outgoing": 0, "incoming": 0, "total": 0})
    
    outgoing = record["outgoing"] or 0
    incoming = record["incoming"] or 0
    
    return count_entity_relationshipsResult.model_validate({
        "outgoing": outgoing,
        "incoming": incoming,
        "total": outgoing + incoming,
    })


async def update_entity_properties(
    session: AsyncSession,
    entity_id: str,
    tenant_id: str,
    properties: dict[str, Any],
) -> bool:
    """
    Update entity properties with mandatory tenant filtering.
    
    Args:
        session: Active Neo4j async session
        entity_id: Entity identifier
        tenant_id: Tenant identifier (required, no default)
        properties: Properties to update
        
    Returns:
        True if entity was updated, False if not found
        
    Raises:
        ValueError: If tenant_id is None or empty
        
    Security:
        - Only updates entities with matching tenant_id
        - No cross-tenant updates
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for update_entity_properties")
    
    query = """
        MATCH (n:Entity {id: $entity_id, tenant_id: $tenant_id})
        SET n += $properties, n.updated_at = datetime()
        RETURN n.id as entity_id
    """
    
    result = await session.run(
        query, 
        {"entity_id": entity_id, "tenant_id": tenant_id, "properties": properties}
    )
    record = await result.single()
    
    return record is not None


async def delete_entity(
    session: AsyncSession,
    entity_id: str,
    tenant_id: str,
) -> bool:
    """
    Delete entity and its relationships with mandatory tenant filtering.
    
    Args:
        session: Active Neo4j async session
        entity_id: Entity identifier
        tenant_id: Tenant identifier (required, no default)
        
    Returns:
        True if entity was deleted, False if not found
        
    Raises:
        ValueError: If tenant_id is None or empty
        
    Security:
        - Only deletes entities with matching tenant_id
        - No cross-tenant deletions
    """
    if not tenant_id:
        raise ValueError("tenant_id is required for delete_entity")
    
    query = """
        MATCH (n:Entity {id: $entity_id, tenant_id: $tenant_id})
        DETACH DELETE n
        RETURN count(n) as deleted
    """
    
    result = await session.run(query, {"entity_id": entity_id, "tenant_id": tenant_id})
    record = await result.single()
    
    return record and record["deleted"] > 0
