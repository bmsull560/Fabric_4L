# Type Alignment Sprint 1 OpenAPI Source-of-Truth Evidence

**Author:** Manus AI  
**Repository:** `bmsull560/Fabric_4L`  
**Sprint:** Sprint 1, OpenAPI source-of-truth reconciliation  
**Status:** Repository-owned export and frontend generated-type regeneration are now operational for Layer 1 through Layer 6, with the Signals contract intentionally retained as a static contract until a repository FastAPI source is identified.

## Executive summary

Sprint 1 reconciled the repository’s OpenAPI and generated TypeScript type source-of-truth path after Sprint 0 froze new frontend-backend drift. The previous export path was not a reliable source-of-truth mechanism because it referenced stale service paths, did not cover every active layer service, and imported service modules in a way that exposed package-initializer and runtime side effects during schema export. The updated exporter now targets the actual Layer 1 through Layer 6 service source tree, isolates each service export in a subprocess, uses synthetic package contexts for monolith-style service layouts, applies safe local export defaults, and preserves the existing static Signals OpenAPI file explicitly rather than pretending it has a discovered FastAPI source.

The regenerated OpenAPI contracts and frontend generated TypeScript DTO files show substantial drift from the previously committed contract artifacts. That drift is expected evidence that the repository’s generated artifacts were stale relative to the current service implementation. The Sprint 1 change set therefore includes both the corrected exporter and the regenerated artifacts so the committed contract files match the current repository-owned backend sources.

| Area | Sprint 1 result | Evidence |
|---|---:|---|
| Layer 1 OpenAPI export | PASS | `scripts/export_openapi.py` exported `contracts/openapi/layer1-ingestion.json` after correcting local list-style CORS configuration. |
| Layer 2 OpenAPI export | PASS | `contracts/openapi/layer2-extraction.json` regenerated from the current service source. |
| Layer 3 OpenAPI export | PASS | `contracts/openapi/layer3-knowledge.json` regenerated after isolating the import and pre-seeding the route import shim needed for schema export. |
| Layer 4 OpenAPI export | PASS | `contracts/openapi/layer4-agents.json` regenerated from the current service source after declared import dependencies were available in the validation environment. |
| Layer 5 OpenAPI export | PASS | `contracts/openapi/layer5-ground-truth.json` regenerated from the current service source. |
| Layer 6 OpenAPI export | PASS | `contracts/openapi/layer6-benchmarks.json` regenerated from the current service source. |
| Signals OpenAPI export | STATIC | `contracts/openapi/signals.json` was intentionally retained because no repository FastAPI source was identified during Sprint 1 discovery. |
| Frontend generated DTO types | PASS | `pnpm run generate:types` regenerated `apps/web/src/api/generated/l1-types.ts` through `l6-types.ts` and retained `signals-types.ts` generation from the static Signals contract. |

## Repository-owned changes made

The primary implementation change is `scripts/export_openapi.py`. The script now models service exports as explicit service specifications, runs each export in an isolated Python subprocess, and writes schemas atomically to `contracts/openapi`. This approach prevents one service’s import state, package aliases, or module globals from contaminating another service export. It also makes the script’s coverage clear: **Layer 1 through Layer 6 are live source exports**, while **Signals is static** until a FastAPI source is located.

The generated artifact changes are intentionally included. The frontend type-generation script consumes the repository OpenAPI files and writes TypeScript DTO definitions into `apps/web/src/api/generated`. After the OpenAPI contracts were regenerated from current backend source, the frontend DTO files changed accordingly. These changes should be reviewed as generated-source updates rather than hand-authored frontend behavior changes.

| File group | Change type | Rationale |
|---|---|---|
| `scripts/export_openapi.py` | Hand-authored exporter correction | Establishes deterministic OpenAPI export coverage for Layer 1 through Layer 6 and documents Signals as static. |
| `contracts/openapi/layer1-ingestion.json` through `layer6-benchmarks.json` | Generated contract update | Commits the backend-source-derived OpenAPI schemas produced by the corrected exporter. |
| `apps/web/src/api/generated/l1-types.ts` through `l6-types.ts` | Generated TypeScript DTO update | Aligns frontend generated DTOs with the regenerated OpenAPI contracts. |
| `docs/contracts/type-alignment-sprint-1-openapi-evidence.md` | Evidence documentation | Captures Sprint 1 validation, residual risks, and the next executable handoff. |

## Validation evidence

The corrected exporter completed with the following summary:

> `Exported 6/6 OpenAPI specifications`

The frontend generated-type command completed with the following generation summary:

> `✓ l1: l1-types.ts`  
> `✓ l2: l2-types.ts`  
> `✓ l3: l3-types.ts`  
> `✓ l4: l4-types.ts`  
> `✓ l5: l5-types.ts`  
> `✓ l6: l6-types.ts`  
> `✓ signals: signals-types.ts`

The command originally attempted as `generate:api` is not present in `apps/web/package.json`; the correct repository script is `generate:types`. Sprint 1 therefore used `pnpm run generate:types` as the authoritative frontend generated DTO refresh command.

| Validation command | Result | Notes |
|---|---:|---|
| `python3 scripts/export_openapi.py` | PASS | Regenerated Layer 1 through Layer 6 OpenAPI contracts. |
| `pnpm run generate:types` from `apps/web` | PASS | Regenerated frontend API DTO files from the OpenAPI contracts. |
| `git diff --name-status apps/web/src/api/generated contracts/openapi scripts/export_openapi.py` | PASS | Confirmed changes are limited to exporter, OpenAPI contracts, and generated frontend DTO artifacts before the Sprint 1 evidence document was added. |

## Residual risks and explicit non-goals

Sprint 1 did not claim that the frontend domain model has been fully migrated behind runtime validation and DTO-to-domain adapters. That work remains the responsibility of later migration sprints. Sprint 1’s scope is the **source-of-truth pipeline**: backend source to OpenAPI, OpenAPI to generated frontend DTOs, and evidence that the repository can refresh those artifacts deterministically.

The validation environment required installing declared Python import dependencies so FastAPI applications could be imported for schema export. This is acceptable for local validation evidence, but the repository should eventually encode the exporter dependency setup in a repeatable CI job or a dedicated development environment profile. The exporter also surfaces pre-existing warnings such as duplicate Layer 6 operation IDs and TypedDict field-shadowing warnings. Those warnings did not block export, but they should be triaged because generated-client quality improves when operation IDs and response model names are stable and unique.

| Residual item | Severity | Recommendation |
|---|---:|---|
| Signals remains static | P1 | Locate or create the Signals service FastAPI source export path, then convert `signals.json` from static retention to source-generated export. |
| Export dependencies are not yet encoded as a dedicated CI environment | P1 | Add a CI-safe dependency setup for `scripts/export_openapi.py` so schema freshness checks do not depend on ad hoc local installs. |
| Layer 6 duplicate operation ID warning | P2 | Assign stable unique operation IDs or route function names to avoid ambiguous generated client identifiers. |
| TypedDict field-shadowing warnings | P2 | Rename generated or helper result wrappers where feasible to reduce warning noise during export and type generation. |

## Next executable handoff

The next Sprint 1 hardening step should add a CI-facing freshness check that fails if `python3 scripts/export_openapi.py` followed by `pnpm run generate:types` produces a non-empty diff. Once that check is in place, Sprint 2 can begin migrating runtime transport boundaries behind Zod schemas and DTO-to-domain adapters without risking additional generated-contract drift.

The immediate recommended sequence is to validate the changed artifacts one more time, remove temporary logs, commit the Sprint 1 source-of-truth package, rebase if remote `main` has moved, and push to `origin/main`.
