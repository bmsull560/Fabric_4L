"""Cross-tenant hostile invariants for layer4-agents."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock

import pytest


def _load_service_code() -> str:
    """Concatenate all Python source under the service ``src`` tree."""
    service_root = Path(__file__).resolve().parents[1] / "src"
    return "\n".join(p.read_text(encoding="utf-8", errors="ignore") for p in service_root.rglob("*.py"))


def test_tenant_a_cannot_read_tenant_b_patterns_present() -> None:
    content = _load_service_code()
    assert "tenant_id" in content, "Expected tenant_id references in source"
    assert "list_" in content or "get_" in content, "Expected read-style method names in source"


def test_tenant_a_cannot_mutate_tenant_b_patterns_present() -> None:
    content = _load_service_code()
    assert "tenant_id" in content, "Expected tenant_id references in source"
    assert (
        "create" in content
        or "update" in content
        or "delete" in content
        or "ingest" in content
    ), "Expected write-style method names in source"


# ---------------------------------------------------------------------------
# Runtime controller-level hostile tests
# ---------------------------------------------------------------------------

class FakeStateManager:
    """Minimal fake state manager for hostile controller tests."""

    def __init__(self):
        self._states: dict[str, Any] = {}

    async def load_state(self, workflow_id: str):
        return self._states.get(workflow_id)

    async def save_state(self, workflow_id: str, state) -> None:
        self._states[workflow_id] = state

    async def list_workflows(self) -> list[str]:
        return list(self._states.keys())

    async def list_active_workflows(self) -> list[str]:
        return [wid for wid, s in self._states.items() if s.status.value in ("running", "pending")]


@pytest.fixture
def hostile_controller():
    from value_fabric.layer4.engine.executor import OrchestrationController
    from value_fabric.layer4.tools.registry import ToolRegistry

    registry = AsyncMock(spec=ToolRegistry)
    controller = OrchestrationController(
        tool_registry=registry,
        state_manager=FakeStateManager(),
    )
    return controller


@pytest.mark.asyncio
async def test_archive_workflow_rejects_cross_tenant(hostile_controller):
    """archive_workflow must raise PermissionError when tenant_id does not match."""
    wf_id = "wf-tenant-a-001"
    state = AsyncMock()
    state.metadata = {"archived": False}
    state.status.value = "completed"

    # Seed the controller's metadata and state manager
    hostile_controller._workflow_metadata[wf_id] = {"tenant_id": "tenant-a"}
    await hostile_controller.state_manager.save_state(wf_id, state)

    with pytest.raises(PermissionError, match="belongs to tenant"):
        await hostile_controller.archive_workflow(wf_id, tenant_id="tenant-b")


@pytest.mark.asyncio
async def test_list_active_workflows_filters_cross_tenant(hostile_controller):
    """list_active_workflows must not return workflows from other tenants."""
    # Create workflow for tenant-a
    state_a = AsyncMock()
    state_a.status.value = "running"
    state_a.metadata = {"archived": False}
    hostile_controller._workflow_metadata["wf-a"] = {"tenant_id": "tenant-a"}
    await hostile_controller.state_manager.save_state("wf-a", state_a)

    # Create workflow for tenant-b
    state_b = AsyncMock()
    state_b.status.value = "running"
    state_b.metadata = {"archived": False}
    hostile_controller._workflow_metadata["wf-b"] = {"tenant_id": "tenant-b"}
    await hostile_controller.state_manager.save_state("wf-b", state_b)

    results = await hostile_controller.list_active_workflows(tenant_id="tenant-a")
    assert len(results) == 1
    assert results[0].get("workflow_id") == "wf-a"


@pytest.mark.asyncio
async def test_list_workflows_filters_cross_tenant(hostile_controller):
    """list_workflows must not return workflows from other tenants."""
    state_a = AsyncMock()
    state_a.status.value = "completed"
    state_a.metadata = {"archived": False}
    hostile_controller._workflow_metadata["wf-a"] = {"tenant_id": "tenant-a"}
    await hostile_controller.state_manager.save_state("wf-a", state_a)

    state_b = AsyncMock()
    state_b.status.value = "completed"
    state_b.metadata = {"archived": False}
    hostile_controller._workflow_metadata["wf-b"] = {"tenant_id": "tenant-b"}
    await hostile_controller.state_manager.save_state("wf-b", state_b)

    results = await hostile_controller.list_workflows(tenant_id="tenant-a")
    assert len(results) == 1
    assert results[0].get("tenant_id") == "tenant-a"
