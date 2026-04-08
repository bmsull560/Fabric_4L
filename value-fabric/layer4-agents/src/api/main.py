"""FastAPI main application for Layer 4 Agentic Workflow Engine."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .routes import workflows, tools, analysis
from ..engine.executor import OrchestrationController
from ..engine.state_manager import StateManager
from ..tools import create_default_registry
from ..tenant.middleware import TenantMiddleware


# Global service instances
workflow_executor: OrchestrationController | None = None
state_manager: StateManager | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global workflow_executor, state_manager
    
    # Startup
    tool_registry = create_default_registry()
    state_manager = StateManager()  # Add Redis client if configured
    workflow_executor = OrchestrationController(tool_registry, state_manager)
    
    # Start the orchestration controller
    await workflow_executor.start()
    
    yield
    
    # Shutdown
    if workflow_executor:
        await workflow_executor.stop()
    workflow_executor = None
    state_manager = None


app = FastAPI(
    title="Layer 4: Agentic Workflow Engine",
    description="LangGraph-powered workflow orchestration for Value Fabric with multi-agent support",
    version="0.2.0",
    lifespan=lifespan
)

# Tenant middleware (must be before CORS to extract from JWT)
app.add_middleware(TenantMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(workflows.router, prefix="/v1", tags=["workflows"])
app.include_router(tools.router, prefix="/v1", tags=["tools"])
app.include_router(analysis.router, prefix="/v1", tags=["analysis"])


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "layer4-agents",
        "version": "0.1.0",
        "executor_ready": workflow_executor is not None
    }


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "service": "Layer 4: Agentic Workflow Engine",
        "version": "0.1.0",
        "documentation": "/docs",
        "health": "/health"
    }
