from pathlib import Path


def test_layer1_compatibility_routes_emit_deprecation_telemetry_contract() -> None:
    source = Path("value_fabric/layer1/api/routes/compatibility.py").read_text(encoding="utf-8")

    assert "layer1_compatibility_route_accessed" in source
    assert 'response.headers["Deprecation"] = "true"' in source
    assert 'response.headers["Sunset"] = _DEPRECATION_REMOVAL_DATE' in source


def test_frontend_uses_canonical_command_center_route_only() -> None:
    source = Path("apps/web/src/shell/router.tsx").read_text(encoding="utf-8")

    assert 'path: "/command-center"' in source
    assert 'path: "/context/command-center"' not in source
