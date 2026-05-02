"""System routes for Layer 6 API."""

from fastapi import APIRouter, Request

router = APIRouter(tags=["system"])


@router.get("/health", response_model=None)
async def health_check(request: Request):
    from .. import main as handlers
    return await handlers.health_check(request)
