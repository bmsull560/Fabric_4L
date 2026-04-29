# jr (just ralph) for Windsurf
AI orchestration methodology adapted for single-agent use in Windsurf Cascade.

## Design Philosophy

- **Intentional context isolation** — Work on one ticket at a time with minimal, focused context. Do not let Cascade see or modify code outside the current task scope unless necessary.
- **Handoff via notes** — Log decisions, steps, and rationale as you work. When switching modes (code → review → revision), read the ticket description + notes + actual code. Preserve what matters without biasing toward a particular approach.
- **Early issue detection** — Catch issues early and surface them rather than grinding on a bad path. If you discover the task is fundamentally mis-scoped, stop and ask.
- **Leave no trace** — After any review or mutation testing, ensure the worktree is exactly as found. No stray commits, staged, or unstaged changes.

## Workflow (Manual Orchestration)

Windsurf has one agent, so you drive the workflow by invoking skills at each step.

### 1. Plan
- Invoke `@jr-plan` with your plan document or feature idea.
- Output: a markdown feature ticket + child task tickets in `.jr/tickets/`.

### 2. Implement
- Open the task ticket you want to work on.
- Invoke `@jr-coder` and paste the ticket ID or description.
- Cascade follows the skill: implements, tests, commits, and marks done.
- Repeat for each task in dependency order.

### 3. Code Review
- When a task is done, invoke `@jr-code-review` with the task context.
- Cascade follows the skill: reviews diff, tests, mutation checks, and verdicts (approve / changes / escalate).
- If changes are requested, return to step 2 for the same task.

### 4. Architect Review
- When all tasks in a feature are done, invoke `@jr-architect-review` with the feature context.
- Cascade follows the skill: reviews cross-task coherence, integration, downstream impact, and regression logic.
- Verdict: approve (feature done) or changes (reopen specific tasks and return to step 2).

### 5. Rebase / Merge
- If stacked branches or conflicts arise, invoke `@jr-rebase` for conflict resolution guidance.
- After architect approval, merge the feature branch.

### 6. Retro
- After a feature ships or stalls, invoke `@jr-retro` with the feature ID.
- Cascade analyzes friction patterns and produces actionable recommendations.

## Ticket Format

Tickets live in `.jr/tickets/<id>.md`:

```markdown
---
id: feat-001
type: feature
title: "Add dark mode toggle"
status: open | in-progress | review | done
parent: (for tasks)
assignee: jr-coder | jr-code-review | jr-architect-review | human
---

## Description
What this feature/task does.

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2

## Notes
- [2024-01-15] coder: Started implementation, discovered X
- [2024-01-15] code-review: CHANGES REQUESTED at `file.ts:42` ...
- [2024-01-16] coder: Fixed, tests pass
- [2024-01-16] code-review: Approved
```

## Git Conventions

- One feature = one branch = one PR.
- Feature branch naming: `feat/<id>-short-title`.
- Task commits: `feat-001-task-003: add toggle component`.
- Keep the worktree clean — no untracked files at review time.
