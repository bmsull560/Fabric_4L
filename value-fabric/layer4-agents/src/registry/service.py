"""Model Registry service layer."""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.audit import emit_audit_event, AuditAction, AuditOutcome
from shared.identity.permissions import Permission

from .eval_gate import check_eval_gate
from .models import ModelPromotionLog, ModelVersion

logger = logging.getLogger(__name__)


class PromotionError(Exception):
    """Raised when a model promotion is not allowed."""

    pass


class ModelRegistryService:
    """Business logic for registering and promoting models."""

    # -----------------------------------------------------------------------
    # CRUD
    # -----------------------------------------------------------------------

    @staticmethod
    async def register_model(
        db: AsyncSession,
        tenant_id: UUID,
        provider: str,
        model_name: str,
        model_version: str,
        stage: str = "dev",
        config: Optional[Dict[str, Any]] = None,
        eval_score: Optional[float] = None,
        eval_run_id: Optional[str] = None,
    ) -> ModelVersion:
        """Register a new model version."""
        model = ModelVersion(
            tenant_id=tenant_id,
            provider=provider,
            model_name=model_name,
            model_version=model_version,
            stage=stage,
            config=config or {},
            eval_score=eval_score,
            eval_run_id=eval_run_id,
        )
        db.add(model)
        await db.flush()

        emit_audit_event(
            AuditAction.MODEL_REGISTERED,
            tenant_id=tenant_id,
            resource_type="ModelVersion",
            resource_id=str(model.id),
            details={
                "provider": provider,
                "model_name": model_name,
                "model_version": model_version,
                "stage": stage,
            },
        )
        logger.info("Registered model %s/%s (%s) for tenant %s", provider, model_name, model_version, tenant_id)
        return model

    @staticmethod
    async def list_models(
        db: AsyncSession,
        tenant_id: UUID,
        stage: Optional[str] = None,
    ) -> List[ModelVersion]:
        """List model versions for a tenant, optionally filtered by stage."""
        q = select(ModelVersion).where(ModelVersion.tenant_id == tenant_id)
        if stage:
            q = q.where(ModelVersion.stage == stage)
        q = q.order_by(ModelVersion.created_at.desc())
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def get_active_production_model(
        db: AsyncSession,
        tenant_id: UUID,
        provider: str,
    ) -> Optional[ModelVersion]:
        """Return the latest production model for a tenant/provider."""
        result = await db.execute(
            select(ModelVersion)
            .where(
                ModelVersion.tenant_id == tenant_id,
                ModelVersion.provider == provider,
                ModelVersion.stage == "production",
            )
            .order_by(ModelVersion.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_model(
        db: AsyncSession,
        model_version_id: UUID,
    ) -> Optional[ModelVersion]:
        """Fetch a single model version by ID."""
        result = await db.execute(
            select(ModelVersion).where(ModelVersion.id == model_version_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_promotion_history(
        db: AsyncSession,
        model_version_id: UUID,
    ) -> List[ModelPromotionLog]:
        """Return the promotion audit trail for a model version."""
        result = await db.execute(
            select(ModelPromotionLog)
            .where(ModelPromotionLog.model_version_id == model_version_id)
            .order_by(ModelPromotionLog.created_at.desc())
        )
        return list(result.scalars().all())

    # -----------------------------------------------------------------------
    # Promotion
    # -----------------------------------------------------------------------

    @staticmethod
    async def promote_model(
        db: AsyncSession,
        model_version_id: UUID,
        to_stage: str,
        promoted_by: Optional[UUID] = None,
        reason: Optional[str] = None,
    ) -> ModelVersion:
        """Promote a model version to a new stage.

        Gates:
        - dev → staging: always allowed
        - staging → production: requires eval_score >= threshold
        - production → deprecated: always allowed
        """
        result = await db.execute(
            select(ModelVersion).where(ModelVersion.id == model_version_id)
        )
        model = result.scalar_one_or_none()
        if model is None:
            raise PromotionError(f"Model version {model_version_id} not found")

        from_stage = model.stage

        if from_stage == to_stage:
            raise PromotionError(f"Model is already in stage '{to_stage}'")

        # Enforce promotion gates
        eval_passed = None
        if from_stage == "staging" and to_stage == "production":
            eval_passed = await check_eval_gate(db, model_version_id)
            if not eval_passed:
                raise PromotionError(
                    "Evaluation gate failed: eval_score below promotion threshold"
                )

        # Update model
        model.stage = to_stage
        model.promoted_by = promoted_by

        # Log promotion
        log_entry = ModelPromotionLog(
            model_version_id=model_version_id,
            from_stage=from_stage,
            to_stage=to_stage,
            promoted_by=promoted_by,
            reason=reason,
            eval_score=model.eval_score,
            eval_gate_passed=eval_passed if eval_passed is not None else True,
        )
        db.add(log_entry)
        await db.flush()

        # Audit event
        action = (
            AuditAction.MODEL_DEPRECATED
            if to_stage == "deprecated"
            else AuditAction.MODEL_PROMOTED
        )
        emit_audit_event(
            action,
            tenant_id=model.tenant_id,
            resource_type="ModelVersion",
            resource_id=str(model.id),
            details={
                "from_stage": from_stage,
                "to_stage": to_stage,
                "reason": reason,
                "eval_score": model.eval_score,
            },
        )
        logger.info(
            "Promoted model %s from %s to %s",
            model_version_id,
            from_stage,
            to_stage,
        )
        return model


async def resolve_llm_model(
    db: AsyncSession,
    tenant_id: UUID,
    provider: str = "openai",
) -> str:
    """Resolve the active production model name for a tenant/provider.

    Falls back to ``os.getenv('LLM_MODEL', 'gpt-4o')`` if no production model
    is registered.
    """
    model = await ModelRegistryService.get_active_production_model(
        db, tenant_id, provider
    )
    if model:
        return model.model_name
    return os.getenv("LLM_MODEL", "gpt-4o")
