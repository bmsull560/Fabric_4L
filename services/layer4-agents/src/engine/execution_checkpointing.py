from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..models.agent_state import WorkflowStatus


async def persist_interruption_if_needed(*, state_manager: Any, workflow_id: str) -> None:
    paused = await state_manager.load_state(workflow_id)
    if paused and paused.status in {WorkflowStatus.PAUSED, WorkflowStatus.INTERRUPTED}:
        return
    if paused:
        paused.status = WorkflowStatus.INTERRUPTED
        paused.metadata["interrupted_at"] = datetime.now(UTC).isoformat()
        paused.metadata["interruption_reason"] = "task cancellation"
        await state_manager.save_state(workflow_id, paused)
