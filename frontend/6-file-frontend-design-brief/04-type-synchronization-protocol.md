# 4. Type Synchronization Protocol

## Purpose Statement

This document defines the protocol for maintaining type-level consistency between the Fabric 4L backend's 244 Zod-validated endpoints and the frontend TypeScript codebase. The current system suffers from undetected type drift: frontend types are manually defined, backend schemas evolve independently, and no automated mechanism flags mismatches before runtime failures occur. This protocol specifies a build-time generation pipeline, a version-locking strategy, clear boundaries between generated and manual types, and a phased migration path from the current ad-hoc definitions to a fully synchronized type system.

---

## 4.1 Current Type Drift Problem

### 4.1.1 244 Backend Endpoints with Zod Schemas, Frontend Types Manually Defined with Detected Drift

Track B's OpenAPI analysis reveals 244 backend endpoints with formally defined Zod schemas, of which only 8 are connected to frontend hooks through verified type contracts. The remaining 236 endpoints — 96.7% of the API surface — are orphaned: they have schema definitions on the backend but no corresponding frontend types, no consuming hooks, and no component surfaces. This gap is not merely an integration problem; it is a type-safety problem. When frontend engineers need to consume one of these orphaned endpoints, they write manual TypeScript interfaces by reading the OpenAPI spec, a process that introduces transcription errors, omits optional fields, and hardcodes versions of schemas that may have changed.

The 8 connected endpoints cluster in two domains: Layer 2 (Extraction) has 7 connected endpoints consumed by `useRunExtraction` and `useOntologySchema`; Layer 3 (Knowledge) has a single connected endpoint at `/v1/entities` consumed by `useEntities`. Every other domain — Layer 1 (Ingestion), Layer 4 (Agents), Layer 5 (Ground Truth), and the Signals layer — has zero connected endpoints. Even within the connected domains, the type link is fragile. The `useOntologySchema` hook does implement runtime validation via `OntologyTypeSchema.safeParse()`, which is the correct pattern, but this is the exception. Most hooks trust the shape of the response without any schema alignment check.

Track C classifies this condition as **Gap 2: Type Synchronization Contract**, marked CRITICAL. The gap has three symptoms: no automated backend-to-frontend type generation, manual types that drift from OpenAPI specs, and inline types instead of imported shared schemas. The drift is not theoretical. Hooks across the codebase define request parameters and response shapes locally, and when the backend changes a field name, a default value, or a cardinality constraint, those changes propagate silently into production.

### 4.1.2 Multiple `any` Types Detected in Hooks: useC1Stream, useComposition, useAuth, usePolling

Track A's hook analysis of 44 hooks found that 11 carry the `unknown` data-source classification, meaning they have no identifiable backend connection. Within this group, four hooks — `useC1Stream`, `useComposition`, `useAuth`, and `POLL_INTERVALS` from `usePolling.ts` — exhibit the exact pattern that type drift produces: they declare `has_types: true` in the audit metadata, but their type definitions contain `any` annotations or inline shapes with no verifiable link to a backend schema.

The `useC1Stream` hook, responsible for C1 agent stream handling, has no `api_endpoints` array and no query keys, yet claims typed responses. `useComposition` likewise has no backend endpoints and no error handling, suggesting its types are either purely local UI shapes or `any`-masked passthroughs. `useAuth` has no endpoints and no error handling, and `POLL_INTERVALS` from `usePolling.ts` is a configuration constant with no server contract at all. These four hooks represent the surface symptom of a deeper structural issue: when no automated type pipeline exists, engineers annotate types to satisfy the compiler without guaranteeing schema alignment. The `has_types: true` flag in the audit data becomes misleading — it indicates TypeScript compilation success, not contract compliance.

Beyond these four, 15 additional hooks across the green and yellow classifications also define inline request and response types. The problem is systemic, not localized.

### 4.1.3 No Automated Detection: Schema Changes on Backend Silently Break Frontend Assumptions

The most dangerous aspect of the current system is the absence of any automated drift detection. When a backend engineer modifies a Zod schema — renames a field, changes a string to an enum, adds a required property, or removes a deprecated field — that change travels through the following path: it is committed to the backend repository, it passes backend CI, it deploys to staging or production, and the frontend continues to compile against its manually defined types. TypeScript has no mechanism to know that `GET /v1/ontology/schema` now returns a schema version field that was not present when the frontend interface was written.

