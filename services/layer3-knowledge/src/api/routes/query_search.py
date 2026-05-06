"""Graph query/search route helpers extracted from Layer 3 monolith.

Migration ledger:
- moved groups: graphrag query aliases, streaming graphrag query, hybrid search execution.
- remaining in app_monolith: decorator compatibility wrappers, deprecation header handling,
  and legacy alias registration.
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from ..cache import get_request_deduplicator
from ..models import GraphRAGQuery, GraphRAGResponse, SearchRequest, SearchResponse, SearchResult, SearchType

logger = logging.getLogger(__name__)


async def _execute_graph_rag_query(
    graph_rag: Any,
    query_text: str,
    entity_type: str | None,
    max_hops: int,
    max_results: int,
) -> GraphRAGResponse:
    start_time = time.time()
    result = await graph_rag.query(
        query_text=query_text,
        entity_type=entity_type,
        max_hops=max_hops,
        max_results=max_results,
    )
    processing_time = (time.time() - start_time) * 1000
    if isinstance(result, dict):
        query_value = result.get("query", query_text)
        entities = result.get("entities", [])
        relationships = result.get("relationships", [])
        context_graph = result.get("context_graph", {})
        confidence_score = result.get("confidence_score", 0.0)
        sources = result.get("sources", [])
        answer = result.get("answer")
    else:
        query_value = result.query
        entities = result.entities
        relationships = result.relationships
        context_graph = result.context_graph
        confidence_score = result.confidence_score
        sources = result.sources
        answer = getattr(result, "answer", None)
    return GraphRAGResponse.model_validate({
        "query": query_value,
        "entities": entities,
        "relationships": relationships,
        "context_graph": context_graph,
        "confidence_score": confidence_score,
        "sources": sources,
        "processing_time_ms": processing_time,
        "answer": answer,
    })


async def graph_rag_query_impl(query: GraphRAGQuery, graph_rag: Any) -> GraphRAGResponse:
    try:
        deduplicator = get_request_deduplicator()
        if deduplicator:
            params = {
                "query": query.query,
                "entity_type": query.entity_type,
                "max_hops": query.max_hops,
                "max_results": query.max_results,
            }
            return await deduplicator.execute(
                operation="graph_rag_query",
                params=params,
                executor=_execute_graph_rag_query,
                ttl=60,
                graph_rag=graph_rag,
                query_text=query.query,
                entity_type=query.entity_type,
                max_hops=query.max_hops,
                max_results=query.max_results,
            )
        return await _execute_graph_rag_query(
            graph_rag, query.query, query.entity_type, query.max_hops, query.max_results
        )
    except Exception as exc:
        logger.error("GraphRAG query failed: %s", exc)
        raise HTTPException(status_code=500, detail="Query processing failed. Please try again later.")


async def graph_rag_query_stream_impl(query: GraphRAGQuery, graph_rag: Any) -> StreamingResponse:
    async def event_generator() -> Any:
        try:
            async for event in graph_rag.query_stream(
                query_text=query.query,
                entity_type=query.entity_type,
                max_hops=query.max_hops,
                max_results=query.max_results,
            ):
                event_data = {
                    "event_type": event["event_type"],
                    "data": event["data"],
                    "timestamp": datetime.utcnow().isoformat(),
                    "progress_percent": event.get("progress_percent", 0.0),
                }
                yield f"data: {json.dumps(event_data)}\\n\\n"
        except Exception as exc:
            logger.error("Streaming GraphRAG query failed: %s", exc)
            error_event = {
                "event_type": "error",
                "data": {"message": str(exc)},
                "timestamp": datetime.utcnow().isoformat(),
                "progress_percent": 100.0,
            }
            yield f"data: {json.dumps(error_event)}\\n\\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


async def _execute_hybrid_search(
    hybrid_search: Any,
    query: str,
    entity_type: str | None,
    search_type: SearchType | str,
    top_k: int,
    weights: dict | None,
) -> SearchResponse:
    start_time = time.time()
    search_type_value = search_type.value if isinstance(search_type, SearchType) else search_type
    if search_type_value == "vector":
        results = await hybrid_search.semantic_search(query, entity_type, top_k)
    elif search_type_value == "fulltext":
        results = await hybrid_search.fulltext_search(query, entity_type, top_k)
    else:
        results = await hybrid_search.search(query, [entity_type] if entity_type else None, top_k, weights)
    search_results = [SearchResult(**asdict(result)) for result in results]
    return SearchResponse.model_validate({
        "query": query,
        "results": search_results,
        "total_results": len(search_results),
        "search_type": SearchType(search_type_value),
        "processing_time_ms": (time.time() - start_time) * 1000,
    })


async def hybrid_search_impl(request: SearchRequest, hybrid_search: Any) -> SearchResponse:
    try:
        deduplicator = get_request_deduplicator()
        if deduplicator:
            params = {
                "query": request.query,
                "entity_type": request.entity_type,
                "search_type": request.search_type,
                "top_k": request.top_k,
                "weights": request.weights,
            }
            return await deduplicator.execute(
                operation="hybrid_search",
                params=params,
                executor=_execute_hybrid_search,
                ttl=30,
                hybrid_search=hybrid_search,
                query=request.query,
                entity_type=request.entity_type,
                search_type=request.search_type,
                top_k=request.top_k,
                weights=request.weights,
            )
        return await _execute_hybrid_search(
            hybrid_search,
            request.query,
            request.entity_type,
            request.search_type,
            request.top_k,
            request.weights,
        )
    except Exception as exc:
        logger.error("Search failed: %s", exc)
        raise HTTPException(status_code=500, detail="Search failed. Please try again later.")
