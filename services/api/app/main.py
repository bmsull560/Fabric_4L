from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.services.seed_data import seed_all
from app.routers import (
    accounts,
    intelligence,
    hypotheses,
    drivers,
    evidence,
    calculator,
    value_cases,
    context_engine,
    governance,
    agents,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_all()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Fabric_4L unified API for value management",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
