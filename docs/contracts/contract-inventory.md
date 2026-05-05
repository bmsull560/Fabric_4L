# Fabric_4L Contract Inventory

**Author:** Manus AI  
**Sprint:** Sprint 0, stabilization and contract inventory  
**Status:** Seeded from repository discovery; owners and endpoint-level details must be refined by layer teams during Sprint 1 and feature migration sprints.

## Purpose

This inventory is the canonical working register for frontend-backend contract alignment. It records API contract artifacts, generated TypeScript DTO surfaces, frontend consumers, runtime validation coverage, mapper coverage, risk level, ownership, and migration status. The inventory is intentionally explicit about unknowns so that unresolved type-system drift is visible rather than hidden in handwritten frontend types or unvalidated API consumption.

## Allowed Migration Status Values

| Status | Meaning |
|---|---|
| `unknown` | The endpoint, consumer, or contract surface has not yet been inspected. |
| `inventoried` | The surface has been identified and recorded, but generated DTO, validation, or adapter coverage may still be incomplete. |
| `generated` | A generated TypeScript DTO/client artifact exists for the OpenAPI surface. |
| `validated` | Runtime validation exists for the response payload before feature logic consumes it. |
| `adapted` | DTO-to-domain mapping exists and React-facing code receives domain or view models only. |
| `migrated` | The endpoint or feature follows the full contract pattern: OpenAPI, generated DTO, Zod validation, mapper, tests, and UI boundary compliance. |
| `deprecated` | The endpoint or frontend consumer is still present but has an approved retirement path. |
| `removed` | The endpoint or frontend consumer has been retired. |

## Risk-Level Definitions

| Risk | Definition | Examples |
|---|---|---|
| P0 | A mismatch can create tenant, governance, financial, workflow, evidence, policy, or launch-readiness risk. | L3 graph topology, L4 agent/workflow events, L5 truth/evidence, L6 benchmark policy decisions, formulas, ROI, value-case outputs, tenant/account identity. |
| P1 | A mismatch can break important product workflows or user trust but does not directly govern high-risk decisions. | Account setup, integrations metadata, source configuration, pack framework display, usage and invoice status. |
| P2 | A mismatch is primarily display-only, administrative, or migration-cleanup debt. | Low-risk labels, static metadata, non-authoritative presentation fields. |

## Inventory Template

| Layer | Service | Endpoint Path | HTTP Method | Operation ID | Backend Request DTO | Backend Response DTO | OpenAPI Artifact | Generated TS Type | Frontend API Module | React Consumers | Runtime Validator | Mapper | Risk | Owner | Migration Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | `unknown` | Add one row per route or tightly coupled endpoint family. |

## Seeded Contract Artifact Inventory

The following entries are seeded from repository paths discovered during Sprint 0. They do not yet claim endpoint-level completion; they establish the baseline artifacts that Sprint 1 and Sprint 2 must reconcile.

| Layer | Service | Endpoint Path | HTTP Method | Operation ID | Backend Request DTO | Backend Response DTO | OpenAPI Artifact | Generated TS Type | Frontend API Module | React Consumers | Runtime Validator | Mapper | Risk | Owner | Migration Status | Notes |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| L1 | Ingestion | Multiple | Multiple | TBD | TBD | TBD | `contracts/openapi/layer1-ingestion.json` | `apps/web/src/api/generated/l1-types.ts` | TBD | TBD | TBD | TBD | P1 | Backend Platform / Frontend Platform | `generated` | Endpoint-level inventory remains required. |
| L2 | Extraction | Multiple | Multiple | TBD | TBD | TBD | `contracts/openapi/layer2-extraction.json` | `apps/web/src/api/generated/l2-types.ts` | TBD | TBD | TBD | TBD | P1 | Backend Platform / Frontend Platform | `generated` | Endpoint-level inventory remains required. |
| L3 | Knowledge / Graph | Multiple | Multiple | TBD | TBD | TBD | `contracts/openapi/layer3-knowledge.json` | `apps/web/src/api/generated/l3-types.ts` | `apps/web/src/api/packs.ts`; `apps/web/src/api/valuePackFramework.ts` | TBD | Partial existing validation in `apps/web/src/api/validation.ts` | Partial adapter patterns in API modules | P0 | L3 Team / Graph UI Team | `inventoried` | High-risk graph and value-pack surfaces must be prioritized. |
| L4 | Agents / Workflow | Multiple | Multiple | TBD | TBD | TBD | `contracts/openapi/layer4-agents.json` | `apps/web/src/api/generated/l4-types.ts` | TBD | TBD | Partial event parsing exists in workflow/stream code | TBD | P0 | L4 Agents Team / Agent UI Team | `inventoried` | Agent event streams, checkpoint, resume, and workflow results are high risk. |
| L5 | Ground Truth | Multiple | Multiple | TBD | TBD | TBD | `contracts/openapi/layer5-ground-truth.json` | `apps/web/src/api/generated/l5-types.ts` | `apps/web/src/hooks/useGroundTruthGovernance.ts` | TBD | TBD | TBD | P0 | L5 Team / Evidence UI Team | `inventoried` | Generated DTO import currently appears in hook code and must be classified as API hook, domain hook, or UI hook. |
| L6 | Benchmarks / Policy | Multiple | Multiple | TBD | TBD | TBD | `contracts/openapi/layer6-benchmarks.json` | `apps/web/src/api/generated/l6-types.ts` | TBD | TBD | TBD | TBD | P0 | L6 Team / Benchmark UI Team | `generated` | Benchmark policy, dataset, and entitlement metadata remain high-risk migration targets. |
| Cross-layer | Signals | Multiple | Multiple | TBD | TBD | TBD | `contracts/openapi/signals.json` | `apps/web/src/api/generated/signals-types.ts` | TBD | TBD | TBD | TBD | P1 | Intelligence Team / Frontend Platform | `generated` | Signals should be inventoried alongside L3/L10-style intelligence migration work. |

