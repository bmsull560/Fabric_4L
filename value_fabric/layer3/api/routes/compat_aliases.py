"""Compatibility alias endpoints delegating to canonical route implementations."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from value_fabric.shared.identity import RequestContext, require_authenticated

from ..dependencies import get_graph_rag, get_hybrid_search
from ..models import GraphRAGQuery, GraphRAGResponse, SearchRequest, SearchResponse
from ..services.compat_metrics import record_deprecated_legacy_field_usage, record_deprecated_route_hit
from . import query_search

router = APIRouter(prefix="/v1", tags=["compatibility"], dependencies=[Depends(require_authenticated)])


<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
def _app_client(request: Request) -> str:
    return request.headers.get("x-app-client", "unknown")
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
def _assert_legacy_alias_enabled(request: Request, alias_name: str) -> None:
    phase = getattr(request.app.state, "layer3_compat_deprecation_phase", "warning_only")
    if phase == "disable_non_prod":
        env = getattr(request.app.state, "environment", "dev")
        if env.lower() != "prod":
            raise HTTPException(status_code=410, detail=f"Legacy alias '{alias_name}' disabled in non-production")
    elif phase == "removed":
        raise HTTPException(status_code=410, detail=f"Legacy alias '{alias_name}' has been removed")
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs


@router.post("/graphrag", response_model=GraphRAGResponse, deprecated=True)
async def graph_rag_legacy_alias(
    query: GraphRAGQuery,
    request: Request,
    graph_rag=Depends(get_graph_rag),
    ctx: RequestContext = Depends(require_authenticated),
):
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
    record_deprecated_route_hit("/v1/graphrag", tenant_id=str(ctx.tenant_id), app_client=_app_client(request))
=======
    _assert_legacy_alias_enabled(request, "/v1/graphrag")
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(request, "/v1/graphrag")
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(request, "/v1/graphrag")
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(request, "/v1/graphrag")
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(request, "/v1/graphrag")
>>>>>>> theirs
    return await query_search.graph_rag_query_impl(query, graph_rag, ctx=ctx, request=request)


@router.post("/query", response_model=GraphRAGResponse, deprecated=True)
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
@router.post("/query/graph", response_model=GraphRAGResponse, deprecated=True)
=======
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
=======
>>>>>>> theirs
@router.post("/query/graph", response_model=GraphRAGResponse)
>>>>>>> theirs
async def graph_rag_query_aliases(
    query: GraphRAGQuery,
    request: Request,
    graph_rag=Depends(get_graph_rag),
    ctx: RequestContext = Depends(require_authenticated),
):
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
    record_deprecated_route_hit("/v1/query", tenant_id=str(ctx.tenant_id), app_client=_app_client(request))
=======
    if request.url.path.endswith("/query"):
        _assert_legacy_alias_enabled(request, "/v1/query")
>>>>>>> theirs
=======
    if request.url.path.endswith("/query"):
        _assert_legacy_alias_enabled(request, "/v1/query")
>>>>>>> theirs
=======
    if request.url.path.endswith("/query"):
        _assert_legacy_alias_enabled(request, "/v1/query")
>>>>>>> theirs
=======
    if request.url.path.endswith("/query"):
        _assert_legacy_alias_enabled(request, "/v1/query")
>>>>>>> theirs
=======
    if request.url.path.endswith("/query"):
        _assert_legacy_alias_enabled(request, "/v1/query")
>>>>>>> theirs
    return await query_search.graph_rag_query_impl(query, graph_rag, ctx=ctx, request=request)


@router.post("/query/graph/stream", deprecated=True)
async def graph_rag_query_stream_alias(
    query: GraphRAGQuery,
    request: Request,
    graph_rag=Depends(get_graph_rag),
    ctx: RequestContext = Depends(require_authenticated),
):
    record_deprecated_route_hit("/v1/query/graph/stream", tenant_id=str(ctx.tenant_id), app_client=_app_client(request))
    return await query_search.graph_rag_query_stream_impl(query, graph_rag)


@router.post("/search/hybrid", response_model=SearchResponse, deprecated=True)
@router.post("/search", response_model=SearchResponse, deprecated=True)
@router.post("/query/search", response_model=SearchResponse, deprecated=True)
async def hybrid_search_aliases(
    request: SearchRequest,
    http_request: Request,
    hybrid_search=Depends(get_hybrid_search),
    ctx: RequestContext = Depends(require_authenticated),
):
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
<<<<<<< ours
    app_client = _app_client(http_request)
    record_deprecated_route_hit("/v1/query/search", tenant_id=str(ctx.tenant_id), app_client=app_client)
    if request.search_type == "fulltext":
        record_deprecated_legacy_field_usage("search_type=fulltext", tenant_id=str(ctx.tenant_id), app_client=app_client)
=======
    _assert_legacy_alias_enabled(http_request, http_request.url.path)
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(http_request, http_request.url.path)
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(http_request, http_request.url.path)
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(http_request, http_request.url.path)
>>>>>>> theirs
=======
    _assert_legacy_alias_enabled(http_request, http_request.url.path)
>>>>>>> theirs
    return await query_search.hybrid_search_impl(request, hybrid_search, ctx=ctx, http_request=http_request)
