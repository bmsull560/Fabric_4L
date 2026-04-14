"""Audit routes for Layer 2 API."""

from fastapi import APIRouter, Depends

from .. import main as handlers
from ..deps import RequestContext, require_authenticated

router = APIRouter(prefix="/v1/audit", tags=["audit"])


@router.get("/trace/{job_id}", response_model=handlers.ProvenanceResponse)
async def get_provenance(
    job_id: str,
    ctx: RequestContext = Depends(require_authenticated),
):
    return await handlers.get_provenance(job_id, ctx)


@router.get("/entity/{entity_id}")
async def get_entity_provenance(
    entity_id: str,
    ctx: RequestContext = Depends(require_authenticated),
):
    return await handlers.get_entity_provenance(entity_id, ctx)
