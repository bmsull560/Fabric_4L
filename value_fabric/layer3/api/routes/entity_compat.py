<<<<<<< ours
"""Compatibility implementations extracted from app_monolith entity endpoints.

These functions contain the former monolith business logic so app_monolith
handlers can remain thin backward-compatibility shims.
"""

from datetime import datetime
from typing import Any

from fastapi import HTTPException

from ...logging_config import get_logger
from ..models import (
    EntityContextResponse,
    EntityDetail,
    EntityFilterRequest,
    EntityListResponse,
    EntityRelationships,
    EntitySummary,
    RelationshipPreview,
    ValueTreeResponse,
    ValueTreeTraversal,
)

logger = get_logger(__name__)


async def get_entity_context_impl(entity_id: str, hops: int, relationship_types: list[str] | None, fields: str | None, cursor: str | None, limit: int, graph_rag: Any) -> EntityContextResponse:
    context = await graph_rag.get_entity_context(entity_id=entity_id, hops=hops, relationship_types=relationship_types)
    if not context["center"]:
        raise HTTPException(status_code=404, detail=f"Entity {entity_id} not found")
    if fields:
        field_list = [f.strip() for f in fields.split(",")]
        center = {k: v for k, v in context["center"].items() if k in field_list or k == "id"}
        neighbors = [{k: v for k, v in n.items() if k in field_list or k == "id"} for n in context["neighbors"]]
        relationships = [{k: v for k, v in r.items() if k in field_list or k in ["source", "target", "type"]} for r in context["relationships"]]
    else:
        center = context["center"]
        neighbors = context["neighbors"]
        relationships = context["relationships"]

    pagination_info = None
    if cursor or len(neighbors) > limit:
        offset = int(cursor) if cursor and cursor.isdigit() else 0
        total_neighbors = len(neighbors)
        paginated_neighbors = neighbors[offset : offset + limit]
        has_more = (offset + limit) < total_neighbors
        pagination_info = {
            "returned_count": len(paginated_neighbors),
            "total_neighbors": total_neighbors,
            "has_more": has_more,
            "next_cursor": str(offset + limit) if has_more else None,
        }
        neighbors = paginated_neighbors
    return EntityContextResponse(entity_id=entity_id, center=center, neighbors=neighbors, relationships=relationships, entity_count=context["entity_count"], relationship_count=context["relationship_count"], pagination=pagination_info)


async def traverse_value_tree_impl(request: ValueTreeTraversal, graph_rag: Any) -> ValueTreeResponse:
    result = await graph_rag.traverse_value_tree(start_entity_id=request.entity_id, direction=request.direction)
    return ValueTreeResponse(start_entity_id=result["start_entity_id"], direction=result["direction"], paths=result["paths"], path_count=result["path_count"])


async def list_entities_impl(request: Any, search_text: str | None, entity_types: list[str] | None, domains: list[str] | None, statuses: list[str] | None, min_confidence: float | None, max_confidence: float | None, limit: int, offset: int, sort_by: str, sort_order: str, neo4j_driver: Any, extract_tenant_id: Any) -> EntityListResponse:
    tenant_id = extract_tenant_id(request)
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required for entity listing")
    where_clauses = ["e.tenant_id = $tenant_id"]
    params: dict[str, Any] = {"tenant_id": tenant_id}
    if search_text:
        where_clauses.append("(toLower(e.name) CONTAINS toLower($search_text) OR toLower(e.description) CONTAINS toLower($search_text))")
        params["search_text"] = search_text
    if entity_types:
        where_clauses.append("e.entity_type IN $entity_types")
        params["entity_types"] = entity_types
    if domains:
        where_clauses.append("e.domain IN $domains")
        params["domains"] = domains
    if statuses:
        where_clauses.append("e.status IN $statuses")
        params["statuses"] = statuses
    if min_confidence is not None:
        where_clauses.append("e.confidence >= $min_confidence")
        params["min_confidence"] = min_confidence
    if max_confidence is not None:
        where_clauses.append("e.confidence <= $max_confidence")
        params["max_confidence"] = max_confidence
    where_clause = "WHERE " + " AND ".join(where_clauses)
    valid_sort_fields = {"name", "updated_at", "confidence", "entity_type", "status", "created_at"}
    if sort_by not in valid_sort_fields:
        sort_by = "updated_at"
    sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
    # strict-scoped-query-execution: Entity listing predicates always include e.tenant_id = $tenant_id.
    count_query = f"""MATCH (e:Entity) {where_clause} RETURN count(e) as total"""
    async with neo4j_driver.session() as session:
        count_result = await session.run(count_query, params)
        total_count_record = await count_result.single()
        total_count = total_count_record["total"] if total_count_record else 0
        # strict-scoped-query-execution: Entity listing predicates always include e.tenant_id = $tenant_id.
        entity_query = f"""MATCH (e:Entity) {where_clause} RETURN e {{.id,.name,.entity_type,.domain,.status,.confidence,.confidence_label,.description,.updated_at,.source_name,.extraction_job_id,.created_at,.created_by}} ORDER BY e.{sort_by} {sort_direction} SKIP $offset LIMIT $limit"""
        params["offset"] = offset
        params["limit"] = limit
        result = await session.run(entity_query, params)
        records = await result.fetch()
        summaries = []
        for record in records:
            node = record["e"]
            confidence = node.get("confidence", 0.0)
            status = node.get("status") or ("validated" if confidence >= 0.9 else "pending" if confidence >= 0.7 else "draft")
            confidence_label = node.get("confidence_label") or ("high" if confidence >= 0.9 else "medium" if confidence >= 0.7 else "low")
            summaries.append(EntitySummary(id=node.get("id", "unknown"), name=node.get("name", "Unknown"), entity_type=node.get("entity_type", "Capability"), domain=node.get("domain"), status=status, confidence=confidence, confidence_label=confidence_label, description=node.get("description"), updated_at=node.get("updated_at") or datetime.utcnow(), source_name=node.get("source_name"), extraction_job_id=node.get("extraction_job_id")))
        available_domains: list[str] = []
        available_sources: list[str] = []
    has_more = (offset + len(summaries)) < total_count
    return EntityListResponse(results=summaries, total_count=total_count, filtered_count=total_count, limit=limit, offset=offset, has_more=has_more, available_domains=available_domains, available_sources=available_sources)


async def query_entities_impl(request: EntityFilterRequest, fastapi_request: Any, neo4j_driver: Any, list_entities_callable: Any) -> EntityListResponse:
    return await list_entities_callable(request=fastapi_request, search_text=request.search_text, entity_types=[str(entity_type) for entity_type in request.entity_types] if request.entity_types else None, domains=request.domains, statuses=[str(status) for status in request.statuses] if request.statuses else None, min_confidence=request.min_confidence, max_confidence=request.max_confidence, limit=request.limit, offset=request.offset, sort_by=request.sort_by, sort_order=request.sort_order, neo4j_driver=neo4j_driver)
=======
"""Compatibility shim for legacy Layer 3 entity route imports.

Canonical implementation lives in ``value_fabric.layer3.api.routes.entities``.

Deprecated:
    This shim is temporary for compatibility consumers and is scheduled for
    removal after the v2.7 release window (target: 2026-12-31).
"""

from value_fabric.layer3.api.routes.entities import router

__all__ = ["router"]
>>>>>>> theirs
