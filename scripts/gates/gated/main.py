"""FastAPI application for gate daemon."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from uuid import UUID

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .config import DaemonConfig
from .daemon import GateDaemon
from .plugins.loader import PluginLoader


# Global daemon instance
_daemon: Optional[GateDaemon] = None


class ExecuteRequest(BaseModel):
    """Gate execution request."""
    profile: str = Field(default="pr-fast")
    trace_id: Optional[str] = None


class ExecuteResponse(BaseModel):
    """Gate execution response."""
    execution_id: str
    gate_id: str
    status: str
    started_at: str


class GateStatusResponse(BaseModel):
    """Gate status response."""
    execution_id: str
    gate_id: str
    status: str
    results: list[dict]
    artifacts: list[dict]
    duration_seconds: float


class EvaluateRequest(BaseModel):
    """Release evaluation request."""
    gate_ids: Optional[list[str]] = None
    profile: str = Field(default="release-candidate")
    block_on_missing: bool = True
    stale_threshold_hours: int = 24


class EvaluateResponse(BaseModel):
    """Release evaluation response."""
    result: str
    blocks_release: bool
    gates_evaluated: int
    gate_results: list[dict]


class ArtifactResponse(BaseModel):
    """Artifact list response."""
    artifacts: list[dict]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    gates_loaded: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global _daemon
    
    # Startup
    config = DaemonConfig()
    logging.basicConfig(level=getattr(logging, config.log_level.upper()))
    
    _daemon = GateDaemon(config)
    
    # Load plugins
    loader = PluginLoader(config.plugin_search_path)
    plugins = loader.load_all()
    for plugin in plugins:
        _daemon.register_plugin(plugin)
    
    logging.info(f"Gate daemon started with {len(plugins)} plugins")
    yield
    
    # Shutdown
    logging.info("Gate daemon shutting down")


app = FastAPI(
    title="Fabric Gate Daemon",
    description="Unified release gate orchestration system",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        gates_loaded=len(_daemon._plugins) if _daemon else 0,
    )


@app.get("/v1/gates")
async def list_gates():
    """List all registered gates."""
    if not _daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    return {"gates": _daemon.list_gates()}


@app.post("/v1/gates/{gate_id}/execute", response_model=ExecuteResponse)
async def execute_gate(gate_id: str, request: ExecuteRequest):
    """Execute a gate."""
    if not _daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    try:
        execution = await _daemon.execute_gate(
            gate_id=gate_id,
            profile=request.profile,
            trace_id=request.trace_id,
        )
        
        return ExecuteResponse(
            execution_id=str(execution.execution_id),
            gate_id=execution.gate_id,
            status="completed",
            started_at=execution.started_at.isoformat(),
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/gates/{gate_id}/status/{execution_id}")
async def get_gate_status(gate_id: str, execution_id: str):
    """Get gate execution status."""
    if not _daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    execution = _daemon.get_execution(execution_id)
    if not execution or execution.gate_id != gate_id:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    from datetime import datetime
    duration = 0.0
    if execution.finished_at:
        duration = (execution.finished_at - execution.started_at).total_seconds()
    
    return GateStatusResponse(
        execution_id=str(execution.execution_id),
        gate_id=execution.gate_id,
        status="completed" if execution.finished_at else "running",
        results=[
            {
                "name": r.name,
                "result": r.result.value,
                "value": r.value,
                "threshold": r.threshold,
                "duration_ms": r.duration_ms,
                "message": r.message,
            }
            for r in execution.results
        ],
        artifacts=[
            {
                "path": str(a.path),
                "content_type": a.content_type,
                "checksum": a.checksum,
                "size_bytes": a.size_bytes,
            }
            for a in execution.artifacts
        ],
        duration_seconds=duration,
    )


@app.get("/v1/gates/{gate_id}/artifacts")
async def get_gate_artifacts(gate_id: str):
    """Get gate artifacts."""
    if not _daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    # Find latest execution for this gate
    latest = None
    for exec in _daemon._executions.values():
        if exec.gate_id == gate_id:
            if not latest or exec.started_at > latest.started_at:
                latest = exec
    
    if not latest:
        return ArtifactResponse(artifacts=[])
    
    return ArtifactResponse(
        artifacts=[
            {
                "path": str(a.path),
                "content_type": a.content_type,
                "checksum": a.checksum,
                "size_bytes": a.size_bytes,
            }
            for a in latest.artifacts
        ]
    )


@app.post("/v1/evaluate", response_model=EvaluateResponse)
async def evaluate_release(request: EvaluateRequest):
    """Evaluate all gates for release."""
    if not _daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    result = _daemon.evaluate_release(
        gate_ids=request.gate_ids,
        profile=request.profile,
        block_on_missing=request.block_on_missing,
        stale_threshold_hours=request.stale_threshold_hours,
    )
    
    return EvaluateResponse(**result)


@app.post("/v1/manifest/sign")
async def sign_manifest():
    """Sign release manifest."""
    # TODO: Implement signing
    return {"status": "not_implemented"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8888)
