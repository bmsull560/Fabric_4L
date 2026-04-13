"""Tenant Service — business logic for Tenant, User, and APIKey lifecycle.

This service is the single source of truth for:
- Creating / suspending / deleting tenants
- Inviting / activating / deactivating users
- Issuing / revoking API keys

All methods are async to integrate with SQLAlchemy's async session.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from shared.identity.hashing import (
    extract_key_prefix,
    generate_api_key,
    hash_api_key,
)
from shared.identity.models import (
    APIKeyCreateRequest,
    APIKeyCreateResponse,
    APIKeyModel,
    TenantCreateRequest,
    TenantModel,
    TenantStatus,
    TenantUpdateRequest,
    UserInviteRequest,
    UserModel,
    UserStatus,
    UserUpdateRequest,
)
from shared.identity.permissions import ROLE_PERMISSIONS, Role

from .models.api_key import APIKey
from .models.tenant import Tenant
from .models.user import User

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tenant CRUD
# ---------------------------------------------------------------------------


async def create_tenant(
    db: AsyncSession, request: TenantCreateRequest
) -> TenantModel:
    """Create a new tenant.  Caller must hold ADMIN_TENANTS permission."""
    tenant = Tenant(
        id=uuid.uuid4(),
        name=request.name,
        slug=request.slug,
        status=TenantStatus.ACTIVE.value,
        settings=request.settings,
    )
    db.add(tenant)
    await db.flush()
    logger.info("Created tenant %s (slug=%s)", tenant.id, tenant.slug)
    return _tenant_to_model(tenant)


async def get_tenant(db: AsyncSession, tenant_id: UUID) -> Optional[TenantModel]:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    return _tenant_to_model(tenant) if tenant else None


async def list_tenants(
    db: AsyncSession, *, status: Optional[str] = None, limit: int = 100, offset: int = 0
) -> List[TenantModel]:
    q = select(Tenant).order_by(Tenant.created_at.desc()).limit(limit).offset(offset)
    if status:
        q = q.where(Tenant.status == status)
    result = await db.execute(q)
    return [_tenant_to_model(t) for t in result.scalars().all()]


async def update_tenant(
    db: AsyncSession, tenant_id: UUID, request: TenantUpdateRequest
) -> Optional[TenantModel]:
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return None
    if request.name is not None:
        tenant.name = request.name
    if request.status is not None:
        tenant.status = request.status.value
    if request.settings is not None:
        tenant.settings = request.settings
    tenant.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _tenant_to_model(tenant)


async def delete_tenant(db: AsyncSession, tenant_id: UUID) -> bool:
    """Soft-delete by setting status to 'deleted'."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        return False
    tenant.status = TenantStatus.DELETED.value
    tenant.updated_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("Soft-deleted tenant %s", tenant_id)
    return True


# ---------------------------------------------------------------------------
# User management
# ---------------------------------------------------------------------------


async def invite_user(
    db: AsyncSession,
    tenant_id: UUID,
    request: UserInviteRequest,
    invited_by: Optional[UUID] = None,
) -> UserModel:
    """Invite a new user to the tenant.  Caller must hold ADMIN_USERS permission."""
    user = User(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        email=request.email,
        display_name=request.display_name,
        role=request.role.value,
        status=UserStatus.INVITED.value,
        invited_by=invited_by,
    )
    db.add(user)
    await db.flush()
    logger.info("Invited user %s to tenant %s", request.email, tenant_id)
    return _user_to_model(user)


async def get_user(
    db: AsyncSession, tenant_id: UUID, user_id: UUID
) -> Optional[UserModel]:
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    return _user_to_model(user) if user else None


