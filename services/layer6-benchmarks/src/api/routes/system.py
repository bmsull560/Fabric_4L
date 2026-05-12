"""System routes for Layer 6 API."""

from fastapi import APIRouter, Request

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


@router.get("/health", response_model=None, responses=SYSTEM_HEALTH_RESPONSES)
async def health_check(request: Request):
    from .. import main as handlers
    payload = await handlers.health_check(request)
    return _with_readiness(dict(payload), "layer6-benchmarks")
