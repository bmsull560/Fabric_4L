---
name: create_task
description: Creates tasks in project management systems
---

# Create Task

Create tasks in project management systems (Asana, Monday, ClickUp).

## Parameters

- `title`: string — Task title (required)
- `description`: string — Task description (required)
- `assignee`: string — Assigned user ID (optional)
- `due_date`: string — Due date ISO format (optional)
- `priority`: enum — low, medium, high (default: medium)
- `related_to`: object — Related entity references (optional)

## Steps

1. Validate PM provider configuration
2. Build provider-specific payload
3. Create task via API
4. Return task details and URL

## Output

Returns CreateTaskOutput with:
- `task_id`: Created task ID
- `success`: Boolean status
- `url`: Task URL in PM system
- `error`: Error message if failed
