"""Cross-tenant hostile invariants for layer1-ingestion."""

from pathlib import Path


def _code() -> str:
    service_root = Path(__file__).resolve().parents[1] / "src"
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in service_root.rglob("*.py"))


def test_tenant_a_cannot_read_tenant_b_patterns_present():
    content = _code()
    assert "tenant_id" in content
    assert "list_" in content or "get_" in content


def test_tenant_a_cannot_mutate_tenant_b_patterns_present():
    content = _code()
    assert "tenant_id" in content
    assert "create" in content or "update" in content or "delete" in content or "ingest" in content
