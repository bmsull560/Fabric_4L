---
description: Break complex tasks into sub-tasks and execution plan
---

# Workflow Planner

Use this workflow to break complex tasks into manageable sub-tasks and create an execution plan.

## Parameters

- `task_description`: High-level task description (string, required)
- `constraints`: List of constraints (time, resources, dependencies) (optional)
- `available_tools`: List of available workflow/tool names (optional, default: all)
- `output_format`: SEQUENTIAL | PARALLEL | MIXED (default: MIXED)

## Steps

1. Parse the high-level task description
2. Identify required sub-tasks
3. Map sub-tasks to available workflows/tools
4. Determine dependencies between tasks
5. Create execution plan (sequential vs parallel)
6. Estimate completion time
7. Present plan for approval

## Output

Execution plan containing:
- Ordered list of sub-tasks
- Assigned workflows/tools per task
- Dependency graph
- Estimated timeline
- Required inputs/outputs at each step

## Example Use

"Plan the work for generating a complete business case for a new prospect"
