# Workspace Persistence Baseline Cleanup Evidence

Author: **Manus AI**  
Date: **2026-05-05**

## Summary

This cleanup resolves the single remaining web Vitest baseline failure that remained after the graph/OpenAPI stabilization sprint. The failure was isolated to `src/hooks/useWorkspaceCase.test.ts > usePersistWorkspaceTab > should persist tab data`, where the test still expected an unsupported workflow side effect through `POST /workflows` with `workflow_type: 'workspace_tab_persist'`.

The current hook implementation persists workspace tab data directly through `PUT /analysis/cases/{caseId}/workspace/{tabKey}` and returns the response payload. Repository-wide exact search confirmed that `workspace_tab_persist` existed only in the stale frontend test assertion, not in supported workflow schemas or implementation references. The minimal fix therefore updates the test expectation to assert the direct workspace persistence behavior and explicitly verifies that no workflow creation call is emitted.

## Change Details

| File | Change | Rationale |
|---|---|---|
| `apps/web/src/hooks/useWorkspaceCase.test.ts` | Removed the stale `apiClient.post('l4', '/workflows', ...)` mock and assertion from `usePersistWorkspaceTab`. | The hook no longer creates a workflow when persisting workspace tab data. |
| `apps/web/src/hooks/useWorkspaceCase.test.ts` | Added an assertion that `result.current.data` equals the direct `PUT` response payload. | Locks the observable hook contract to the direct persistence result. |
| `apps/web/src/hooks/useWorkspaceCase.test.ts` | Added `expect(apiClient.post).not.toHaveBeenCalled()`. | Prevents accidental reintroduction of the unsupported workflow side effect. |

## Validation Evidence

| Check | Result | Evidence |
|---|---:|---|
| Focused workspace persistence validation | PASS | `pnpm exec vitest run src/hooks/useWorkspaceCase.test.ts` completed with **1 passed file** and **13 passed tests**. |
| Full web Vitest suite | PASS | `pnpm run test` completed with **86 passed files** and **1,238 passed tests**. |
| Frontend TypeScript check | PASS | `pnpm run check` completed successfully in `apps/web` with `tsc --noEmit`. |

## Outcome

The web Vitest persistence baseline is now clean. The prior broad-suite result of **85 passed files / 1,237 passed tests / 1 failing test** has been restored to a clean **86 passed files / 1,238 passed tests** result, with the workspace persistence test aligned to the currently supported direct tab-persistence contract.
