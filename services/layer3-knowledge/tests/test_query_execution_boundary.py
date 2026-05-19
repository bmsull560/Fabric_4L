"""Regression tests for the Layer 3 approved Neo4j execution boundary."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from db.query_execution import TenantQueryValidationError, run_validated_query


REPO_ROOT = Path(__file__).resolve().parents[3]
HIGH_RISK_RUNTIME_ROOTS = (
    REPO_ROOT / "services" / "layer3-knowledge" / "src" / "api" / "routes",
    REPO_ROOT / "services" / "layer3-knowledge" / "src" / "services",
    REPO_ROOT / "services" / "layer3-knowledge" / "src" / "agents",
    REPO_ROOT / "services" / "layer3-knowledge" / "src" / "analytics",
)
ALLOWED_SYSTEM_SCOPED_PATH_FRAGMENTS = (
    "services/layer3-knowledge/src/schema/",
    "services/layer3-knowledge/src/migrations/",
    "services/layer3-knowledge/src/bootstrap/",
)


class _DirectSessionRunVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.violations: list[tuple[int, int]] = []

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802 - ast visitor hook
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and func.attr == "run"
            and isinstance(func.value, ast.Name)
            and func.value.id == "session"
        ):
            self.violations.append((node.lineno, node.col_offset))
        self.generic_visit(node)


def test_high_risk_runtime_modules_use_approved_execution_boundary() -> None:
    """High-risk runtime modules must use approved wrappers (system scopes allowlisted)."""

    violations: list[str] = []
    for root in HIGH_RISK_RUNTIME_ROOTS:
        for path in root.rglob("*.py"):
            rel = path.relative_to(REPO_ROOT).as_posix()
            if any(rel.startswith(fragment) for fragment in ALLOWED_SYSTEM_SCOPED_PATH_FRAGMENTS):
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            visitor = _DirectSessionRunVisitor()
            visitor.visit(tree)
            for line, col in visitor.violations:
                violations.append(f"{rel}:{line}:{col}")

    assert not violations, "direct session.run calls found in high-risk runtime modules:\n" + "\n".join(violations)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "query",
    [
        "MATCH (e:Entity) RETURN e",
        "MATCH (p:Product {id: $id}) RETURN p",
        "MATCH (e:Evidence)-[:SUPPORTS]->(d:ValueDriver {tenant_id: $tenant_id}) RETURN e, d",
    ],
)
async def test_tenant_owned_label_queries_fail_closed_without_tenant_predicates(query: str) -> None:
    """Tenant-owned labels require explicit tenant predicates before execution."""

    class FakeSession:
        async def run(self, query, params):  # pragma: no cover - must not execute
            raise AssertionError(f"unsafe query unexpectedly executed: {query} {params}")

    with pytest.raises(TenantQueryValidationError, match="missing tenant scoping"):
        await run_validated_query(FakeSession(), query, {"id": "shared-id", "tenant_id": "tenant-a"})


@pytest.mark.asyncio
async def test_tenant_owned_label_query_executes_when_every_label_is_scoped() -> None:
    """Scoped tenant-owned label queries are delegated with forced tenant params."""

    class FakeSession:
        def __init__(self) -> None:
            self.calls: list[tuple[str, dict]] = []

        async def run(self, query, params):
            self.calls.append((query, params))
            return ["ok"]

    fake = FakeSession()
    query = """
    MATCH (e:Entity {tenant_id: $tenant_id})-[:SUPPORTS]->(d:ValueDriver)
    WHERE d.tenant_id = $tenant_id
    RETURN e, d
    """

    result = await run_validated_query(fake, query, {"tenant_id": "spoofed"}, tenant_id="tenant-a")

    assert result == ["ok"]
    assert fake.calls == [(query, {"tenant_id": "tenant-a", "_tenant_id": "tenant-a"})]
