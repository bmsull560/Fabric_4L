from __future__ import annotations

from fastapi import HTTPException, Request


def extract_tenant_id(request: Request | None, *, tenant_support_enabled: bool) -> str | None:
    if not request or not tenant_support_enabled:
        return None
    ctx = getattr(request.state, "governance_context", None)
    if ctx and ctx.tenant_id:
        return str(ctx.tenant_id)
    return None


def resolve_ingest_tenant_id(header_tenant_id: str | None, body_tenant_id: str | None) -> str:
    normalized_header = header_tenant_id.strip() if header_tenant_id else ""
    normalized_body = body_tenant_id.strip() if body_tenant_id else ""

    if normalized_header and normalized_body and normalized_header != normalized_body:
        raise HTTPException(status_code=403, detail="Tenant header does not match request tenant_id")
    tenant_id = normalized_header or normalized_body
    if not tenant_id:
        raise HTTPException(status_code=400, detail="tenant_id is required for RDF ingestion")
    return tenant_id
