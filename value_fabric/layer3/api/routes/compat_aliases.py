<<<<<<< ours
"""Compatibility alias endpoints delegating to canonical route implementations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from value_fabric.shared.identity import RequestContext, require_authenticated

from ..dependencies import get_graph_rag, get_hybrid_search
from ..models import GraphRAGQuery, GraphRAGResponse, SearchRequest, SearchResponse
from . import query_search

router = APIRouter(prefix="/v1", tags=["compatibility"], dependencies=[Depends(require_authenticated)])


@router.post("/graphrag", response_model=GraphRAGResponse)
async def graph_rag_legacy_alias(
    query: GraphRAGQuery,
    request: Request,
    graph_rag=Depends(get_graph_rag),
    ctx: RequestContext = Depends(require_authenticated),
):
    return await query_search.graph_rag_query_impl(query, graph_rag, ctx=ctx, request=request)


@router.post("/query", response_model=GraphRAGResponse)
@router.post("/query/graph", response_model=GraphRAGResponse)
async def graph_rag_query_aliases(
    query: GraphRAGQuery,
    request: Request,
    graph_rag=Depends(get_graph_rag),
    ctx: RequestContext = Depends(require_authenticated),
):
    return await query_search.graph_rag_query_impl(query, graph_rag, ctx=ctx, request=request)


@router.post("/query/graph/stream")
async def graph_rag_query_stream_alias(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    return await query_search.graph_rag_query_stream_impl(query, graph_rag)


@router.post("/search/hybrid", response_model=SearchResponse, deprecated=True)
@router.post("/search", response_model=SearchResponse, deprecated=True)
@router.post("/query/search", response_model=SearchResponse)
async def hybrid_search_aliases(
    request: SearchRequest,
    http_request: Request,
    hybrid_search=Depends(get_hybrid_search),
    ctx: RequestContext = Depends(require_authenticated),
):
    return await query_search.hybrid_search_impl(request, hybrid_search, ctx=ctx, http_request=http_request)
=======
"""Compatibility shim for legacy Layer 3 query/search alias route imports.

Canonical implementation lives in ``value_fabric.layer3.api.routes.query_search``.

Deprecated:
    This shim is temporary for compatibility consumers and is scheduled for
    removal after the v2.7 release window (target: 2026-12-31).
"""

from value_fabric.layer3.api.routes.query_search import router

__all__ = ["router"]
>>>>>>> theirs
