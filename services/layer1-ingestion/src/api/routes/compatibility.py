"""Compatibility and shared security probe routes for Layer 1."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request

from value_fabric.shared.identity import RequestContext, Role, require_authenticated, require_role


router = APIRouter()
_INGESTION_SOURCE_COMPAT_STORE: dict[str, dict[str, Any]] = {}


@router.post("/v1/ingest", tags=["Compatibility"])
async def short_ingest_compatibility_boundary(
    _ctx: RequestContext = Depends(require_authenticated),
) -> dict[str, str]:
    raise HTTPException(
        status_code=410,
        detail="Use the canonical /api/v1/ingestion endpoints for Layer 1 ingestion operations.",
    )


@router.post("/api/v1/ingestion/sources", tags=["Compatibility"], status_code=201)
async def create_ingestion_source_compatibility_boundary(
    request: Request,
    ctx: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid source payload") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=422, detail="Source payload must be an object")
    source_id = str(payload.get("id") or uuid4())
    record = {
        **payload,
        "id": source_id,
        "tenant_id": str(ctx.tenant_id),
        "status": payload.get("status", "created"),
        "created_at": datetime.now(UTC).isoformat(),
    }
    _INGESTION_SOURCE_COMPAT_STORE[source_id] = record
    return record


@router.get("/api/v1/ingestion/sources/{source_id}", tags=["Compatibility"])
async def get_ingestion_source_compatibility_boundary(
    source_id: str,
    _ctx: RequestContext = Depends(require_authenticated),
) -> dict[str, Any]:
    record = _INGESTION_SOURCE_COMPAT_STORE.get(source_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return record


@router.get("/api/v1/entities", tags=["Security Compatibility"])
async def entity_security_boundary(
    _ctx: RequestContext = Depends(require_authenticated),
) -> dict[str, list[Any]]:
    return {"entities": []}


@router.delete("/api/v1/entities/{entity_id}", tags=["Security Compatibility"])
async def entity_delete_security_boundary(
    entity_id: str,
    _ctx: RequestContext = Depends(require_role(Role.TENANT_ADMIN, Role.SUPER_ADMIN)),
) -> dict[str, str]:
    raise HTTPException(
        status_code=501,
        detail=f"Entity deletion for {entity_id} is owned by the Layer 3 entity API contract.",
    )


@router.get("/api/v1/user/profile", tags=["Security Compatibility"])
async def user_profile_security_boundary(
    ctx: RequestContext = Depends(require_authenticated),
) -> dict[str, str]:
    return {"user_id": str(ctx.user_id), "tenant_id": str(ctx.tenant_id)}


@router.get("/api/v1/user/{user_id}/private-data", tags=["Security Compatibility"])
async def user_private_data_security_boundary(
    user_id: str,
    ctx: RequestContext = Depends(require_authenticated),
) -> dict[str, str]:
    if str(ctx.user_id) != user_id:
        raise HTTPException(status_code=403, detail="User cannot access another user's private data")
    return {"user_id": user_id}


@router.get("/api/admin/users", tags=["Security Compatibility"])
@router.get("/api/admin/config", tags=["Security Compatibility"])
@router.get("/api/admin/audit-logs", tags=["Security Compatibility"])
@router.get("/api/admin/tenants", tags=["Security Compatibility"])
async def admin_read_security_boundary(
    _ctx: RequestContext = Depends(require_role(Role.TENANT_ADMIN, Role.SUPER_ADMIN)),
) -> dict[str, str]:
    return {"status": "authorized"}
