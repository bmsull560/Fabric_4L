"""System routes for Layer 6 API."""

from fastapi import APIRouter, Request

from .. import main as handlers

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check(request: Request | None = None):
    return await handlers.health_check(request)