The first signal of this mismatch is typically a runtime error: an undefined property access, a failed destructuring, or a silently corrupted UI state. In a system with 244 endpoints and 44 hooks, the probability of undetected drift increases with every schema change. The frontend currently has no dependency on the backend OpenAPI spec at build time. There is no spec URL referenced in `package.json`, no generation script in the build pipeline, and no CI step that validates type compatibility between the committed frontend types and the current backend schema.

---

## 4.2 Auto-Generation Pipeline

### 4.2.1 Build-Time Generation: openapi-typescript from OpenAPI Spec

The target architecture introduces a single source of truth for all API-level types: the backend's OpenAPI specification, which is derived directly from Zod schemas. The generation tool is `openapi-typescript`, a mature, zero-runtime-dependency package that converts an OpenAPI 3.x document into a TypeScript declaration file with exact field names, optionality, enum values, and nested object structures preserved.

The generation command runs at build time, not at runtime. This is a deliberate decision. Runtime generation would add latency, network dependencies, and failure modes to the application startup sequence. Build-time generation produces a static `.d.ts` file that is committed to the repository (after CI validation) and imported by hooks at compile time. The TypeScript compiler treats generated types identically to hand-written ones — there is no runtime cost and no bundle size impact.

The OpenAPI spec is served by the backend at a well-known URL (e.g., `/openapi.json`) and is also published as a build artifact from the backend CI pipeline. The frontend build fetches this artifact during the pre-build phase. If the spec is unreachable, the build fails explicitly rather than proceeding with stale types.

### 4.2.2 Output Location: `src/generated/api-types.ts` — Never Manually Edited

All generated types are written to a single file: `src/generated/api-types.ts`. This path is governed by a strict contract: the file is **never manually edited**. A header comment at the top of the file marks it as auto-generated, and a lint rule prevents manual modifications.

```typescript
// ============================================================================
// AUTO-GENERATED FILE — DO NOT EDIT MANUALLY
// Generated from backend OpenAPI spec via openapi-typescript
// Source: <backend-openapi-url>
// Last generated: <timestamp>
// ============================================================================

export interface paths {
  "/v1/ontology/schema": {
    get: {
      responses: {
        200: {
          content: {
            "application/json": {
              types: OntologyType[];
              relationships: TypeRelationship[];
              version: string;
            };
          };
        };
      };
    };
  };
  // ... 244 endpoint definitions
}

export interface components {
  schemas: {
    OntologyType: {
      id: string;
      name: string;
      description?: string;
      properties: OntologyProperty[];
    };
    OntologyProperty: {
      id: string;
      name: string;
      type: "string" | "number" | "boolean" | "entity";
      required: boolean;
    };
    // ... all Zod schemas
  };
}
```

The generated file exports two primary namespaces: `paths`, containing route-level request and response types organized by HTTP method and status code; and `components`, containing reusable schema definitions that correspond to backend Zod models. Hooks import from these namespaces rather than defining local interfaces. For example, `useOntologySchema` would import `components["schemas"]["OntologyType"]` instead of maintaining its own `OntologyType` interface.

This structure provides complete type coverage for all 244 endpoints, including the 236 that are currently orphaned. When a frontend engineer begins integrating an orphan endpoint, the types are already available for import — no transcription step, no drift.

### 4.2.3 CI Integration: Type Generation Runs as Pre-Build Step, Failures Block Deployment

The generation pipeline is integrated into the frontend CI as a mandatory pre-build step. The sequence is:

1. **Fetch Spec**: CI downloads the OpenAPI JSON from the backend artifact store using the pinned version tag (see Section 4.3).
2. **Generate Types**: `openapi-typescript` converts the spec to `src/generated/api-types.ts`.
3. **Diff Check**: CI compares the newly generated file against the committed version. If they differ, the build fails with a descriptive error indicating which schemas changed.
4. **Build**: Only if the diff check passes (or the updated types have been explicitly committed) does the build proceed.
5. **Type Check**: `tsc --noEmit` runs across the full codebase to ensure the generated types compile correctly with all hook and component code.

This gating mechanism prevents deployments with unsynchronized types. The diff check is particularly important for detecting breaking changes: if a backend schema rename causes a generated type to change, every hook that imports that type will fail type checking, and the CI failure will surface the exact location and nature of the mismatch.

---

## 4.3 Version Locking Strategy

### 4.3.1 Backend API Version Tags Pinned in Frontend package.json

