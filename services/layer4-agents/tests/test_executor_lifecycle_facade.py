from __future__ import annotations

from datetime import UTC, datetime

import pytest

from value_fabric.layer4.engine.execution_dispatch import build_workflow_task
from value_fabric.layer4.engine.execution_validation import ensure_controller_accepts_execution
from value_fabric.layer4.engine.executor import WorkflowExecutionError


def test_validation_phase_raises_when_shutdown() -> None:
    with pytest.raises(WorkflowExecutionError):
        ensure_controller_accepts_execution(is_shutdown=True, error_cls=WorkflowExecutionError)


def test_dispatch_phase_builds_scheduler_task_shape() -> None:
    task = build_workflow_task(
        priority=3,
        workflow_id="wf-123",
        tenant_id="tenant-a",
        user_id="user-a",
        workflow_type="roi_calculator",
        workflow=object(),
        initial_state=object(),
        checkpoint_interval=5,
        handler=lambda *_args, **_kwargs: None,
    )
    assert task.task_id == "wf-wf-123"
    assert task.workflow_instance_id == "wf-123"
    assert task.tenant_id == "tenant-a"
    assert task.context["workflow_type"] == "roi_calculator"
    assert task.tenant_context["auth_source"] == "workflow_execution"
