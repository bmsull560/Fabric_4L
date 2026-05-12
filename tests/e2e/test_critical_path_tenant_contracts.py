"""Critical-path release guardrails for tenant isolation and cross-layer contracts."""

from __future__ import annotations

from pathlib import Path


def test_layer4_contract_includes_tenant_header_requirements() -> None:
    contract = Path("contracts/openapi/layer4-agents.yaml").read_text(encoding="utf-8")
    assert "X-Tenant-ID" in contract
    assert "/v1/integrations/{provider}/sync" in contract


def test_value_engine_smoke_contract_enforces_tenant_header_behavior() -> None:
    smoke = Path("tests/e2e/test_value_engine_smoke_contract.py").read_text(encoding="utf-8")
    assert 'headers["X-Tenant-ID"] == "tenant-123"' in smoke


def test_k8s_prod_overlay_uses_digest_pinned_images() -> None:
    prod_overlay = Path("k8s/envs/prod/kustomization.yaml").read_text(encoding="utf-8")
    assert "digest: sha256:" in prod_overlay
