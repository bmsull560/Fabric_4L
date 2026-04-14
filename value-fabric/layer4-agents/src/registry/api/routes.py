"""Model Registry API routes."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from shared.identity.context import RequestContext
from shared.identity.dependencies import require_any_permission
from shared.identity.permissions import Permission
from sqlalchemy.ext.asyncio import AsyncSession

from ...database import get_db
from ..service import ModelRegistryService

router = APIRouter(prefix="/models", tags=["Model Registry"])

require_write_or_admin_models = require_any_permission(
    Permission.WRITE_MODELS, Permission.ADMIN_MODELS
)


class ModelRegisterRequest(BaseModel):
    """Payload to register a new model version."""

    provider: str = Field(..., min_length=1, max_length=50)
    model_name: str = Field(..., min_length=1, max_length=100)
    model_version: str = Field(..., min_length=1, max_length=50)
    stage: str = Field(default="dev", pattern=r"^(dev|staging|production|deprecated)$")
    config: dict[str, Any] = Field(default_factory=dict)
    eval_score: float | None = Field(None, ge=0.0, le=1.0)
    eval_run_id: str | None = Field(None, max_length=100)


class ModelVersionResponse(BaseModel):
    """Read-only model version response."""

    id: UUID
    tenant_id: UUID
    provider: str
    model_name: str
    model_version: str
    stage: str
    promoted_by: UUID | None = None
    eval_score: float | None = None
    eval_run_id: str | None = None
    config: dict[str, Any]
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class ModelPromoteRequest(BaseModel):
    """Payload to promote a model to a new stage."""

    to_stage: str = Field(..., pattern=r"^(dev|staging|production|deprecated)$")
    reason: str | None = Field(None, max_length=2000)


class PromotionLogResponse(BaseModel):
    """Read-only promotion log entry."""

    id: UUID
    model_version_id: UUID
    from_stage: str
    to_stage: str
    promoted_by: UUID | None = None
    reason: str | None = None
    eval_score: float | None = None
    eval_gate_passed: bool
    created_at: str

    model_config = ConfigDict(from_attributes=True)


@router.post("", response_model=ModelVersionResponse, status_code=status.HTTP_201_CREATED)
async def api_register_model(
    request: ModelRegisterRequest,
    ctx: RequestContext = Depends(require_write_or_admin_models),
    db: AsyncSession = Depends(get_db),
) -> ModelVersionResponse:
    """Register a new model version. Requires ``write:models`` or ``admin:models``."""
    model = await ModelRegistryService.register_model(
        db=db,
        tenant_id=ctx.tenant_id,
        provider=request.provider,
        model_name=request.model_name,
        model_version=request.model_version,
        stage=request.stage,
        config=request.config,
        eval_score=request.eval_score,
        eval_run_id=request.eval_run_id,
    )
    return ModelVersionResponse.model_validate(model)


@router.get("", response_model=list[ModelVersionResponse])
async def api_list_models(
    stage: str | None = Query(None, pattern=r"^(dev|staging|production|deprecated)$"),
    ctx: RequestContext = Depends(
        require_any_permission(
            Permission.READ_MODELS, Permission.WRITE_MODELS, Permission.ADMIN_MODELS
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> list[ModelVersionResponse]:
    """List model versions for the caller's tenant."""
    models = await ModelRegistryService.list_models(db, ctx.tenant_id, stage=stage)
    return [ModelVersionResponse.model_validate(m) for m in models]


@router.get("/{model_id}", response_model=ModelVersionResponse)
async def api_get_model(
    model_id: UUID,
    ctx: RequestContext = Depends(
        require_any_permission(
            Permission.READ_MODELS, Permission.WRITE_MODELS, Permission.ADMIN_MODELS
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ModelVersionResponse:
    """Get a single model version by ID."""
    model = await ModelRegistryService.get_model(db, model_id)
    if model is None or model.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Model version not found")
    return ModelVersionResponse.model_validate(model)


@router.post("/{model_id}/promote", response_model=ModelVersionResponse)
async def api_promote_model(
    model_id: UUID,
    request: ModelPromoteRequest,
    ctx: RequestContext = Depends(require_write_or_admin_models),
    db: AsyncSession = Depends(get_db),
) -> ModelVersionResponse:
    """Promote a model version to a new stage."""
    from uuid import UUID as UuidType

    promoted_by = UuidType(ctx.user_id) if ctx.user_id else None
    try:
        model = await ModelRegistryService.promote_model(
            db=db,
            model_version_id=model_id,
            to_stage=request.to_stage,
            promoted_by=promoted_by,
            reason=request.reason,
        )
    except ModelRegistryService.PromotionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if model.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Model version not found")
    return ModelVersionResponse.model_validate(model)


@router.get("/{model_id}/history", response_model=list[PromotionLogResponse])
async def api_get_promotion_history(
    model_id: UUID,
    ctx: RequestContext = Depends(
        require_any_permission(
            Permission.READ_MODELS, Permission.WRITE_MODELS, Permission.ADMIN_MODELS
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> list[PromotionLogResponse]:
    """Get promotion history for a model version."""
    model = await ModelRegistryService.get_model(db, model_id)
    if model is None or model.tenant_id != ctx.tenant_id:
        raise HTTPException(status_code=404, detail="Model version not found")
    history = await ModelRegistryService.get_promotion_history(db, model_id)
    return [PromotionLogResponse.model_validate(h) for h in history]


@router.get("/active", response_model=ModelVersionResponse)
async def api_get_active_model(
    provider: str = Query(..., min_length=1, max_length=50),
    ctx: RequestContext = Depends(
        require_any_permission(
            Permission.READ_MODELS, Permission.WRITE_MODELS, Permission.ADMIN_MODELS
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> ModelVersionResponse:
    """Get the active production model for a provider."""
    model = await ModelRegistryService.get_active_production_model(db, ctx.tenant_id, provider)
    if model is None:
        raise HTTPException(status_code=404, detail="No active production model found")
    return ModelVersionResponse.model_validate(model)