Type synchronization requires version alignment between the frontend type definitions and the backend schema source. The frontend `package.json` contains a `backendApiVersion` field that pins the exact backend version whose OpenAPI spec is used for generation.

```json
{
  "name": "fabric-4l-frontend",
  "version": "4.2.1",
  "backendApiVersion": "v2.14.3",
  "scripts": {
    "generate:types": "openapi-typescript https://api.backend.dev/openapi.json?version=v2.14.3 --output src/generated/api-types.ts",
    "typecheck": "tsc --noEmit",
    "build": "npm run generate:types && npm run typecheck && vite build"
  }
}
```

The `backendApiVersion` is not a semver range — it is an exact tag. This eliminates ambiguity: every engineer on the team, and every CI run, generates types from the same backend schema version. When the backend team releases a new API version, the frontend team updates this field deliberately, after reviewing the changelog and planning any necessary hook updates.

### 4.3.2 Breaking Change Detection: CI Compares Generated Types Against Committed Version

The CI diff check mentioned in Section 4.2.3 serves as the breaking change detector. When the committed `api-types.ts` differs from the freshly generated version, the CI pipeline emits a failure report that includes:

- The backend version that produced the mismatch
- A structural diff of the generated file
- A list of frontend hooks that import the affected types

This gives engineers a precise map of the impact before any code is deployed. If the backend change is a non-breaking addition (e.g., a new optional field), the engineer regenerates types, commits the updated file, and the build passes. If the change is breaking (e.g., a renamed required field), the engineer must update the consuming hooks before the build can succeed.

The following matrix summarizes the four possible type-change scenarios and the required frontend action:

| Change Category | Example | Backend Semver | Frontend Action | CI Behavior |
|---|---|---|---|---|
| Non-breaking addition | New optional field on response | Minor bump | Regenerate types, commit | Passes after regeneration |
| Non-breaking expansion | New enum value added | Minor bump | Regenerate types, commit | Passes after regeneration |
| Breaking rename | Required field renamed | Major bump | Update hook code + regenerate | Fails until hooks updated |
| Breaking removal | Deprecated field removed | Major bump | Update hook code + regenerate | Fails until hooks updated |

This matrix governs the contract between backend and frontend release processes. Backend teams communicate the change category through semver, and the CI pipeline enures that frontend code aligns with the declared category before deployment proceeds.

### 4.3.3 Gradual Migration Path: Critical Domains First, Full Coverage Target

Full type synchronization across all 244 endpoints cannot happen atomically without halting feature development. The protocol specifies a phased migration that starts with the domains where type drift causes the most production risk and expands systematically to full coverage.

The priority domains are determined by two factors: the number of connected hooks (indicating active frontend usage) and the business criticality of the domain. Track B's orphan registry and Track A's hook classification provide the data for this prioritization.

| Priority | Domain | Connected Hooks | Orphan Endpoints | Migration Phase |
|---|---|---|---|---|
| 1 | Accounts | `useAccounts`, `useTenants`, `useIntegrations` | 16 | Phase 1 — Critical |
| 2 | Ontology | `useOntologySchema` | 14 | Phase 1 — Critical |
| 3 | Workflows | `useActiveWorkflows`, `useCanonicalCaseId` | 9 | Phase 1 — Critical |
| 4 | Formulas | `useFormulas`, `useFormulaVersions` | 5 | Phase 2 — Standard |
| 5 | Entities | `useEntities`, `useGraphQuery` | 1 connected, 88 layer orphans | Phase 2 — Standard |
| 6 | ValuePacks | `useValuePacks`, `useValueTree` | 9 | Phase 2 — Standard |
| 7 | Ingestion | `useIngestionJobs`, `useSources` | 26 | Phase 3 — Full |
| 8 | Ground Truth | `useBenchmarks` | 13 | Phase 3 — Full |
| 9 | Agents / C1 | `useC1Stream` | 84 | Phase 3 — Full |
| 10 | System / Health | `useSystemHealth` | 15 | Phase 3 — Full |

This ordering reflects the audit findings directly. The Accounts domain has 16 orphan endpoints but three active hooks — any schema change in this domain affects live CRM integration. Ontology has 14 orphans but one highly connected hook (`useOntologySchema`) that already implements runtime validation, making it a natural early adopter. Workflows has 9 orphans and touches agent execution, a core value proposition. Phase 1 covers these three domains with generated types before expanding to the remaining seven domains in Phases 2 and 3.

