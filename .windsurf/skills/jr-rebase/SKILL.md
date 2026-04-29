---
name: jr-rebase
description: "Resolve git rebase conflicts in feature branches. Use when a rebase has conflicts that need resolution."
---

You are an expert at resolving git rebase conflicts. Follow this procedure to produce correct, functional code.

## Context Gathering

1. Identify the feature being rebased and the upstream branch or commit.
2. Read the feature ticket for intent.
3. Read the upstream feature ticket (if one exists) to understand what upstream implemented.
4. Run `git status` to identify conflicting files and rebase state.

## Scenarios

**Upstream merged (no worktree exists):**
- The upstream feature was squash-merged to main.
- Use `git show <merge-commit>:<file>` to see the upstream final state.
- The upstream ticket notes are valuable context.

**Upstream not yet merged:**
- The upstream feature branch still exists.
- You can examine the upstream branch directly to understand its changes.

## Conflict Resolution

For each conflicting file:
1. Read the file and locate conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`).
2. Understand both sides:
   - `HEAD` (ours) = the target you are rebasing onto.
   - Incoming (theirs) = your feature's changes being replayed.
3. Gather context from both feature tickets to understand intent.
4. Resolve based on context:
   - Preserve your feature's intended functionality.
   - Incorporate necessary upstream changes (they were merged for a reason).
   - When both sides changed the same code, determine the correct version based on ticket context.
5. Edit to remove conflict markers and produce correct code.
6. Stage: `git add <file>`.

After resolving all conflicts in the current commit:
```sh
git rebase --continue
```

If more conflicts surface (multi-commit rebase), repeat the process.

## Completion

When the rebase completes successfully:
1. Add a note to the feature ticket:
   ```
   [YYYY-MM-DD] rebase: Conflicts: <files>. Resolution: <brief summary>.
   ```
2. Verify the worktree is clean and tests pass.
3. Tell the user the rebase is complete.

## Escalation

Escalate to the user if:
- Semantic conflicts where you cannot determine the correct resolution.
- File deletions vs modifications where intent is unclear.
- Complex conflicts requiring human judgment.

Do NOT abort the rebase — leave it in progress for manual resolution if escalating.
