"""Compatibility alias endpoints delegating to canonical route implementations."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..dependencies import get_graph_rag, get_hybrid_search
from ..models import GraphRAGQuery, GraphRAGResponse, SearchRequest, SearchResponse
from . import query_search

router = APIRouter(prefix="/v1", tags=["compatibility"])


@router.post("/graphrag", response_model=GraphRAGResponse)
async def graph_rag_legacy_alias(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    return await query_search.graph_rag_query_impl(query, graph_rag)


@router.post("/query", response_model=GraphRAGResponse)
@router.post("/query/graph", response_model=GraphRAGResponse)
async def graph_rag_query_aliases(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    return await query_search.graph_rag_query_impl(query, graph_rag)


@router.post("/query/graph/stream")
async def graph_rag_query_stream_alias(
    query: GraphRAGQuery,
    graph_rag=Depends(get_graph_rag),
):
    return await query_search.graph_rag_query_stream_impl(query, graph_rag)


@router.post("/search/hybrid", response_model=SearchResponse, deprecated=True)
@router.post("/search", response_model=SearchResponse, deprecated=True)
async def hybrid_search_aliases(
    request: SearchRequest,
    hybrid_search=Depends(get_hybrid_search),
):
    return await query_search.hybrid_search_impl(request, hybrid_search)