async def list_users(
    db: AsyncSession, tenant_id: UUID, *, limit: int = 100, offset: int = 0
) -> List[UserModel]:
    result = await db.execute(
        select(User)
        .where(User.tenant_id == tenant_id)
        .order_by(User.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_user_to_model(u) for u in result.scalars().all()]


async def update_user(
    db: AsyncSession, tenant_id: UUID, user_id: UUID, request: UserUpdateRequest
) -> Optional[UserModel]:
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None
    if request.display_name is not None:
        user.display_name = request.display_name
    if request.role is not None:
        user.role = request.role.value
    if request.status is not None:
        user.status = request.status.value
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _user_to_model(user)


async def deactivate_user(
    db: AsyncSession, tenant_id: UUID, user_id: UUID
) -> bool:
    result = await db.execute(
        select(User).where(User.id == user_id, User.tenant_id == tenant_id)
    )
    user = result.scalar_one_or_none()
    if not user:
        return False
    user.status = UserStatus.DEACTIVATED.value
    user.updated_at = datetime.now(timezone.utc)
    await db.flush()
    logger.info("Deactivated user %s in tenant %s", user_id, tenant_id)
    return True


# ---------------------------------------------------------------------------
# API key management
# ---------------------------------------------------------------------------


async def create_api_key(
    db: AsyncSession,
    tenant_id: UUID,
    request: APIKeyCreateRequest,
    user_id: Optional[UUID] = None,
) -> APIKeyCreateResponse:
    """Issue a new API key.  Caller must hold ADMIN_API_KEYS permission.

    The raw key is returned **once** and never stored.  The HMAC-SHA256
    digest is stored in the database.
    """
    raw_key = generate_api_key()
    key_hash = hash_api_key(raw_key)
    prefix = extract_key_prefix(raw_key)
    key_id = f"vf_{uuid.uuid4().hex}"

    permissions = request.permissions
    if not permissions:
        permissions = ROLE_PERMISSIONS[request.role].permissions

    key = APIKey(
        key_id=key_id,
        tenant_id=tenant_id,
        user_id=user_id,
        name=request.name,
        key_hash=key_hash,
        prefix=prefix,
        role=request.role.value,
        permissions=[p.value for p in permissions],
        enabled=True,
        expires_at=request.expires_at,
        rate_limit_per_minute=request.rate_limit_per_minute,
        metadata_=request.metadata,
    )
    db.add(key)
    await db.flush()
    logger.info("Created API key %s for tenant %s", key_id, tenant_id)

    return APIKeyCreateResponse(
        key_id=key_id,
        tenant_id=tenant_id,
        name=request.name,
        api_key=raw_key,
        prefix=prefix,
        role=request.role,
        permissions=frozenset(permissions),
        expires_at=request.expires_at,
        rate_limit_per_minute=request.rate_limit_per_minute,
        created_at=key.created_at,
    )


async def list_api_keys(
    db: AsyncSession, tenant_id: UUID, *, enabled_only: bool = True
) -> List[APIKeyModel]:
    q = select(APIKey).where(APIKey.tenant_id == tenant_id)
    if enabled_only:
        q = q.where(APIKey.enabled.is_(True))
    result = await db.execute(q.order_by(APIKey.created_at.desc()))
    return [_api_key_to_model(k) for k in result.scalars().all()]


async def revoke_api_key(
    db: AsyncSession, tenant_id: UUID, key_id: str
) -> bool:
    """Disable (soft-delete) an API key."""
    result = await db.execute(
        select(APIKey).where(APIKey.key_id == key_id, APIKey.tenant_id == tenant_id)
    )
    key = result.scalar_one_or_none()
    if not key:
        return False
    key.enabled = False
    await db.flush()
    logger.info("Revoked API key %s for tenant %s", key_id, tenant_id)
    return True


async def lookup_api_key_by_hash(
    db: AsyncSession, raw_key: str
) -> Optional[dict]:
    """Look up an API key record by its raw value (for GovernanceMiddleware).

    Returns a dict suitable for ``GovernanceMiddleware``'s ``api_key_resolver``
    or ``None`` if the key is not found / disabled / expired.
    """
    key_hash = hash_api_key(raw_key)
    result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    key = result.scalar_one_or_none()
    if not key:
        return None
    if not key.enabled or key.is_expired():
        return None
    # Update last_used_at asynchronously (fire-and-forget inside same session)
    key.last_used_at = datetime.now(timezone.utc)
    return {
        "key_id": key.key_id,
        "tenant_id": str(key.tenant_id),
        "user_id": str(key.user_id) if key.user_id else None,
        "role": key.role,
        "permissions": key.permissions,
        "enabled": key.enabled,
        "rate_limit_per_minute": key.rate_limit_per_minute,
    }


# ---------------------------------------------------------------------------
# Private converters
# ---------------------------------------------------------------------------


def _tenant_to_model(t: Tenant) -> TenantModel:
    return TenantModel(
        id=t.id,
        name=t.name,
        slug=t.slug,
        status=t.status,
        settings=t.settings or {},
        created_at=t.created_at,
        updated_at=t.updated_at,
    )


def _user_to_model(u: User) -> UserModel:
    return UserModel(
        id=u.id,
        tenant_id=u.tenant_id,
        email=u.email,
        display_name=u.display_name,
        role=u.role,
        status=u.status,
        last_login_at=u.last_login_at,
        invited_by=u.invited_by,
        created_at=u.created_at,
        updated_at=u.updated_at,
    )


def _api_key_to_model(k: APIKey) -> APIKeyModel:
    from shared.identity.permissions import Permission

    perms: frozenset = frozenset()
    if k.permissions:
        perms = frozenset(
            Permission(p) for p in k.permissions if p in Permission._value2member_map_
        )

    return APIKeyModel(
        key_id=k.key_id,
        tenant_id=k.tenant_id,
        user_id=k.user_id,
        name=k.name,
        prefix=k.prefix,
        role=k.role,
        permissions=perms,
        enabled=k.enabled,
        created_at=k.created_at,
        expires_at=k.expires_at,
        last_used_at=k.last_used_at,
        rate_limit_per_minute=k.rate_limit_per_minute,
        metadata=k.metadata_ or {},
    )
