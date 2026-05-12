from __future__ import annotations

import ast
from pathlib import Path


def _load_module(path: str) -> ast.Module:
    return ast.parse(Path(path).read_text(encoding="utf-8"))


def test_layer1_compatibility_routes_emit_deprecation_telemetry_contract() -> None:
    module = _load_module("value_fabric/layer1/api/routes/compatibility.py")
    source = ast.unparse(module)

    assert "layer1_compatibility_route_accessed" in source
    assert '_DEPRECATION_REMOVAL_DATE = "2026-12-31"' in source
    assert 'response.headers["Deprecation"] = "true"' in source
    assert 'response.headers["Sunset"] = _DEPRECATION_REMOVAL_DATE' in source


def test_frontend_uses_canonical_command_center_route_only() -> None:
    source = Path("apps/web/src/shell/router.tsx").read_text(encoding="utf-8")

    assert 'path: "/command-center"' in source
    assert 'path: "/context/command-center"' not in source
