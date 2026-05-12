"""Layer 3 FastAPI app factory and lifespan wiring."""

from __future__ import annotations

from fastapi import FastAPI


def create_app(*, lifespan) -> FastAPI:
    """Create the Layer 3 FastAPI application with canonical metadata."""
    return FastAPI(
        title="Value Fabric - Knowledge Graph & Semantic Layer",
        description="""
    ## Layer 3: Knowledge Graph & Semantic Layer API
    
    The Value Fabric Knowledge Graph API provides intelligent semantic search, 
    graph-based retrieval, and analytics capabilities for enterprise AI workflows.
    """,
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        contact={"name": "Value Fabric Team", "email": "value-fabric@example.com"},
        license_info={"name": "Proprietary", "url": "https://valuefabric.com/license"},
        lifespan=lifespan,
    )
