# Type Alignment Sprint 11: Graph/OpenAPI Fixture Stabilization Evidence

Author: **Manus AI**
Date: 2026-05-05
Repository: `bmsull560/Fabric_4L`

## Summary

Sprint 11 addressed the graph and OpenAPI fixture failures that were identified as the highest-value follow-up after Sprint 10. The stabilization work kept production behavior and fixtures aligned with the canonical frontend domain model: graph hooks now call the Layer 3 subgraph base route consistently, default MSW graph fixtures return a coherent two-node subgraph, OpenAPI contract fixtures include the required `tenant_id` field on `TruthObjectResponse`, and hook-result assertions now inspect the camelCase domain fields produced by the graph mappers.

The sprint deliberately focused on **fixture and assertion drift**, rather than broad feature refactoring. DTO-shaped mock payloads remain DTO-shaped at API boundaries, while hook consumers and graph utility checks now assert the domain model returned after parser validation and mapper conversion.

## Changed Files

| File | Purpose |
|---|---|
| `apps/web/src/hooks/useGraphQuery.ts` | Aligns `useSubgraph` with the Layer 3 `/subgraph` base route that the MSW and API-client layer already expect. |
| `apps/web/src/test/mocks/handlers.ts` | Stabilizes default graph fixtures to return a coherent two-node, one-edge subgraph and adds `tenant_id` to default TruthObject mock data. |
| `apps/web/src/api/__tests__/contract/_helpers.ts` | Updates the local contract-test helper schema and fixture factory so `TruthObjectResponse` includes the canonical required `tenant_id` field. |
| `apps/web/src/hooks/useGraphQuery.test.ts` | Updates graph hook assertions from DTO snake_case field names to the domain field names returned by the hooks. |
| `apps/web/src/hooks/useGraphQuery.comprehensive.test.ts` | Updates actual hook-result assertions to domain field names while preserving DTO-style fixture factories and type-guard checks where they intentionally validate API payload shape. |
| `apps/web/src/hooks/useGraphQuery.integration.test.ts` | Updates integration assertions to use mapped graph domain fields such as `sourceId`, `targetId`, `totalNodes`, `totalEdges`, and `pathCount`. |
| `apps/web/src/hooks/useGraphQuery.property.test.ts` | Updates property checks to verify domain-level graph invariants after parser mapping. |
| `apps/web/src/lib/graph-utils.ts` | Makes pure graph utility helpers tolerant of both canonical domain nodes and legacy DTO-shaped test nodes when deriving entity type. |

## Stabilization Scope

The graph failures had two related causes. First, the hook route and mock route drifted apart, so default subgraph calls did not consistently hit the intended MSW handler. Second, several tests asserted raw DTO field names after the graph hook had already validated and mapped responses into the frontend domain model.

| Area | Stabilized Behavior | Boundary Preserved |
|---|---|---|
| Layer 3 subgraph route | `useSubgraph` now requests `/subgraph` through the Layer 3 API client base, avoiding duplicate `/graph/subgraph` path composition. | The API client layer remains responsible for adding the Layer 3 base path. |
| Default graph fixtures | Default subgraph responses expose two nodes and one coherent edge, matching hook tests that expect a connected graph. | MSW payloads remain API DTOs before hook-level parsing. |
| Hook result assertions | Tests now assert `confidenceScore`, `entityCount`, `pathCount`, `sourceId`, `targetId`, `totalNodes`, and `totalEdges` on returned hook data. | DTO factory/type-guard sections continue to validate DTO field names where that is the intended subject. |
| OpenAPI TruthObject fixture | Contract fixtures and helper schema now include `tenant_id`, matching the required response field. | The contract helper remains a local test schema and fixture factory; generated types were not modified in this sprint. |
| Graph utilities | Utility functions derive entity type from either `entityType` or legacy `entity_type` test input. | Domain-shaped nodes remain the canonical production shape. |

## Regression Validation Evidence

Validation was run after the graph route, fixture, assertion, and OpenAPI helper updates. The focused graph/OpenAPI tests passed, and the TypeScript check completed successfully. The full web Vitest suite improved from the Sprint 10 handoff state to a single isolated workspace-tab test failure that also reproduces by itself and is therefore outside the graph/OpenAPI stabilization scope.

| Check | Result | Evidence |
|---|---:|---|
| Focused Sprint 11 graph/OpenAPI validation | PASS | `pnpm exec vitest run src/hooks/useGraphQuery.test.ts src/hooks/useGraphQuery.comprehensive.test.ts src/api/__tests__/contract/openapi-drift.contract.test.ts` completed with **3 passed files** and **87 passed tests** after the route, fixture, and domain-assertion updates. |
| Additional graph regression validation | PASS | `pnpm exec vitest run src/hooks/useGraphQuery.integration.test.ts src/hooks/useGraphQuery.property.test.ts src/lib/graph-utils.test.ts` completed with **3 passed files** and **57 passed tests**. |
| Frontend TypeScript check | PASS | `pnpm run check` completed successfully in `apps/web` with `tsc --noEmit`. |
| Full web Vitest suite | NON-BLOCKING BASELINE FAILURE | `pnpm run test` executed **86 files / 1,238 tests**, with **85 files / 1,237 tests passing** and a single failure in `src/hooks/useWorkspaceCase.test.ts > usePersistWorkspaceTab > should persist tab data`. |
| Workspace baseline isolation | REPRODUCED OUTSIDE SPRINT SCOPE | `pnpm exec vitest run src/hooks/useWorkspaceCase.test.ts` reproduced the same single assertion failure in isolation: the test expects `apiClient.post('l4', '/workflows', ...)`, while the current hook implementation persists via `apiClient.put('l4', '/analysis/cases/{caseId}/workspace/{tabKey}', payload)`. |

## Outcome

Sprint 11 resolved the graph and OpenAPI fixture drift that blocked confidence in the broad web regression suite. All graph hook suites touched by the stabilization now pass under focused validation, the OpenAPI drift contract no longer fails on the missing `tenant_id` TruthObject fixture field, graph utility coverage passes with both domain and legacy fixture shapes, and TypeScript remains clean.

The only remaining broad-suite failure is not a graph or OpenAPI regression. It is an isolated workspace-tab persistence expectation mismatch that was confirmed by running `useWorkspaceCase.test.ts` independently. That test should be handled in a separate workspace persistence cleanup sprint so this commit remains scoped to the requested graph/OpenAPI stabilization.

## Residual Risks and Follow-Up

| Follow-Up | Recommended Priority | Rationale |
|---|---:|---|
| Resolve `useWorkspaceCase.test.ts` persistence expectation drift | P1 | Full `pnpm run test` is down to one isolated non-graph failure, so fixing this workspace baseline would restore a fully green broad Vitest gate. |
| Keep graph tests explicit about DTO vs domain assertions | P1 | Future graph fixture changes should preserve the distinction between API payload validation and hook consumer behavior. |
| Add a regression note for Layer 3 route composition | P2 | The `/subgraph` hook route depends on the API client base path; documenting that convention can prevent reintroducing `/graph/subgraph` duplication. |
