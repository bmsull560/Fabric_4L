from contextlib import asynccontextmanager

from fastapi import FastAPI
from value_fabric.shared.fastapi_framework import create_fabric_app
from value_fabric.shared.security import validate_production_safety

from app.core.config import get_settings
from app.routers import (
    accounts,
    agents,
    calculator,
    context_engine,
    drivers,
    evidence,
    governance,
    hypotheses,
    intelligence,
    value_cases,
)
from app.services.seed_data import seed_all

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_production_safety()
    if settings.seed_demo_data:
        seed_all()
    yield


app = create_fabric_app(
    service_name="fabric-4l-api",
    title=settings.app_name,
    version="0.1.0",
    description="Fabric_4L unified API for value management",
    lifespan=lifespan,
    cors_policy=settings.cors_policy,
)

app.include_router(accounts.router, prefix="/v1")
app.include_router(intelligence.router, prefix="/v1")
app.include_router(hypotheses.router, prefix="/v1")
app.include_router(drivers.router, prefix="/v1")
app.include_router(evidence.router, prefix="/v1")
app.include_router(calculator.router, prefix="/v1")
app.include_router(value_cases.router, prefix="/v1")
app.include_router(context_engine.router, prefix="/v1")
app.include_router(governance.router, prefix="/v1")
app.include_router(agents.router, prefix="/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "fabric-4l-api"}


@app.get("/metrics")
async def metrics():
    return {"requests_total": 0, "errors_total": 0}
