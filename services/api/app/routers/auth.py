"""Authentication router for signup, login, and token management."""

from __future__ import annotations

from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.core.database import db
from value_fabric.shared.database.tenant_validation import SYSTEM_TENANT_ID
from app.core.security import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.models.schemas import Tenant, User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Request/response schemas
# ---------------------------------------------------------------------------

class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    name: str
    tenant_name: str
    plan: str = "team"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class InviteRequest(BaseModel):
    email: EmailStr
    name: str
    role: Literal["admin", "editor", "viewer"] = "editor"


class AcceptInviteRequest(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    tenant_id: str
    status: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def signup(payload: SignupRequest) -> TokenResponse:
    """Create a new tenant and user, then return a JWT."""
    # Check for existing user with the same email — cross-tenant lookup uses
    # the "system" reserved keyword to bypass per-tenant scoping.
    existing = db.users.list(tenant_id=SYSTEM_TENANT_ID, filter_fn=lambda u: u.email == payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    import uuid as _uuid
    tenant_id = str(_uuid.uuid4())
    tenant = Tenant(
        id=tenant_id,
        name=payload.tenant_name,
        plan=payload.plan,  # type: ignore[arg-type]
    )
    db.tenants.insert(tenant.id, tenant)

    user_id = f"user-{payload.email.split('@')[0].lower()}"
    user = User(
        id=user_id,
        tenant_id=tenant_id,
        email=payload.email,
        name=payload.name,
        role="admin",
        password_hash=hash_password(payload.password),
        status="active",
    )
    db.users.insert(user.id, user)

    access_token = create_access_token(
        subject=user.id,
        tenant_id=tenant_id,
        expires_delta=timedelta(hours=24),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=24 * 60 * 60,
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate a user and return a JWT."""
    # Cross-tenant email lookup — "system" bypasses per-tenant scoping.
    users = db.users.list(tenant_id=SYSTEM_TENANT_ID, filter_fn=lambda u: u.email == payload.email)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = users[0]
    if user.status == "invited":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account pending activation. Please accept your invitation.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.status == "deactivated":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account deactivated. Contact your tenant administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        subject=user.id,
        tenant_id=user.tenant_id,
        expires_delta=timedelta(hours=24),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=24 * 60 * 60,
    )


@router.post("/invite", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def invite_user(
    payload: InviteRequest,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Invite a new user to the current tenant (requires admin role)."""
    if current_user.role not in ("admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only tenant admins can invite users",
        )

    existing = db.users.list(tenant_id=SYSTEM_TENANT_ID, filter_fn=lambda u: u.email == payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    user_id = f"user-{payload.email.split('@')[0].lower()}"
    user = User(
        id=user_id,
        tenant_id=current_user.tenant_id,
        email=payload.email,
        name=payload.name,
        role=payload.role,
        status="invited",
        invited_by=current_user.id,
    )
    db.users.insert(user.id, user)

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        tenant_id=user.tenant_id,
        status=user.status,
    )


@router.post("/accept-invite", response_model=TokenResponse)
async def accept_invite(payload: AcceptInviteRequest) -> TokenResponse:
    """Accept an invitation by setting a password and activating the account."""
    users = db.users.list(tenant_id=SYSTEM_TENANT_ID, filter_fn=lambda u: u.email == payload.email)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    user = users[0]
    if user.status != "invited":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Invitation already accepted or account deactivated",
        )

    # Update user to active with password
    updated = user.model_copy(update={
        "status": "active",
        "password_hash": hash_password(payload.password),
        "name": payload.name,
    })
    db.users.insert(updated.id, updated)

    access_token = create_access_token(
        subject=updated.id,
        tenant_id=updated.tenant_id,
        expires_delta=timedelta(hours=24),
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=24 * 60 * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Return the currently authenticated user (requires valid JWT)."""
    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        tenant_id=user.tenant_id,
        status=user.status,
    )
