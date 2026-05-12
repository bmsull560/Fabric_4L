"""System routes for Layer 2 API."""

from fastapi import APIRouter, Request
from fastapi.responses import Response

from .. import main as handlers

router = APIRouter(tags=["system"])

SYSTEM_HEALTH_RESPONSES = {
    200: {"description": "Service health payload"},
    503: {"description": "Service unavailable"},
}


def _with_readiness(payload: dict, default_service: str) -> dict:
    status = str(payload.get("status", "unhealthy"))
    payload.setdefault("service", default_service)
    payload["readiness"] = {
        "is_ready": status in {"healthy", "degraded"},
        "reason": "dependencies_available" if status in {"healthy", "degraded"} else "dependencies_unavailable",
    }
    return payload


@router.get("/health", responses=SYSTEM_HEALTH_RESPONSES)
async def health_check():
    payload = await handlers.health_check()
    return _with_readiness(dict(payload), "layer2-extraction")


@router.get("/metrics", tags=["Monitoring"], include_in_schema=False)
async def metrics_endpoint(request: Request):
    result = await handlers.metrics_endpoint(request)
    if isinstance(result, Response):
        return result
    return result
