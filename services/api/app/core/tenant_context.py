from contextvars import ContextVar
from typing import Optional
from fastapi import Request, HTTPException, Depends

TenantContext: ContextVar[Optional[str]] = ContextVar("tenant_id", default=None)


def get_tenant_id() -> str:
    tenant_id = TenantContext.get()
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Tenant context required")
    return tenant_id


class TenantRequired:
    def __init__(self, auto_create: bool = False):
        self.auto_create = auto_create

    async def __call__(self, request: Request) -> str:
        tenant_id = request.headers.get("X-Tenant-ID")
        if not tenant_id:
            tenant_id = request.query_params.get("tenant_id")
        if not tenant_id:
            raise HTTPException(status_code=400, detail="X-Tenant-ID header required")
        TenantContext.set(tenant_id)
        return tenant_id


tenant_required = TenantRequired()
