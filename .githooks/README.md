# Fabric 4L — Git Hooks

This directory contains git hooks that enforce production gate checks locally before code leaves your machine.

## Quick Setup

Run once after cloning (or use `make setup-hooks`):

```bash
git config core.hooksPath .githooks
```

This tells git to use the hooks in this directory instead of the default `.git/hooks/`.

## What the Pre-Push Hook Does

Before every `git push`, the hook runs the full production gate test suite (82 tests, ~0.6s). If any test fails, the push is **blocked**.

The gate tests cover six critical domains:

| Gate | Domain | What It Catches |
|------|--------|-----------------|
| S2-A | Tenant context contract | Raw `get_db` usage (RLS bypass), missing auth on endpoints |
| S2-B | Cross-tenant API isolation | Workflow auth gaps, dependency audit failures |
| S2-C | RLS enforcement | Missing/broken RLS policies, unsafe migration patterns |
| S2-H | Export tenant access | Unauthenticated exports, S3 keys without tenant namespace |
| S1-A | State alignment | Frontend/backend enum drift (WorkflowStatus, WorkflowType) |
| S2-J | Startup validation | Weak JWT secrets, RLS disabled, superuser connections |

## Why This Exists

Fabric 4L uses AI agents extensively for code generation. Agents write fast but do not inherently know the project's security invariants. This hook is the safety net that catches what agents — and humans — miss.

**Real example:** After a merge, 5 new endpoints were found to bypass tenant isolation because the agent used `get_db` instead of `get_db_from_context`. The gate tests caught this immediately.

## Emergency Bypass

If you absolutely must push without running gates (e.g., documentation-only change):

```bash
git push --no-verify
```

Use sparingly. The CI gate on GitHub will still catch failures on the PR.

## For New Developers / Agents

If you are an AI agent or a new developer:

1. Run `make setup-hooks` after cloning
2. Never use `get_db` in route handlers — use `get_db_from_context`
3. Never create an endpoint without `require_authenticated` (unless it is a documented pre-auth flow)
4. If you add a new `WorkflowStatus` or `WorkflowType`, update both backend and frontend
5. If the pre-push hook blocks you, **fix the code** — do not bypass
