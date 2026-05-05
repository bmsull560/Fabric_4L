# Fabric_4L Type Alignment Sprint 2 Runtime Boundary Evidence

**Author:** Manus AI  
**Date:** 2026-05-05  
**Scope:** Frontend runtime boundary validation and DTO-to-domain migration slice for the ground-truth governance hooks.

## Executive Summary

Sprint 2 established the first focused runtime-validation migration slice after the contract freshness gate was added. The selected boundary was `apps/web/src/hooks/useGroundTruthGovernance.ts` because repository audit evidence showed that it exposed generated Layer 5 DTO aliases directly to hook consumers. The migration now routes Layer 5 ground-truth responses through a domain-owned Zod schema module before TanStack Query publishes data to UI consumers.

The implementation preserves the existing API surface for hook consumers while changing the ownership model. Generated DTO types remain a regeneration artifact under `apps/web/src/api/generated/`, but the hook now exports domain-owned types from `apps/web/src/lib/schemas/groundTruthGovernance.ts`. This means frontend feature code depends on a stable domain contract and receives explicit runtime parse failures when backend response shape drift reaches the trust boundary.

| Sprint 2 Objective | Result | Evidence |
|---|---:|---|
| Remove generated DTO leakage from the selected hook boundary | PASS | `useGroundTruthGovernance.ts` no longer imports `@/api/generated`, `components["schemas"]`, or generated operation aliases. |
| Add runtime validation at the API-to-query boundary | PASS | `groundTruthGovernance.ts` defines Zod schemas and parser functions for truth lists, audit events, freshness summary, stale truths, and the maturity ladder. |
| Preserve frontend typechecking | PASS | `pnpm run check` completed successfully in `apps/web`. |
| Preserve deterministic contract freshness | PASS | `scripts/ci/check_contract_freshness.sh` completed successfully after OpenAPI and generated-type regeneration. |
| Repair stale generated operation alias exposed by regenerated contracts | PASS | `valuePackFramework.ts` now uses the current Layer 3 operation key generated from the OpenAPI source. |

## Implemented Changes

The migration introduced a new domain schema module at `apps/web/src/lib/schemas/groundTruthGovernance.ts`. This module owns the frontend domain types for the selected boundary and provides parser functions that accept `unknown` transport payloads. It covers the response families currently returned by the ground-truth governance hooks.

| File | Change | Rationale |
|---|---|---|
| `apps/web/src/lib/schemas/groundTruthGovernance.ts` | Added Zod schemas, inferred domain types, and parser functions. | Moves the trust boundary from generated DTO aliases to explicit runtime validation. |
| `apps/web/src/hooks/useGroundTruthGovernance.ts` | Replaced generated DTO imports and cast-based response handling with domain parser calls. | Prevents raw DTO leakage to hook consumers and makes backend drift observable at the boundary. |
| `apps/web/src/api/valuePackFramework.ts` | Updated the stale Layer 3 operation alias to `list_valuepacks_v1_valuepacks_get`. | Keeps frontend typechecking aligned with regenerated OpenAPI output from Sprint 1. |

## Boundary Design

The selected boundary now follows a three-step contract path. First, `apiClient.get(...)` returns transport data and the hook treats `response.data` as `unknown`. Second, a domain parser such as `parseTruthObjectListResponse` validates the transport payload through Zod. Third, TanStack Query publishes the parsed domain result through strongly typed hook generics.

| Boundary Step | Before Sprint 2 | After Sprint 2 |
|---|---|---|
| Transport response | Cast directly to generated OpenAPI response aliases. | Read as `unknown` at the API boundary. |
| Runtime validation | No explicit parser in the selected hook. | Zod parser functions validate response shapes before publication. |
| Published hook types | Generated DTO aliases leaked from `@/api/generated/l5-types`. | Domain-owned schema-inferred types exported from `@/lib/schemas/groundTruthGovernance`. |
| Drift behavior | Shape mismatch could remain latent until UI access. | Shape mismatch fails during parser execution at the query boundary. |

The implementation intentionally uses `.passthrough()` on response object schemas. This preserves forward-compatible additive backend fields while still requiring the fields used by the frontend domain. The approach gives Sprint 2 a practical migration baseline: missing or invalid required fields fail fast, while harmless server additions do not break the UI prematurely.

## Validation Evidence

Targeted validation was run after the migration and after the generated Layer 3 operation alias repair. The validation command checked for raw DTO leakage in the migrated hook, confirmed parser exports, ran the frontend typechecker, executed the contract freshness gate, and inspected the resulting change set.

| Validation Check | Command or Probe | Result |
|---|---|---:|
| DTO leakage check | `grep -n "@/api/generated\|components[\"schemas\"]\| as components" apps/web/src/hooks/useGroundTruthGovernance.ts` | PASS, no matches. |
| Parser presence check | `grep -n "parseTruthObjectListResponse\|parseStaleTruthsResponse\|parseMaturityLadderResponse" apps/web/src/lib/schemas/groundTruthGovernance.ts` | PASS, parser exports present. |
| Frontend static typecheck | `cd apps/web && pnpm run check` | PASS. |
| Contract freshness gate | `scripts/ci/check_contract_freshness.sh` | PASS. |

The contract freshness gate regenerated the OpenAPI source-of-truth files and frontend generated DTOs, then reported that no committed drift remained. The validation log also showed the expected repository status containing only the Sprint 2 source changes and temporary audit files before cleanup.

## Residual Risks and Follow-Up

Sprint 2 deliberately migrated one high-signal hook boundary rather than attempting a broad refactor. The remaining frontend generated DTO imports discovered in Sprint 0 and Sprint 2 audits should be migrated incrementally through the same pattern: generated DTOs may be used as inputs to schema design and contract regeneration, but UI-facing hooks should publish domain-owned schema-inferred types.

| Residual Item | Status | Recommended Next Action |
|---|---|---|
| Other hooks and API modules still import generated DTO aliases directly. | Open | Select the next high-traffic TanStack Query hook and apply the same parser-boundary migration. |
| Runtime parser tests are not yet dedicated for the new ground-truth governance schemas. | Open | Add focused unit tests with representative valid payloads and drift payloads. |
| The no-new-drift policy is documented but not yet fully automated for all raw generated imports. | Open | Add a repository-owned lint or grep gate that prevents newly introduced generated DTO leakage outside approved adapter directories. |
| Signals OpenAPI remains static from Sprint 1. | Open | Identify or add the signals service FastAPI source before treating signals as a regenerated source-of-truth contract. |

## Handoff Recommendation

The next sprint should convert the Sprint 2 pattern into a repeatable enforcement path. The highest-value next step is to add a small contract-boundary test suite for `groundTruthGovernance.ts` and then migrate one additional generated DTO leak from a TanStack Query hook or API module. This will turn the new pattern from a single successful slice into a repeatable frontend architecture convention.

## References

No external references were used for this evidence report. The findings are based on repository files, local validation output, and the committed Sprint 0 and Sprint 1 contract-alignment documentation.
