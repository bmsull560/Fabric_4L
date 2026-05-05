# Fabric_4L Type-Alignment Executable Work Plan

**Author:** Manus AI  
**Scope:** Frontend-backend type-alignment migration execution plan  
**Current execution point:** Sprint 0, stabilization and contract inventory

## A. Sprint Plan Review

The attached sprint roadmap is directionally sound and should remain the governing migration sequence. Its core architectural intent is preserved: FastAPI/Pydantic-generated OpenAPI remains the canonical API contract, generated TypeScript artifacts are permitted only at API and adapter boundaries, Zod performs runtime validation at network trust boundaries, DTOs are mapped into frontend-safe domain models, React components consume domain or view models only, and CI eventually blocks contract drift, stale generated clients, raw DTO leakage, and unsafe `any` usage.

The repository already contains several enabling assets, including committed OpenAPI artifacts under `contracts/openapi/`, generated TypeScript API artifacts under `apps/web/src/api/generated/`, a generator script at `apps/web/scripts/generate-api-types.ts`, a central Axios API client at `apps/web/src/api/client.ts`, existing Zod validation utilities in `apps/web/src/api/validation.ts`, and a custom Fabric contract ESLint plugin consumed by `apps/web/.eslintrc.js`. These assets make a progressive migration realistic, but they also mean Sprint 0 should emphasize inventory, governance, and non-invasive guardrails before any broad code refactor.

| Review Area | Finding | Execution Decision |
|---|---|---|
| Roadmap sequencing | The proposed Sprint 0 through Sprint 12 sequence is broadly correct because governance and inventory precede code generation, runtime validation, adapters, feature migrations, and blocking CI. | Keep the roadmap order and begin with Sprint 0. |
| OpenAPI export reality | The generator expects L1 through L6 plus `signals`, and committed artifacts exist for those surfaces. The export script discovery indicates special attention is needed before assuming every layer is exported deterministically by the same path. | Add a Sprint 0 discovery item and do not claim L1-L6 deterministic export until Sprint 1 validates it. |
| DTO leakage | Current generated imports appear concentrated in API and hook code rather than React page/component files. | Treat this as a favorable starting point, but inventory it explicitly and block future leakage later through lint policy. |
| Unsafe typing | Existing `no-explicit-any` is already configured as an ESLint error, but repository grep still finds unsafe casts, `JSON.parse`, `fetch`, and framework/test exceptions. | Sprint 0 should inventory and classify, not immediately rewrite all legacy code. |
| Runtime validation | Zod already exists in the dependency/toolchain and in selected API validation modules, but it is not yet a uniform trust-boundary pattern. | Defer shared validation foundation to Sprint 3 while documenting the intended boundary in Sprint 0 policy. |
| CI enforcement | Blocking CI before inventory and migration would create avoidable disruption. | Keep CI hard enforcement in Sprint 11; Sprint 0 only creates policy and backlog evidence. |

### Major Modifications Recommended

| Modification | Why It Matters | Impact on Sprint Order | Risk If Ignored | Recommended Adjustment |
|---|---|---|---|---|
| Add an explicit Sprint 0 repository-reality checkpoint for OpenAPI exporter coverage versus generated-client expectations. | The current repository has generated artifacts for L1-L6 and signals, while exporter behavior needs verification before deterministic export can be claimed. | No order change; it strengthens Sprint 0 and Sprint 1 entry criteria. | Sprint 1 could falsely claim deterministic export and later generate stale or partial clients. | Record exporter coverage as a contract inventory item and require Sprint 1 to reconcile exporter and generator surfaces. |
| Split Sprint 0 into a documentation/governance slice and a future enforcement slice. | The repository already contains legacy unsafe type patterns, so enforcement without inventory could fail unrelated code. | No order change; Sprint 0 remains first but avoids hard lint changes beyond existing rules. | A broad enforcement change could destabilize the frontend before migration begins. | Create inventory, policy, and backlog notes now; enforce boundaries after adapters and generated-client flow are stable. |
| Treat hooks as an intermediate boundary category rather than automatically equivalent to React components. | One generated import currently appears in hook code. Some hooks may be API boundary hooks, while others may be presentation-oriented hooks. | No order change; improves classification accuracy. | Misclassifying hooks could either allow DTO leakage or force unnecessary rewrites. | Add inventory categories for API hook, domain hook, and UI hook. |

