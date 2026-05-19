from pathlib import Path

from scripts.ci.check_layer3_legacy_tenant_dependency_imports import scan


def test_layer3_api_uses_secured_tenant_dependency() -> None:
    findings = scan(Path.cwd(), Path("services/layer3-knowledge/src/api"))
    assert findings == []
