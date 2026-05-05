# Type Alignment Sprint 3 Product Boundary Evidence

Author: **Manus AI**  
Date: 2026-05-05  
Repository: `bmsull560/Fabric_4L`

## Summary

Sprint 3 migrated the product TanStack Query boundary from cast-based transport trust to **domain-owned runtime validation**. The selected boundary was `apps/web/src/hooks/useProducts.ts`, which was previously identified as the highest-value next migration candidate because it concentrates product list, detail, analytics, matching, feature, and capability workflows behind one hook module.

The migration follows the Sprint 2 trust-boundary pattern: API transport responses are treated as **unknown data**, parsed through Zod schemas owned by the frontend domain layer, and then published to hook consumers as schema-inferred domain types. This prevents frontend consumers from depending directly on generated OpenAPI DTO aliases while still allowing regenerated OpenAPI output to remain the backend contract source of truth.

## Changed Files

| File | Purpose |
|---|---|
| `apps/web/src/lib/schemas/products.ts` | Adds product-domain Zod schemas, schema-inferred domain types, and parser functions for all migrated product transport responses. |
| `apps/web/src/hooks/useProducts.ts` | Refactors product query and mutation hooks to call product parser functions instead of asserting `response.data` to local or generated DTO types. |
| `docs/contracts/type-alignment-sprint-3-product-boundary-evidence.md` | Records implementation evidence, validation results, residual risks, and handoff recommendations. |

## Boundary Scope

The Sprint 3 slice covers the product hook module as the product-domain runtime boundary. It includes product collection retrieval, product detail retrieval, portfolio analytics, signal matching, product feature operations, and capability coverage operations.

| Boundary Area | Runtime Validation Outcome |
|---|---|
| Product list response | Parsed through domain-owned product list schema before being returned from the query function. |
| Product detail response | Parsed through domain-owned product schema before being returned from the query function. |
| Portfolio analytics response | Parsed through a domain-owned portfolio summary schema. |
| Product signal matches | Parsed as a domain-owned list response containing product signal match records. |
| Feature mutation responses | Parsed as domain-owned unknown-record responses because the backend shape is currently permissive. |
| Capability mutation responses | Parsed as domain-owned unknown-record responses because the backend shape is currently permissive. |

The implementation intentionally keeps request bodies typed by frontend-owned request interfaces in the hook module. Sprint 3 focused on the highest-risk trust direction: backend transport responses entering TanStack Query caches and hook consumers.

## Validation Evidence

Targeted validation was run after the product schema and hook refactor. The validation command checked for residual product response casts, generated DTO leakage in the migrated product boundary, frontend type safety, and contract freshness.

| Check | Result | Evidence |
|---|---:|---|
| Product cast leakage check | PASS | No `response.data as ...` product casts were found in `apps/web/src/hooks/useProducts.ts`. |
| Generated DTO leakage check | PASS | No `@/api/generated`, `operations[...]`, or `components[...]` references were found in `apps/web/src/hooks/useProducts.ts` or `apps/web/src/lib/schemas/products.ts`. |
| Frontend typecheck | PASS | `pnpm run check` completed successfully in `apps/web`. |
| Contract freshness gate | PASS | `scripts/ci/check_contract_freshness.sh` regenerated OpenAPI contracts and frontend DTO types without committed drift. |

> Sprint 3 validation concluded with: `Contract freshness gate passed: OpenAPI contracts and generated frontend DTO types are current.`

## Residual Risks and Follow-Up

The product domain schemas intentionally use `.passthrough()` on structured response records where the backend currently exposes additional fields or may evolve generated shapes. This keeps the migration compatible with the current OpenAPI contract while still validating required domain fields. Follow-up work should tighten the feature and capability mutation response schemas once backend response envelopes become more explicit.

| Follow-Up | Recommended Priority | Rationale |
|---|---:|---|
| Add parser unit tests for `products.ts` | P0 | Positive and negative fixtures should lock the runtime boundary behavior before the next product-domain expansion. |
| Tighten permissive feature and capability mutation schemas | P1 | Current schemas accept unknown record responses because the backend response shape is broad; tighter envelopes would improve drift detection. |
| Migrate `useCompetitiveIntel.ts` | P1 | It remains the next high-traffic L3 TanStack Query boundary with no equivalent runtime parser layer. |
| Migrate `useEvidence.ts` | P1 | Evidence workflows are high-impact and currently still rely on cast-based transport trust. |
| Add no-new-drift lint rules for generated DTO imports in hooks | P2 | The product and ground-truth migrations create concrete examples for enforcing hook-level generated DTO isolation. |

## Handoff Recommendation

The next sprint should add focused parser tests for `groundTruthGovernance.ts` and `products.ts`, then migrate `useCompetitiveIntel.ts` using the same **unknown transport → Zod parser → schema-inferred domain type** pattern. Once at least three high-traffic boundaries have been migrated, the repository can safely introduce a stricter lint rule preventing direct generated DTO imports in frontend hook modules.
