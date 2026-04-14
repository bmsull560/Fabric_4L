"""System routes for Layer 2 API."""

from fastapi import APIRouter, Request
from fastapi.responses import Response

from .. import main as handlers

router = APIRouter(tags=["system"])


@router.get("/health")
async def health_check():
    return await handlers.health_check()


@router.get("/metrics")
async def metrics_endpoint(request: Request):
    result = await handlers.metrics_endpoint(request)
    if isinstance(result, Response):
        return result
    return result