## Generated DTO Import Audit

Sprint 0 discovery found generated TypeScript imports only in API or hook-oriented code, not directly in React page or component files. This is a useful baseline, but it does not prove domain-boundary compliance because hooks may still leak transport shapes into UI consumers.

| File | Imported Generated Surface | Current Classification | Risk | Required Follow-Up |
|---|---|---|---|---|
| `apps/web/src/api/packs.ts` | `./generated/l3-types` | API module usage | P0 | Confirm DTOs are validated and mapped before UI consumption. |
| `apps/web/src/api/valuePackFramework.ts` | `./generated/l3-types` | API module usage | P0 | Confirm value-pack DTOs are adapted into stable domain models. |
| `apps/web/src/hooks/useGroundTruthGovernance.ts` | `@/api/generated/l5-types` | Hook usage requiring classification | P0 | Decide whether this hook is an API-boundary hook or a UI-facing hook; add mapper if UI-facing. |

## Unsafe Type and Unchecked Transport Audit Summary

Sprint 0 discovery found existing unsafe typing and unchecked transport patterns. These are recorded as legacy debt and must not be expanded by new work. Immediate broad rewrites are intentionally deferred until the corresponding schema and adapter foundations exist.

| Pattern | Count Found | Primary Locations | Sprint 0 Classification | Follow-Up Sprint |
|---|---:|---|---|---|
| `as any` | 24 | Primarily tests, mocks, and selected legacy frontend code | Existing debt; no new production usage allowed | Sprint 11 enforcement after migration |
| `: any` | 3 | Hook utility patterns and legacy exceptions | Existing debt requiring exception review | Sprint 0 backlog / Sprint 11 enforcement |
| `unknown as` | 10 | Tests, API validation, and mock boundaries | Requires case-by-case classification | Sprint 0 backlog |
| `JSON.parse` | 12 | SSE/event parsing, local storage parsing, OpenAPI validation helper, ontology editing | Requires runtime schema validation or safe parser wrappers | Sprint 3 and feature migrations |
| `fetch(` | 25 | Auth/session, stream clients, hook-level API calls | Requires trust-boundary classification | Sprint 3 and feature migrations |
| `axios` | 14 | Central API client and error-handling helpers | Allowed infrastructure usage; responses still need schema validation | Sprint 3 |

## Sprint 0 Inventory Acceptance Status

| Acceptance Item | Status | Evidence |
|---|---|---|
| Inventory template is committed. | COMPLETE | This document defines the canonical inventory columns and statuses. |
| Template is referenced from onboarding docs. | DEFERRED | No onboarding document was modified in the first Sprint 0 slice to keep changes narrow. |
| Risk-level definitions are included. | COMPLETE | P0, P1, and P2 classifications are defined above. |
| Generated DTO imports are cataloged. | COMPLETE | Three current generated import locations are listed. |
| Misuse instances have follow-up tickets. | PARTIAL | No direct page/component misuse was found; hook-level usage is captured in the backlog for classification. |
| Unsafe type usage inventory is complete enough to freeze drift. | PARTIAL | Pattern counts and representative files are captured; line-level remediation tickets are tracked in the Sprint 0 backlog. |
