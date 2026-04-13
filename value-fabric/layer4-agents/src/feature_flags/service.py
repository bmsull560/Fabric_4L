"""FeatureFlagService — business logic for feature flag CRUD and evaluation."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import BackgroundTasks
from shared.audit import AuditEmitter, emit_audit_event
from shared.audit.models import AuditAction
from shared.identity.context import RequestContext
from shared.identity.feature_flags import is_enabled, register_feature_flag_lookup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import FeatureFlag

logger = logging.getLogger(__name__)


class FeatureFlagService:
    """CRUD and evaluation service for feature flags."""

    @staticmethod
    async def list_flags(
        db: AsyncSession,
        tenant_id: UUID | None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[FeatureFlag]:
        """List feature flags scoped to a tenant or platform-wide."""
        q = select(FeatureFlag)
        if tenant_id is not None:
            q = q.where(FeatureFlag.tenant_id == tenant_id)
        else:
            q = q.where(FeatureFlag.tenant_id.is_(None))
        q = q.order_by(FeatureFlag.flag_key.asc()).limit(limit).offset(offset)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def get_flag(
        db: AsyncSession,
        flag_key: str,
        tenant_id: UUID | None,
    ) -> FeatureFlag | None:
        """Fetch a single flag by key and tenant scope."""
        q = select(FeatureFlag).where(
            FeatureFlag.flag_key == flag_key,
            FeatureFlag.tenant_id == tenant_id,
        )
        result = await db.execute(q)
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_flag(
        db: AsyncSession,
        flag_key: str,
        tenant_id: UUID | None,
        enabled: bool,
        rollout_percentage: int,
        description: str | None,
        metadata: dict[str, Any] | None,
        updated_by: UUID | None,
        background_tasks: BackgroundTasks | None = None,
        ctx: RequestContext | None = None,
    ) -> FeatureFlag:
        """Create or update a feature flag."""
        existing = await FeatureFlagService.get_flag(db, flag_key, tenant_id)
        if existing is not None:
            existing.enabled = enabled
            existing.rollout_percentage = rollout_percentage
            if description is not None:
                existing.description = description
            if metadata is not None:
                existing.metadata_ = metadata
            existing.updated_by = updated_by
            await db.flush()
            action = AuditAction.FEATURE_FLAG_UPDATED
        else:
            existing = FeatureFlag(
                tenant_id=tenant_id,
                flag_key=flag_key,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                description=description,
                metadata_=metadata or {},
                updated_by=updated_by,
            )
            db.add(existing)
            await db.flush()
            action = AuditAction.FEATURE_FLAG_CREATED

        event = emit_audit_event(
            action,
            tenant_id=tenant_id,
            user_id=ctx.user_id if ctx else None,
            api_key_id=ctx.api_key_id if ctx else None,
            resource_type="FeatureFlag",
            resource_id=flag_key,
            details={
                "enabled": enabled,
                "rollout_percentage": rollout_percentage,
                "tenant_id": str(tenant_id) if tenant_id else None,
            },
        )
        if background_tasks is not None:
            from ...database import db_session

            background_tasks.add_task(AuditEmitter.write_to_db, event, db_session)

        return existing

    @staticmethod
    async def delete_flag(
        db: AsyncSession,
        flag_key: str,
        tenant_id: UUID | None,
        background_tasks: BackgroundTasks | None = None,
        ctx: RequestContext | None = None,
    ) -> bool:
        """Delete a feature flag."""
        existing = await FeatureFlagService.get_flag(db, flag_key, tenant_id)
        if existing is None:
            return False
        await db.delete(existing)
        await db.flush()

        event = emit_audit_event(
            AuditAction.FEATURE_FLAG_DELETED,
            tenant_id=tenant_id,
            user_id=ctx.user_id if ctx else None,
            api_key_id=ctx.api_key_id if ctx else None,
            resource_type="FeatureFlag",
            resource_id=flag_key,
            details={"tenant_id": str(tenant_id) if tenant_id else None},
        )
        if background_tasks is not None:
            from ...database import db_session

            background_tasks.add_task(AuditEmitter.write_to_db, event, db_session)

        return True

    @staticmethod
    async def evaluate_flag(
        flag_key: str,
        tenant_id: UUID | None,
        user_id: str | None = None,
    ) -> bool:
        """Evaluate a feature flag for the given context (uses Redis cache)."""
        return await is_enabled(flag_key, tenant_id, user_id)

    @staticmethod
    async def lookup_flag(
        db: AsyncSession,
        flag_key: str,
        tenant_id: UUID | None,
    ) -> dict[str, Any] | None:
        """Lookup flag data for evaluation (used by shared identity feature flag system).

        Returns dict with 'enabled' and 'rollout_percentage' keys, or None if not found.
        """
        flag = await FeatureFlagService.get_flag(db, flag_key, tenant_id)
        if flag is None:
            return None
        return {
            "enabled": flag.enabled,
            "rollout_percentage": flag.rollout_percentage,
        }


async def _lookup_flag(flag_key: str, tenant_id: UUID | None) -> dict[str, Any] | None:
    """DB lookup callback registered with ``shared.identity.feature_flags``."""
    from ...database import db_session

    async with db_session() as db:
        # Try tenant-specific first
        if tenant_id is not None:
            result = await db.execute(
                select(FeatureFlag).where(
                    FeatureFlag.tenant_id == tenant_id,
                    FeatureFlag.flag_key == flag_key,
                )
            )
            row = result.scalar_one_or_none()
            if row is not None:
                return {
                    "enabled": row.enabled,
                    "rollout_percentage": row.rollout_percentage,
                }

        # Fall back to platform-wide
        result = await db.execute(
            select(FeatureFlag).where(
                FeatureFlag.tenant_id.is_(None),
                FeatureFlag.flag_key == flag_key,
            )
        )
        row = result.scalar_one_or_none()
        if row is not None:
            return {
                "enabled": row.enabled,
                "rollout_percentage": row.rollout_percentage,
            }
    return None


def init_feature_flag_lookup() -> None:
    """Register the Layer 4 DB-backed lookup with the shared evaluator."""
    register_feature_flag_lookup(_lookup_flag)
