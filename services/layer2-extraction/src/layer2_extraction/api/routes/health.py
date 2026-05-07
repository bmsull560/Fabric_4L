"""Health and metrics routes for Layer 2 API."""

from fastapi import APIRouter, Request

from .. import service

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return await service.health_check()


@router.get("/metrics")
async def metrics_endpoint(request: Request):
    return await service.metrics_endpoint(request)
