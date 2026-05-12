from __future__ import annotations

from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
ENTITY_COMPAT = ROOT / "value_fabric/layer3/api/routes/entity_compat.py"
COMPAT_ALIASES = ROOT / "value_fabric/layer3/api/routes/compat_aliases.py"
APP_MONOLITH = ROOT / "value_fabric/layer3/api/app_monolith.py"


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"))


def _import_from_modules(tree: ast.Module) -> list[str]:
    modules: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
    return modules


def test_compat_shims_import_canonical_route_modules_and_export_router() -> None:
    entity_tree = _parse(ENTITY_COMPAT)
    alias_tree = _parse(COMPAT_ALIASES)

    assert "value_fabric.layer3.api.routes.entities" in _import_from_modules(entity_tree)
    assert "value_fabric.layer3.api.routes.query_search" in _import_from_modules(alias_tree)

    for tree in (entity_tree, alias_tree):
        all_assigns = [n for n in tree.body if isinstance(n, ast.Assign)]
        assert any(
            isinstance(target, ast.Name)
            and target.id == "__all__"
            and isinstance(assign.value, ast.List)
            and [elt.value for elt in assign.value.elts if isinstance(elt, ast.Constant)] == ["router"]
            for assign in all_assigns
            for target in assign.targets
        )


def test_compat_router_registration_does_not_shadow_canonical_mounts() -> None:
    source = APP_MONOLITH.read_text(encoding="utf-8")

    # Canonical entity router should remain mounted under /v1.
    assert "RouterMount(entities.router, prefix=\"/v1\")" in source

    # Compatibility aliases remain separately mounted and must not replace canonical mounts.
    assert "RouterMount(compat_aliases.router)" in source
    assert source.count("RouterMount(compat_aliases.router)") == 1
