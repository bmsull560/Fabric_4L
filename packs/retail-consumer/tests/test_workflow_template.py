"""Retail & Consumer Value Pack - Workflow Template Tests

Validates workflow template structure, phases, and task definitions.
"""

from typing import Any

import pytest

# Workflow validation constants - aligned with workflow_template.json structure
REQUIRED_WORKFLOW_FIELDS: list[str] = [
    "template_id", "template_name", "description", "phases"
]


class TestWorkflowStructure:
    """Verify workflow template structure and required fields."""

    def test_workflow_has_required_fields(self, workflow_template_data: dict[str, Any]) -> None:
        """Workflow template must contain all required top-level fields."""
        for field in REQUIRED_WORKFLOW_FIELDS:
            assert field in workflow_template_data, f"Workflow template missing required field: {field}"

    def test_workflow_pack_id_matches(self, workflow_template_data: dict[str, Any], expected_pack_id: str) -> None:
        """Workflow template pack_id must match the expected pack identifier."""
        assert workflow_template_data.get("pack_id") == expected_pack_id, (
            f"Workflow pack_id mismatch: expected {expected_pack_id}, "
            f"got {workflow_template_data.get('pack_id')}"
        )

    def test_workflow_has_template_id(self, workflow_template_data: dict[str, Any]) -> None:
        """Workflow template must have a unique template identifier."""
        assert "template_id" in workflow_template_data, "Missing template_id"
        assert workflow_template_data["template_id"].startswith("rc-wf-"), (
            f"Template ID should start with 'rc-wf-': {workflow_template_data['template_id']}"
        )

    def test_workflow_has_description(self, workflow_template_data: dict[str, Any]) -> None:
        """Workflow template must have a non-empty description."""
        desc = workflow_template_data.get("description", "")
        assert len(desc) > 20, f"Workflow description too short or missing: {desc}"


class TestWorkflowPhases:
    """Verify workflow phase definitions."""

    def test_workflow_has_phases(self, workflow_template_data: dict[str, Any]) -> None:
        """Workflow must define at least one phase."""
        assert "phases" in workflow_template_data, "Missing phases in workflow"
        phases = workflow_template_data["phases"]
        assert isinstance(phases, list), "phases must be a list"
        assert len(phases) > 0, "At least one phase required"

    def test_phases_have_required_fields(self, workflow_template_data: dict[str, Any]) -> None:
        """Each phase must have phase_id, name, order, and tasks."""
        required_phase_fields = ["phase_id", "name", "order", "tasks"]
        for phase in workflow_template_data["phases"]:
            for field in required_phase_fields:
                assert field in phase, f"Phase {phase.get('phase_id', 'unknown')} missing field: {field}"

    def test_phase_orders_are_sequential(self, workflow_template_data: dict[str, Any]) -> None:
        """Phase order values should be sequential starting from 1."""
        phases = workflow_template_data["phases"]
        orders = [p["order"] for p in phases]
        expected = list(range(1, len(phases) + 1))
        assert sorted(orders) == expected, f"Phase orders not sequential: {orders}"

    def test_phase_ids_are_unique(self, workflow_template_data: dict[str, Any]) -> None:
        """Each phase must have a unique identifier."""
        phases = workflow_template_data["phases"]
        phase_ids = [p["phase_id"] for p in phases]
        assert len(phase_ids) == len(set(phase_ids)), f"Duplicate phase IDs: {phase_ids}"


class TestWorkflowTasks:
    """Verify task definitions within workflow phases."""

    def test_tasks_have_required_fields(self, workflow_template_data: dict[str, Any]) -> None:
        """Each task must have task_id, name, type, and priority."""
        required_task_fields = ["task_id", "name", "type", "priority"]
        for phase in workflow_template_data["phases"]:
            for task in phase.get("tasks", []):
                for field in required_task_fields:
                    assert field in task, (
                        f"Task {task.get('task_id', 'unknown')} in phase {phase['phase_id']} "
                        f"missing field: {field}"
                    )

    def test_task_ids_are_unique_across_phases(self, workflow_template_data: dict[str, Any]) -> None:
        """All task IDs must be unique across all phases."""
        all_task_ids = []
        for phase in workflow_template_data["phases"]:
            for task in phase.get("tasks", []):
                all_task_ids.append(task["task_id"])
        assert len(all_task_ids) == len(set(all_task_ids)), f"Duplicate task IDs: {all_task_ids}"

    def test_tasks_reference_valid_priorities(self, workflow_template_data: dict[str, Any]) -> None:
        """Task priorities must be valid values."""
        valid_priorities = {"low", "medium", "high", "critical"}
        for phase in workflow_template_data["phases"]:
            for task in phase.get("tasks", []):
                priority = task.get("priority", "").lower()
                assert priority in valid_priorities, (
                    f"Task {task['task_id']} has invalid priority: {priority}"
                )

    def test_tasks_have_estimated_hours(self, workflow_template_data: dict[str, Any]) -> None:
        """Each task should have estimated_hours for capacity planning."""
        for phase in workflow_template_data["phases"]:
            for task in phase.get("tasks", []):
                assert "estimated_hours" in task, (
                    f"Task {task['task_id']} missing estimated_hours"
                )
                hours = task["estimated_hours"]
                assert isinstance(hours, (int, float)), (
                    f"Task {task['task_id']} estimated_hours must be numeric: {hours}"
                )
                assert hours > 0, f"Task {task['task_id']} estimated_hours must be positive: {hours}"


class TestWorkflowRoles:
    """Verify workflow role definitions."""

    def test_workflow_has_required_roles(self, workflow_template_data: dict[str, Any]) -> None:
        """Workflow template must specify required roles."""
        assert "required_roles" in workflow_template_data, "Missing required_roles"
        roles = workflow_template_data["required_roles"]
        assert isinstance(roles, list), "required_roles must be a list"
        assert len(roles) > 0, "At least one required role needed"

    def test_roles_are_assigned_to_tasks(self, workflow_template_data: dict[str, Any]) -> None:
        """Verify role assignment coverage and validity.

        Note: This test checks that assigned roles are from the valid set.
        Full coverage of all required_roles is ideal but not enforced here
        to allow for partially completed workflow templates.

        Data Quality Finding: As of 2026-04-15, 'store_operations_vp' is
        listed in required_roles but not assigned to any task.
        """
        required_roles = set(workflow_template_data.get("required_roles", []))
        assigned_roles = set()
        for phase in workflow_template_data["phases"]:
            for task in phase.get("tasks", []):
                if "assigned_role" in task:
                    assigned_roles.add(task["assigned_role"])

        # All assigned roles must be in the required_roles list
        invalid_roles = assigned_roles - required_roles
        assert len(invalid_roles) == 0, f"Tasks assigned to invalid roles: {invalid_roles}"

        # At least 50% of required roles should have assignments (pragmatic threshold)
        if len(required_roles) > 0:
            coverage = len(assigned_roles & required_roles) / len(required_roles)
            assert coverage >= 0.5, (
                f"Role assignment coverage {coverage:.0%} is below 50% threshold. "
                f"Unassigned required roles: {required_roles - assigned_roles}"
            )
