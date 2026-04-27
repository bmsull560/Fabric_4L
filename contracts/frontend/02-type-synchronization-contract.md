# Contract B: Type Synchronization Contract

**Status:** Ratified  
**Version:** 1.0.0  
**Date:** 2026-04-26  
**Scope:** All TypeScript type definitions consumed by frontend hooks  
**Enforcement:** CI gate `type_sync_check` (see Section 6)

---

## 1. Purpose

This contract mandates automated OpenAPI-to-TypeScript generation and eliminates manual type maintenance. The frontend audit found 244 backend endpoints with formal Pydantic schemas and zero automated type generation — all frontend types are manually maintained, with multiple hooks using `any` or unverified casts.

After this contract is enforced, no frontend type that represents a backend API shape may be manually authored. All such types MUST be generated from the backend OpenAPI specifications.

---

## 2. Type Categories

### 2.1 Generated Types (Backend-Owned)

These types represent backend API request and response shapes. They are generated from OpenAPI specs and MUST NOT be manually edited.

| Category | Source | Location | Example |
|----------|--------|----------|---------|
| API Response types | OpenAPI `components/schemas` | `src/api/generated/{layer}-types.ts` | `Account`, `Product`, `Hypothesis` |
| API Request types | OpenAPI `requestBody` schemas | `src/api/generated/{layer}-types.ts` | `CreateProductRequest`, `EnrichmentParams` |
| Enum types | OpenAPI `enum` definitions | `src/api/generated/{layer}-types.ts` | `HypothesisStatus`, `NarrativeTone` |
| Error types | OpenAPI error response schemas | `src/api/generated/errors.ts` | `ValidationError`, `NotFoundError` |

### 2.2 Manual Types (Frontend-Owned)

These types are UI-specific and have no backend counterpart. They MAY be manually authored and maintained.

| Category | Location | Example |
|----------|----------|---------|
| UI state types | `src/types/ui.ts` | `TabState`, `ModalConfig`, `FilterPanelState` |
| View model types | `src/types/views.ts` | `DashboardViewModel`, `AccountCardProps` |
| Form state types | `src/types/forms.ts` | `AccountFormValues`, `FormulaEditorState` |
| Component prop types | Co-located with component | `AccountListProps`, `HypothesisCardProps` |

---

## 3. Generation Pipeline

### 3.1 Source of Truth

The OpenAPI specifications in `contracts/openapi/` are the source of truth for all generated types. These files are produced by `make contracts` from the live FastAPI applications.

| Layer | OpenAPI Spec | Generated Output |
|-------|-------------|-----------------|
| Layer 1 (Ingestion) | `contracts/openapi/layer1-ingestion.json` | `src/api/generated/l1-types.ts` |
| Layer 2 (Extraction) | `contracts/openapi/layer2-extraction.json` | `src/api/generated/l2-types.ts` |
| Layer 3 (Knowledge) | `contracts/openapi/layer3-knowledge.json` | `src/api/generated/l3-types.ts` |
| Layer 4 (Agents) | `contracts/openapi/layer4-agents.json` | `src/api/generated/l4-types.ts` |
| Layer 5 (Ground Truth) | `contracts/openapi/layer5-ground-truth.json` | `src/api/generated/l5-types.ts` |
| Signals | `contracts/openapi/signals.json` | `src/api/generated/signals-types.ts` |

### 3.2 Generation Tool

The pipeline uses `openapi-typescript` to generate TypeScript types from OpenAPI 3.x specifications:

```bash
# Generate all layer types (canonical command)
pnpm run generate:types

# Backward-compatible alias (deprecated)
pnpm run generate:api-types

# Generate a single layer
npx openapi-typescript contracts/openapi/layer3-knowledge.json \
  -o frontend/client/src/api/generated/l3-types.ts
```

### 3.3 Generation Rules

1. Generated files include a `// @generated` header comment — do not edit
2. Generated files are committed to the repository (not `.gitignore`d)
3. Generation runs as a pre-build step in CI
4. The `backendApiVersion` field in `package.json` pins the backend schema version

---

## 4. Migration Strategy

### 4.1 Phase 1 (Sprint 1-3): Critical Domains

Generate types for the domains with the highest orphan endpoint counts:

| Domain | Endpoints | Priority |
|--------|-----------|----------|
| Accounts | 16 | P0 |
| Products (DIL) | 10 | P0 |
| Evidence (DIL) | 9 | P0 |
| Competitive Intel (DIL) | 10 | P0 |
| Enrichment (DIL) | 4 | P0 |
| Value Hypotheses (DIL) | 7 | P0 |
| Narratives (DIL) | 5 | P0 |
| ROI Calculator (DIL) | 7 | P0 |
| Intelligence (DIL) | 3 | P0 |

### 4.2 Phase 2 (Sprint 4-8): Remaining Domains

Generate types for Ontology, Workflows, Formulas, ValuePacks, Governance, Settings.

### 4.3 Phase 3 (Sprint 9-12): Full Coverage

Generate types for Tools, Analysis, CRM Webhooks, OIDC SSO, and any remaining domains.

---

## 5. Breaking Change Protocol

When a backend schema change breaks the generated types:

| Semver Category | Example | Frontend Action |
|----------------|---------|-----------------|
| Patch (field added) | New optional field on Account | Regenerate types, no hook changes |
| Minor (endpoint added) | New `/accounts/search` endpoint | Regenerate types, create new hook |
| Major (field removed/renamed) | `account.domain` renamed to `account.website_domain` | Regenerate types, update all consuming hooks, update tests |

Major changes require a **Contract Amendment RFC** reviewed by both a frontend architect and a backend engineer before merge.

---

## 6. CI Enforcement

The `type_sync_check` CI gate runs on every PR:

1. Regenerate all types from the committed OpenAPI specs (`pnpm run generate:types`)
2. Diff the output against committed generated files (`git diff --exit-code frontend/client/src/api/generated/`)
3. **Fail the build** if any mismatch is detected, with per-file drift details mapping changed OpenAPI spec paths to generated outputs
4. Run `pnpm tsc --noEmit` to verify type compatibility

---

## 7. Changelog

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-04-26 | Initial ratification |
