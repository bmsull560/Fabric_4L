from __future__ import annotations

import pytest
from fastapi import HTTPException

from value_fabric.layer3.api.app_monolith import _resolve_ingest_tenant_id


def test_ingest_tenant_resolution_requires_tenant() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _resolve_ingest_tenant_id(None, None)

    assert exc_info.value.status_code == 400
    assert "tenant_id is required" in str(exc_info.value.detail)


def test_ingest_tenant_resolution_rejects_forged_body_tenant() -> None:
    with pytest.raises(HTTPException) as exc_info:
        _resolve_ingest_tenant_id("tenant-a", "tenant-b")

    assert exc_info.value.status_code == 403


@pytest.mark.parametrize(
    ("header_tenant_id", "body_tenant_id", "expected"),
    [
        ("tenant-a", None, "tenant-a"),
        (" tenant-a ", None, "tenant-a"),
        (None, "tenant-a", "tenant-a"),
        ("tenant-a", "tenant-a", "tenant-a"),
    ],
)
def test_ingest_tenant_resolution_accepts_explicit_scope(
    header_tenant_id: str | None,
    body_tenant_id: str | None,
    expected: str,
) -> None:
    assert _resolve_ingest_tenant_id(header_tenant_id, body_tenant_id) == expected
