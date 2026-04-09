"""
Layer 5 Ground Truth — FastAPI application entry point.

Run with:
  uvicorn layer5_ground_truth.src.api.main:app --host 0.0.0.0 --port 8005 --reload

Or via Docker:
  docker compose up layer5-ground-truth
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import get_settings
from ..database import close_db, init_db
from .router import router

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (startup / shutdown)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifecycle — database init and teardown."""
    settings = get_settings()
    logger.info("Starting Layer 5 Ground Truth service on port %d", settings.api_port)

    # Initialize DB tables (no-op if already exist; Alembic handles migrations)
    if settings.debug:
        logger.info("DEBUG mode: running init_db() to create tables if missing")
        await init_db()

    yield

    logger.info("Shutting down Layer 5 Ground Truth service")
    await close_db()


# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Value Fabric — Ground Truth Layer (L5)",
        description=(
            "Evidence-backed, CFO-defensible facts for the Value Fabric platform. "
            "Provides a validation state machine (extracted → supported → corroborated → approved), "
            "a 0–5 maturity ladder, and bidirectional integration with the Layer 3 Knowledge Graph."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
        contact={
            "name": "Value Fabric Engineering",
            "url": "https://github.com/bmsull560/Fabric_4L",
        },
        license_info={
            "name": "Proprietary",
        },
        openapi_tags=[
            {
                "name": "ground-truth",
                "description": (
                    "CRUD and validation operations for TruthObject records. "
                    "All endpoints are scoped to an organization_id for multi-tenancy."
                ),
            },
            {
                "name": "system",
                "description": "Health check and operational endpoints.",
            },
        ],
    )

    # CORS — restrict in production via environment variable
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.debug else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount the API router
    app.include_router(router)

    # Root redirect to docs
    @app.get("/", include_in_schema=False)
    async def root() -> JSONResponse:
        return JSONResponse(
            content={
                "service": "Value Fabric Ground Truth Layer (L5)",
                "version": "0.1.0",
                "docs": "/docs",
                "health": "/api/v1/health",
            }
        )

    return app


# ---------------------------------------------------------------------------
# Module-level app instance (used by uvicorn)
# ---------------------------------------------------------------------------

app = create_app()