---

## 4.4 Manual Type Boundaries

### 4.4.1 When to Keep Manual Types: UI-Specific Shapes, Form State, View Models

Auto-generated types cover the API layer — the exact shapes that cross the HTTP boundary between backend and frontend. However, not every type in a frontend application maps 1:1 to an API response. Three categories of types should remain manually defined:

**UI-specific shapes** include component props, layout structures, and theme-driven variants that have no backend counterpart. A `SidebarItem` interface with `icon`, `label`, `route`, and `isCollapsed` properties is purely a frontend concern. Generating this from the backend OpenAPI spec would be impossible and nonsensical.

**Form state types** often diverge from API shapes for usability reasons. A multi-step wizard may accumulate partial state across steps before submitting a single consolidated payload. The intermediate step states are frontend-only types that should remain manually defined, with explicit transformation functions that map the final form state to a generated API request type.

**View models** are derived representations of API data tailored for specific UI surfaces. An account list view may need `displayName` (computed from `firstName` + `lastName`), `statusColor` (mapped from `status`), and `lastActivityRelative` (a formatted string derived from `lastActivityAt`). These computed fields belong in a manual view model type that composes a generated API base type with UI-specific extensions.

### 4.4.2 Hybrid Approach: Generated Types for API Layer, Manual Types for Presentation Layer

The protocol mandates a clear architectural boundary between generated and manual types. Generated types from `src/generated/api-types.ts` are used exclusively at the API client boundary: request payloads in `POST` and `PUT` bodies, response data from `GET` endpoints, and query parameter shapes. Manual types live in domain-specific files (e.g., `src/types/accounts.ts`, `src/types/workflows.ts`) and extend or compose generated types for presentation-layer concerns.

This hybrid approach prevents two common anti-patterns. The first is "type leakage," where generated API types are used directly as component props, coupling UI components to the API schema and forcing UI changes when the API changes. The second is "shadow drift," where manual types duplicate generated types with slightly different field names, recreating the drift problem within the manual layer. The boundary rule is: if the type describes something that crosses the network, it is generated; if it describes something that stays inside the browser, it is manual.

### 4.4.3 Type Guard Functions for Runtime Validation at the Protocol Hook Layer

Generated types provide compile-time safety but disappear at runtime. TypeScript's type erasure means that a hook receiving a `200 OK` response with an unexpected shape will not throw a type error — it will proceed with invalid data until something downstream breaks. To close this gap, the protocol requires runtime type guards at the protocol hook layer.

The `useOntologySchema` hook already implements this pattern correctly using `OntologyTypeSchema.safeParse()`. The protocol generalizes this approach: every hook that consumes a generated response type must validate the runtime shape against a Zod schema that is derived from, and kept in sync with, the backend source schema. The Zod schemas for runtime validation are published by the backend as a separate package (`@fabric4l/api-schemas`) that the frontend installs via npm. This package is version-locked alongside the OpenAPI spec.

```typescript
import { z } from "zod";
import { OntologyTypeSchema, OntologyPropertySchema } from "@fabric4l/api-schemas";
import type { components } from "../generated/api-types";

// Generated type for compile-time safety
type OntologyType = components["schemas"]["OntologyType"];

/**
 * Runtime-validated fetch for ontology types.
 * Compile-time: uses generated OntologyType from api-types.ts
 * Runtime: validates with Zod schema from @fabric4l/api-schemas
 */
async function fetchOntologyType(typeId: string): Promise<OntologyType> {
  const response = await apiClient.get(`/v1/ontology/schema/types/${typeId}`);

  const result = OntologyTypeSchema.safeParse(response.data);
  if (!result.success) {
    logError("Schema mismatch on fetchOntologyType", {
      typeId,
      issues: result.error.issues,
      received: response.data,
    });
    throw new SchemaMismatchError("OntologyType", result.error);
  }

  return result.data; // Typed as OntologyType at compile time, validated at runtime
}
```

This dual-layer validation — generated TypeScript types for the compiler, Zod schemas for the runtime — is the core of the Type Synchronization Protocol. It eliminates both the false confidence of unchecked `has_types: true` annotations and the brittleness of purely manual type definitions. The `SchemaMismatchError` thrown on validation failure includes the expected schema name and the Zod issue path, making production debugging precise and fast.

---

## 4.5 Implementation Steps

### 4.5.1 Phase 1: Set Up Generation Tool and CI Pipeline for OpenAPI to TypeScript