### Major Modifications Rejected or Unnecessary

The plan does not require a stop-the-world rewrite, a replacement of the generated-client pipeline, or immediate migration of all L3-L6 screens. It also does not require introducing new dependencies during Sprint 0 because the repository already includes Zod, openapi-typescript generation, ESLint infrastructure, TanStack Query, and Axios. Broad backend DTO changes are intentionally deferred until the inventory and exporter baseline are stable.

### Final Execution Order

| Sprint | Theme | Stabilization Gate Before Advancing |
|---|---|---|
| Sprint 0 | Stabilization and inventory | Contract inventory, no-new-drift policy, discovered-risk backlog, and narrow validation complete. |
| Sprint 1 | OpenAPI source-of-truth baseline | Deterministic exporter coverage reconciled with committed OpenAPI artifacts and generator expectations. |
| Sprint 2 | Generated TypeScript client pipeline | Regeneration is reproducible and freshness can be checked without manual edits. |
| Sprint 3 | Runtime validation foundation | Shared Zod boundary and tests exist for selected high-risk primitives. |
| Sprint 4 | DTO-to-domain adapter architecture | Standard mapper/domain/view-model conventions and one reference adapter are stable. |
| Sprints 5-9 | L3-L6 and value modeling migrations | Each high-risk feature migrates through schema, mapper, tests, and UI boundary validation. |
| Sprint 10 | Legacy containment | Remaining endpoints are wrapped with retirement criteria. |
| Sprint 11 | CI/CD enforcement and launch gates | Advisory checks become blocking only after the repo can realistically pass. |
| Sprint 12 | Hardening and handoff | Runbooks, ADR templates, and debt review are complete. |

## B. Execution Start

The current sprint is **Sprint 0: Stabilization and Contract Inventory**. The sprint will avoid semantic API changes and will not manually edit generated artifacts. The first implementation slice will create or update governance and inventory documents using actual repository paths and audit evidence.

| Sprint 0 Work Item | Required Repository Change | Files Likely Touched | Validation Command |
|---|---|---|---|
| Contract inventory template and initial entries | Create the canonical inventory and seed it with discovered OpenAPI artifacts, generated clients, API consumers, and risk classifications. | `docs/contracts/contract-inventory.md` | Markdown inspection plus grep audit reconciliation. |
| No-new-drift policy | Create policy that freezes raw DTO leakage, new production `any`, unvalidated API consumption, duplicate handwritten response types, and snake_case UI domain leakage. | `docs/contracts/no-new-drift-policy.md` | Review against `.eslintrc.js` and current audit findings. |
| Sprint 0 backlog notes | Capture discovered violations, owners, and follow-up tickets without pretending they are fixed. | `docs/contracts/type-alignment-sprint-0-backlog.md` | Grep audits for generated imports, unsafe casts, JSON parsing, fetch, and Axios. |
| Stabilization report | Record changes, validations, residual risk, and next sprint recommendation. | `docs/contracts/type-alignment-sprint-0-stabilization-report.md` | `git status`, targeted frontend validation where available. |

### Files Inspected

| File or Path | Purpose in Sprint 0 |
|---|---|
| `apps/web/.eslintrc.js` | Confirms `@typescript-eslint/no-explicit-any` is already enforced and shows existing Fabric contract lint integration. |
| `apps/web/scripts/generate-api-types.ts` | Confirms generated DTO/client workflow expectations for layer-scoped OpenAPI artifacts. |
| `contracts/openapi/` | Confirms committed OpenAPI artifacts exist for L1-L6 and signals. |
| `apps/web/src/api/generated/` | Confirms generated TypeScript artifacts exist for L1-L6 and signals. |
| `scripts/export_openapi.py` | Identifies exporter behavior that Sprint 1 must reconcile with generator expectations. |
| `apps/web/src/api/client.ts` | Confirms current successful responses are not yet uniformly runtime-validated at the trust boundary. |
| `apps/web/src/api/validation.ts` | Confirms Zod validation exists in pockets and can be consolidated later. |

### Planned Sprint 0 Changes

Sprint 0 will produce narrow documentation and governance artifacts rather than broad refactors. This approach reduces drift immediately by making the contract boundary explicit while avoiding destabilizing legacy code that has not yet been migrated through Zod schemas and DTO-to-domain adapters.
