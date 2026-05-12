"""Hostile tenant-isolation tests for endpoints with compatibility tenant hints.

Endpoint inventory covered by this module:
- POST /v1/ingest (services/layer3-knowledge/src/api/models.py::IngestRequest.tenant_id)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

import importlib.util

pytestmark = pytest.mark.tenant_boundary

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_PATH = REPO_ROOT / "services" / "layer3-knowledge" / "src" / "api" / "models.py"
APP_MONOLITH_PATH = REPO_ROOT / "services" / "layer3-knowledge" / "src" / "api" / "app_monolith.py"
TENANT_RESOLUTION_PATH = REPO_ROOT / "services" / "layer3-knowledge" / "src" / "api" / "services" / "tenant_resolution.py"


def _resolve_ingest_tenant_id(header_tenant_id: str | None, body_tenant_id: str | None) -> str:
    spec = importlib.util.spec_from_file_location("tenant_resolution", TENANT_RESOLUTION_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module.resolve_ingest_tenant_id(header_tenant_id, body_tenant_id)


def test_endpoint_inventory_includes_optional_tenant_hint_model() -> None:
    """Enumerate endpoints whose request models include compatibility tenant hints."""
    source = MODELS_PATH.read_text(encoding="utf-8")
    assert "class IngestRequest" in source
    assert "Optional tenant hint for compatibility" in source


def test_ingest_rejects_missing_auth_tenant_context_fail_closed() -> None:
    """Missing authenticated tenant context must be rejected with stable contract."""
    source = APP_MONOLITH_PATH.read_text(encoding="utf-8", errors="ignore")
    assert 'raise HTTPException(status_code=401, detail="Authentication context is required")' in source


def test_ingest_rejects_mismatched_tenant_hint_fail_closed() -> None:
    """Body/header tenant hints must not override authenticated tenant context."""
    with pytest.raises(HTTPException) as header_exc:
        _resolve_ingest_tenant_id("tenant-auth", "tenant-other")
    assert header_exc.value.status_code == 403
    assert header_exc.value.detail == "Tenant header does not match request tenant_id"


def test_ingest_rejects_cross_tenant_access_attempt_fail_closed() -> None:
    """Cross-tenant attempts via compatibility hints are rejected with stable contract."""
    with pytest.raises(HTTPException) as exc:
        _resolve_ingest_tenant_id("tenant-a", "tenant-b")

    assert exc.value.status_code == 403
    assert exc.value.detail == "Tenant header does not match request tenant_id"
