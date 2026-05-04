"""Entity API routes - Canonical Entity Browser endpoints.

This module provides the canonical entity browser API as specified in
the Value Fabric API contract. It exposes endpoints for:
- Listing entities with filtering and search
- Getting detailed entity information
- Querying entities with Cypher-like filters

These endpoints have been refactored from main.py as part of the
architectural decomposition effort (Weakness #3).
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from value_fabric.shared.identity import RequestContext, require_authenticated

from ...logging_config import get_logger
from ..dependencies import (
    AppState,
    get_app_state,
    get_graph_rag,
    get_neo4j_driver,
)
from ..models import (
    EntityDetail,
    EntityFilterRequest,
    EntityListResponse,
    EntitySummary,
    ValueTreeResponse,
    ValueTreeTraversal,
)

router = APIRouter(prefix="/v1", tags=["Entities"], dependencies=[Depends(require_authenticated)])
logger = get_logger(__name__)


@router.get("/entities", response_model=EntityListResponse)
async def list_entities(
    search_text: str | None = Query(None, max_length=200, description="Search across name and description"),
    entity_types: list[str] | None = Query(None, description="Filter by entity types"),
    confidence_min: float = Query(0.0, ge=0.0, le=1.0, description="Minimum confidence score"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    sort_by: str = Query("confidence", description="Sort field: confidence, name, created_at"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    _ctx: RequestContext = Depends(require_authenticated),
    neo4j_driver=Depends(get_neo4j_driver),
) -> EntityListResponse:
    """List entities with optional filtering and pagination.

    This is the canonical entity browser endpoint per the Value Fabric API spec.
    Returns high-quality entity summaries with consistent field naming.
    """
    try:
        # Build the Cypher query with filters
        where_clauses = []
        params: dict[str, Any] = {}

        if search_text:
            where_clauses.append(
                "(toLower(e.name) CONTAINS toLower($search_text) OR "
                "toLower(e.description) CONTAINS toLower($search_text))"
            )
            params["search_text"] = search_text

        if entity_types:
            where_clauses.append("e.entity_type IN $entity_types")
            params["entity_types"] = entity_types

        if confidence_min > 0:
            where_clauses.append("e.confidence_score >= $confidence_min")
            params["confidence_min"] = confidence_min

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Validate sort parameters
        valid_sort_fields = {"confidence": "e.confidence_score", "name": "e.name", "created_at": "e.created_at"}
        sort_field = valid_sort_fields.get(sort_by, "e.confidence_score")
        sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"

        # Single query: count and paginated data in one round-trip.
        # The CALL {} subquery is evaluated independently; the outer MATCH
        # returns paginated rows each carrying the pre-computed total.
        params["offset"] = offset
        params["limit"] = limit
        combined_query = f"""
            CALL {{
                MATCH (e:Entity)
                WHERE {where_clause}
                RETURN count(e) as total
            }}
            MATCH (e:Entity)
            WHERE {where_clause}
            RETURN e.id as id,
                   e.name as name,
                   e.description as description,
                   e.entity_type as entity_type,
                   e.confidence_score as confidence_score,
                   e.created_at as created_at,
                   total
            ORDER BY {sort_field} {sort_direction}
            SKIP $offset
            LIMIT $limit
        """

        results = await neo4j_driver.execute_query(combined_query, params)
        total = results[0]["total"] if results else 0

        entities = [
            EntitySummary(
                id=row["id"],
                name=row["name"] or "Unnamed Entity",
                description=row["description"],
                entity_type=row["entity_type"],
                confidence_score=row["confidence_score"] or 0.0,
                created_at=row["created_at"],
            )
            for row in results
        ]

        return EntityListResponse(
            entities=entities,
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + len(entities)) < total,
        )

    except Exception as e:
        logger.error("Entity listing failed: %s", e)
        raise HTTPException(status_code=500, detail="Entity listing failed. Please try again later.")


@router.get("/entities/{entity_id}", response_model=EntityDetail)
async def get_entity_detail(
    entity_id: str,
    include_provenance: bool = Query(True, description="Include provenance chain"),
    include_relationships: bool = Query(True, description="Include related entities"),
    _ctx: RequestContext = Depends(require_authenticated),
    neo4j_driver=Depends(get_neo4j_driver),
    app_state: AppState = Depends(get_app_state),
) -> EntityDetail:
    """Get detailed information about a specific entity.

    Returns complete entity details including properties, provenance,
    and optionally related entities and their relationships.
    """
    try:
        # Get entity node
        entity_query = """
            MATCH (e:Entity {id: $entity_id})
            RETURN e
        """
        entity_result = await neo4j_driver.execute_query(entity_query, {"entity_id": entity_id})

        if not entity_result:
            raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")

        entity_node = entity_result[0]["e"]

        # Get properties
        properties = dict(entity_node)

        # Get provenance if requested
        provenance = None
        if include_provenance:
            prov_query = """
                MATCH (e:Entity {id: $entity_id})-[:DERIVED_FROM]->(source:Source)
                RETURN source
            """
            prov_result = await neo4j_driver.execute_query(prov_query, {"entity_id": entity_id})
            if prov_result:
                source_node = prov_result[0]["source"]
                provenance = {
                    "source_id": source_node.get("id"),
                    "source_type": source_node.get("source_type"),
                    "extraction_method": source_node.get("extraction_method"),
                    "extracted_at": source_node.get("extracted_at"),
                    "confidence": source_node.get("confidence_score"),
                }

        # Get relationships if requested
        relationships = []
        if include_relationships:
            rel_query = """
                MATCH (e:Entity {id: $entity_id})-[r]-(other:Entity)
                RETURN other.id as related_id,
                       other.name as related_name,
                       other.entity_type as related_type,
                       type(r) as relationship_type,
                       r.confidence_score as rel_confidence
                LIMIT 20
            """
            rel_results = await neo4j_driver.execute_query(rel_query, {"entity_id": entity_id})
            relationships = [
                {
                    "entity_id": row["related_id"],
                    "name": row["related_name"],
                    "entity_type": row["related_type"],
                    "relationship": row["relationship_type"],
                    "confidence": row["rel_confidence"] or 0.0,
                }
                for row in rel_results
            ]

        return EntityDetail(
            id=entity_id,
            name=entity_node.get("name", "Unnamed Entity"),
            description=entity_node.get("description"),
            entity_type=entity_node.get("entity_type", "unknown"),
            confidence_score=entity_node.get("confidence_score", 0.0),
            properties=properties,
            provenance=provenance,
            related_entities=relationships,
            created_at=entity_node.get("created_at"),
            updated_at=entity_node.get("updated_at"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Entity detail retrieval failed for %s: %s", entity_id, e)
        raise HTTPException(status_code=500, detail="Entity detail retrieval failed. Please try again later.")


@router.post("/entities/query", response_model=EntityListResponse)
async def query_entities(
    request: EntityFilterRequest,
    _ctx: RequestContext = Depends(require_authenticated),
    neo4j_driver=Depends(get_neo4j_driver),
) -> EntityListResponse:
    """Query entities using Cypher-like filter conditions.

    Supports complex filtering with multiple conditions, logical operators,
    and custom sorting.
    """
    try:
        # Build WHERE clause from filters
        where_clauses = []
        params: dict[str, Any] = {"limit": request.limit or 20, "offset": request.offset or 0}

        if request.entity_types:
            where_clauses.append("e.entity_type IN $entity_types")
            params["entity_types"] = request.entity_types

        if request.confidence_min is not None:
            where_clauses.append("e.confidence_score >= $confidence_min")
            params["confidence_min"] = request.confidence_min

        if request.confidence_max is not None:
            where_clauses.append("e.confidence_score <= $confidence_max")
            params["confidence_max"] = request.confidence_max

        where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Execute query
        query_cypher = f"""
            MATCH (e:Entity)
            WHERE {where_clause}
            RETURN e.id as id,
                   e.name as name,
                   e.description as description,
                   e.entity_type as entity_type,
                   e.confidence_score as confidence_score,
                   e.created_at as created_at
            ORDER BY e.confidence_score DESC
            SKIP $offset
            LIMIT $limit
        """

        results = await neo4j_driver.execute_query(query_cypher, params)

        entities = [
            EntitySummary(
                id=row["id"],
                name=row["name"] or "Unnamed Entity",
                description=row["description"],
                entity_type=row["entity_type"],
                confidence_score=row["confidence_score"] or 0.0,
                created_at=row["created_at"],
            )
            for row in results
        ]

        return EntityListResponse(
            entities=entities,
            total=len(entities),  # Simplified; should use count query
            limit=request.limit or 20,
            offset=request.offset or 0,
            has_more=len(entities) == (request.limit or 20),
        )

    except Exception as e:
        logger.error("Entity query failed: %s", e)
        raise HTTPException(status_code=500, detail="Entity query failed. Please try again later.")


@router.post("/entity/traverse", response_model=ValueTreeResponse)
async def traverse_value_tree(
    request: ValueTreeTraversal,
    _ctx: RequestContext = Depends(require_authenticated),
    graph_rag=Depends(get_graph_rag),
) -> ValueTreeResponse:
    """Traverse the value tree starting from a root entity.

    Performs graph traversal to find value-related entities and their
    relationships, returning a structured tree representation.
    """
    try:
        result = await graph_rag.traverse_value_tree(
            root_entity_id=request.root_entity_id,
            max_depth=request.max_depth,
            relationship_types=request.relationship_types,
        )

        return ValueTreeResponse(
            root_id=request.root_entity_id,
            tree_data=result.get("tree_data", {}),
            entities=result.get("entities", []),
            total_value=result.get("total_value"),
        )

    except Exception as e:
        logger.error("Value tree traversal failed for %s: %s", request.root_entity_id, e)
        raise HTTPException(status_code=500, detail="Value tree traversal failed. Please try again later.")
