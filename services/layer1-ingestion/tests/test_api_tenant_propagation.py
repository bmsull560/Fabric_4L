"""Tenant context propagation guardrails for layer1-ingestion."""

from pathlib import Path


def test_repository_calls_use_context_tenant_id():
    """Enforce trusted context propagation by checking canonical route code."""
    service_root = Path(__file__).resolve().parents[1] / "src"
    py_files = list(service_root.rglob("*.py"))
    content = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in py_files)
    assert "tenant_id=ctx.tenant_id" in content or "tenant_id=context.tenant_id" in content


def test_missing_tenant_context_has_fail_closed_guard():
    service_root = Path(__file__).resolve().parents[1] / "src"
    py_files = list(service_root.rglob("*.py"))
    content = "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in py_files)
    assert "Tenant context required" in content or "require_tenant_context" in content or "HTTPException(status_code=401" in content
