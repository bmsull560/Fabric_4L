"""System routes for Layer 6 API."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(tags=["system"])

@router.get("/ready", response_model=None)
async def readiness_check():
    """Dependency readiness contract for orchestration and probes."""
    from .. import main as handlers

    payload = dict(await handlers.readiness_check())
    if payload.get("status") == "ready":
        return payload
    return JSONResponse(status_code=503, content=payload)
