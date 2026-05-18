"""Allowed service-local exception for Layer 3 service wrapper.

Owner: layer3-knowledge
Removal/migration target: 2026-09-30
Reason: Route-level helpers for tenant resolution.

Compatibility shim to keep app_monolith as an orchestration facade while
consolidating tenant parsing logic in api/services.
"""

from ...services.tenant_resolution import extract_tenant_id, resolve_ingest_tenant_id

__all__ = ["extract_tenant_id", "resolve_ingest_tenant_id"]
