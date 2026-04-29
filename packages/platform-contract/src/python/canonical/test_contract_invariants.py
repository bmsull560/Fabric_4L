"""Invariant and negative tests for platform canonical Python contracts."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_context_tenant_propagation_fields_and_validation() -> None:
    src = _read("context.py")
    tree = ast.parse(src)
    request_context = next(
        n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "RequestContext"
    )
    ann_fields = {n.target.id for n in request_context.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)}

    required_fields = {"tenant_id", "isolation_tier", "auth_source", "service_account_scopes"}
    missing = required_fields - ann_fields
    assert not missing, f"RequestContext missing tenant propagation fields: {sorted(missing)}"
    assert "Invalid isolation_tier" in src
    assert "Invalid auth_source" in src


def test_tool_boundary_contract_shapes_are_present() -> None:
    src = _read("tool_boundary.py")
    assert "input_schema" in src and "output_schema" in src, "Tool boundary must define input/output schema handles"
    assert "async def execute" in src, "Tools must expose async execute()"
    assert "Must return a Pydantic model or dict" in src


def test_database_lifecycle_contract_rules_documented() -> None:
    src = _read("database.py")
    for required in [
        "SET LOCAL app.tenant_id",
        "Commit on success, rollback on exception",
        "MUST NOT call commit/rollback manually",
    ]:
        assert required in src, f"DB lifecycle invariant missing: {required}"


def test_negative_database_contract_has_actionable_syntax_error_message() -> None:
    src = _read("database.py")
    try:
        compile(src, "database.py", "exec")
    except SyntaxError as err:
        assert "invalid syntax" in str(err)
        assert err.lineno == 7
    else:
        raise AssertionError("Expected intentional violation to fail compilation for enforcement coverage")


def test_negative_context_rejects_invalid_isolation_tier_message() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location("contract_context", ROOT / "context.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    ctx = module.RequestContext(isolation_tier="bogus")
    errors = ctx.validate()
    assert "Invalid isolation_tier: bogus" in errors