Phase 1 establishes the infrastructure for type generation and CI enforcement. This phase does not modify any hook code — it creates the pipeline that will validate all subsequent migration work.

The first task is to install `openapi-typescript` as a dev dependency and add the generation script to `package.json`. The backend team must ensure that the OpenAPI spec is accessible at a stable URL or published as a versioned artifact. The frontend team adds the `backendApiVersion` pin and the `"generate:types"` script.

The second task is to create the `src/generated/` directory and establish the "never manually edited" rule via an ESLint configuration that flags modifications to `api-types.ts` with a custom rule or a `.gitattributes` entry combined with a pre-commit hook.

The third task is the CI integration. The frontend CI pipeline is modified to run the generation script, perform the diff check, and gate the build on type compatibility. A baseline `api-types.ts` is generated from the current pinned backend version and committed to the repository. This becomes the reference against which all future changes are compared.

### 4.5.2 Phase 2: Replace Manual API Types in Green Hooks First (Reference Implementation)

Phase 2 begins the actual migration of hook code from manual types to generated types. The migration starts with green hooks — the 26 hooks that have live backend integration, verified API endpoints, and active usage in production components. These hooks are the safest starting point because their backend contracts are real and testable.

The first three hooks to migrate are the ones that serve as reference implementations for the rest of the codebase:

1. **`useOntologySchema`** — Already has runtime validation via `safeParse()`. Migration replaces its local `OntologyType`, `OntologyProperty`, and `TypeRelationship` interfaces with imports from `components["schemas"]`. This hook demonstrates the pattern: generated types for compile-time safety, existing Zod validation for runtime safety.

2. **`useAccounts`** — Has `has_types: true` and calls `GET l4` / `POST l4` endpoints. Migration replaces its manual account request and response types with generated equivalents from the Accounts schema group.

3. **`useActiveWorkflows`** — Has `has_types: true`, error handling, and calls `GET l4` / `POST l4` / `DELETE l4`. Migration validates that generated workflow types cover all three HTTP methods.

After these three reference implementations are merged and stable, the remaining 23 green hooks are migrated in priority order (Accounts, Ontology, Workflows, Formulas, Entities, ValuePacks). Each migration follows a standard procedure: replace manual interfaces with generated imports, run the test suite, verify that `tsc --noEmit` passes, and confirm runtime validation still works. The CI pipeline ensures that no hook can be merged with drifted types.

### 4.5.3 Phase 3: Full Migration — All Hooks Use Generated Types, Manual Types Only for UI Layer

Phase 3 completes the migration by extending generated type usage to yellow and red hooks, then enforcing the boundary rule across the entire codebase. Yellow hooks (5 hooks including `useFormulaDependents`, `useFormulaVersions`, and `usageKeys`) have generic endpoint passthroughs or partial type coverage; their migration may require backend schema improvements to achieve full type safety. Red hooks (2 hooks: `useOpportunities` and `useSources`) are mock-based with no live backend; their migration is deferred until they are reconnected to real endpoints, but the protocol requires that when reconnection occurs, generated types are used from day one.

The final enforcement mechanism is a CI lint rule that prohibits inline interface definitions for API request or response shapes anywhere in the `src/hooks/` directory. If a hook needs a type that describes an API payload, it must import from `src/generated/api-types.ts` or from a manual type file that explicitly extends a generated base. This rule, combined with the generation pipeline and version locking, closes Gap 2 permanently and establishes the Type Synchronization Contract as a ratified, automated, enforced standard.

---

## Summary of Protocol Contracts

| Contract | Enforcement Mechanism | Owner |
|---|---|---|
| Generated types are never manually edited | ESLint rule + pre-commit hook | Frontend |
| `backendApiVersion` is an exact pin, not a range | `package.json` schema validation | Frontend |
| CI fails on generated type diff | CI pipeline gate | DevOps |
| API-layer types are always generated | Lint rule in `src/hooks/` | Frontend |
| Runtime validation uses version-locked Zod schemas | `@fabric4l/api-schemas` package | Backend |
| Manual types are UI-layer only | Code review + lint guidance | Frontend |

These six contracts, taken together, transform type synchronization from an undocumented, error-prone manual process into a reliable, automated pipeline. The 244 backend endpoints gain guaranteed frontend type coverage. The 44 hooks gain compile-time and runtime validation. And schema changes on either side of the boundary are detected at build time, before they reach production.
