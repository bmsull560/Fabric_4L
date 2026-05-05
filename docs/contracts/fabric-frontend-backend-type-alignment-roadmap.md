# Fabric_4L Frontend–Backend Type-Alignment Architecture Roadmap

**Author:** Manus AI  
**Date:** 2026-05-05  
**Scope:** React/Vite/TypeScript frontend, TanStack Query data access, FastAPI/Pydantic layered services L1–L6, generated OpenAPI types, runtime validation, contract testing, and progressive migration.

---

## Executive Summary

Fabric_4L should resolve the current frontend–backend type-system mismatch by making **FastAPI/Pydantic-generated OpenAPI the canonical API contract source**, generating TypeScript DTO clients from each layer’s OpenAPI document, validating every network-bound payload at runtime with **Zod**, and mapping DTOs into **UI-safe domain models** through thin, tested adapters. This is the most pragmatic strategy because the repository already contains FastAPI services, OpenAPI-generated TypeScript files under `apps/web/src/api/generated`, Zod-based validation in frontend API and contract tests, and contract governance packages under `packages/platform-contract` and `packages/eslint-plugin-fabric-contracts`.

The central architectural rule is simple: **backend DTOs may cross the network boundary, but raw API DTOs must not cross the frontend feature boundary into React components**. UI components should consume domain models and view models only. This preserves product semantics for value modeling, evidence, formulas, agent workflows, tenant governance, and benchmark policy decisions while keeping the transport layer truthful to the backend contract.

> **Recommended decision:** Fabric_4L should not adopt tRPC or gRPC as the primary contract mechanism for the existing product. It should use **layer-scoped OpenAPI 3.1 emitted from FastAPI/Pydantic v2**, feed that into generated TypeScript clients, derive or author runtime Zod schemas at the trust boundary, and enforce drift detection in CI before launch gates can pass.

This roadmap intentionally avoids a stop-the-world refactor. It starts with high-risk L3–L6 workflows, wraps legacy endpoints behind adapters, and migrates one domain slice at a time. The first production gate should be **no new raw DTO leakage, no new `any`, no unvalidated network response, no undocumented endpoint shape, and no PASS claim for live-only gates without environment evidence**.

| Decision Area | Fabric_4L Recommendation | Reason |
|---|---|---|
| Canonical API source | **FastAPI/Pydantic-generated OpenAPI per layer** | Aligns with current backend stack and existing OpenAPI generation assets. |
| Frontend transport types | **Generated DTO types only in API modules and adapters** | Avoids manual drift while keeping backend implementation details out of UI. |
| Runtime guards | **Zod at network and domain boundaries** | Existing repo already uses Zod in API clients, hooks, and contract tests. |
| Transformation pattern | **DTO → domain mapper → optional view model** | Removes scattered endpoint-specific mapping from components. |
| CI enforcement | **OpenAPI diff, generated-code freshness, Vitest/pytest contract tests, lint rules, mock validation** | Detects drift before merge and before launch. |
| Migration strategy | **Progressive, risk-ranked migration across L3–L6 first** | Stabilizes graph, agent/workflow, ground-truth, and benchmark-policy surfaces without pausing feature work. |

---

## Recommended Contract Strategy

OpenAPI is the correct primary contract mechanism for Fabric_4L because it is language-agnostic, HTTP-native, and directly supported by FastAPI. The OpenAPI Specification defines a standard interface description for HTTP APIs, allowing both humans and tools to understand service capabilities without source-code access, and OpenAPI descriptions can be used for documentation, code generation, testing, and automation tooling.[^1] FastAPI’s own documentation states that FastAPI APIs can be described in OpenAPI and used to generate TypeScript SDKs that stay in sync with backend code.[^2]

Fabric_4L should therefore define the contract source as **the exported OpenAPI document produced from explicit Pydantic request and response models for each layer service**. Backend database models, SQLAlchemy entities, Neo4j graph records, LangGraph internal state, Redis cache payloads, and Kubernetes deployment configuration must not be treated as API contracts. They are implementation details. The API contract is the explicit DTO boundary exposed by each service.

| Candidate | Fit for Fabric_4L | Recommendation |
|---|---|---|
| OpenAPI-first handwritten YAML | Strong for governance, weaker for current developer flow. | Use only for externally published APIs or critical shared schemas that need design review before implementation. |
| **FastAPI/Pydantic-generated OpenAPI** | **Best fit** because services already use FastAPI and Pydantic-style DTOs. | **Primary source of truth.** Require explicit `response_model` and stable operation IDs. |
| tRPC | Excellent for monolithic TypeScript stacks, poor fit for Python FastAPI microservices. | Do not adopt as primary; it would introduce a parallel contract model. |
| Protocol Buffers / gRPC | Strong for service-to-service binary RPC, but heavy for browser-first HTTP UX. | Reserve for future high-throughput internal services, not frontend contracts. |
| JSON Schema | Good schema substrate, weak as full API contract by itself. | Use as a derived artifact for validation and schema-specific governance. |
| Hybrid OpenAPI + Zod generation | Strong at runtime edge, but should not replace API source of truth. | Adopt as implementation pattern: OpenAPI DTO generation plus Zod guards. |

The canonical contract should be **layer-scoped rather than monolithic**. Fabric_4L’s L1–L6 architecture has different stability profiles and domain semantics, so each layer should publish a versioned OpenAPI artifact, while shared concepts should be defined as reusable schema components. Tenant identity, provenance, evidence confidence, money, decimal quantity, formula references, benchmark policy references, graph node identity, and workflow correlation metadata should be modeled as shared primitives or small shared components, not by forcing all layers into one giant schema.

| Layer | Contract Artifact | Shared Component Pressure | Versioning Rule |
|---|---|---|---|
| L1 Ingestion | `l1.openapi.json` | Job identity, source metadata, compliance log reference. | Minor version for additive response fields; major for pagination or status enum changes. |
| L2 Extraction | `l2.openapi.json` | Extraction job identity, provenance, entity candidates. | Major for status-machine changes; minor for new evidence fields. |
| L3 Knowledge / Graph | `l3.openapi.json` | Graph node, graph edge, formula, value tree, entity identity. | Highest scrutiny; graph node/edge shape changes require contract review. |
| L4 Agents / Workflows | `l4.openapi.json` plus event schema | Agent event, workflow checkpoint, workflow result, business-case output. | Event-envelope changes require major version or dual-read adapter. |
| L5 Ground Truth | `l5.openapi.json` | Truth object, validation event, freshness, evidence provenance. | Major for maturity/status semantics; minor for additional audit metadata. |
| L6 Benchmarks / Policies | `l6.openapi.json` | Benchmark dataset, policy, entitlement, policy decision metadata. | Major for policy evaluation semantics; minor for new policy fields. |

Contract drift should be detected through three independent signals. First, CI should export each layer’s OpenAPI file from the running service module and compare it against the committed artifact. Second, CI should regenerate TypeScript DTO clients and fail when generated files are stale. Third, contract tests should validate representative fixtures, MSW mocks, and backend responses against the same schema expectations. This gives Fabric_4L compile-time checking, runtime checking, and mock-data checking without relying on any one layer alone.

---

## DTO vs Domain Model Architecture

Fabric_4L should explicitly separate **persistence models**, **backend DTOs**, **generated frontend DTOs**, **frontend domain models**, and **UI view models**. The current mismatch exists because UI state models and backend service-specific response shapes have been allowed to meet directly. The fix is not to make backend responses look like React state. The fix is to make the seam explicit and narrow.

| Model Category | Owner | Naming | Allowed Location | Not Allowed |
|---|---|---|---|---|
| Persistence model | Backend service | `SqlAlchemyModel`, Neo4j record, repository entity | Service data layer only. | Never exported as API response by accident. |
| Backend API DTO | Backend service | `EvidenceItemDto`, `FormulaEvaluationResponse`, `GraphSubgraphResponse` | FastAPI route boundary and OpenAPI. | Should not contain ORM-specific lazy fields. |
| Generated frontend DTO | Frontend API layer | `components["schemas"]["EvidenceItemDto"]` or `EvidenceItemDto` | `src/api/generated`, `src/api/*`, feature adapters. | No direct import in React components. |
| Frontend domain model | Frontend feature domain | `EvidenceItem`, `FormulaEvaluation`, `BenchmarkPolicy` | `src/features/<domain>/domain` or `src/types/domain`. | Must not preserve backend-only casing or nullable clutter. |
| UI view model | React presentation | `EvidenceCardViewModel`, `GraphNodeViewModel` | Component boundary and selectors. | Must not call API clients or parse raw DTO. |
| Agent/workflow payload | L4 contract boundary | `AgentStreamEventDto`, `WorkflowCheckpointDto` | Stream client and workflow adapters. | Must not be treated as arbitrary JSON. |

The naming convention should make misuse obvious. Backend transport types should carry a `Dto`, `Request`, `Response`, or `EventDto` suffix. Frontend domain models should use product terms without transport suffixes. View models should use `ViewModel`. Adapters should be named `map<Dto>To<Domain>`, `parse<Domain>Dto`, or `to<Domain>ViewModel`, and should live next to the feature API module rather than inside components.

The standard import rule should be: **React components may import domain models and view models, but may not import from `src/api/generated`**. The repository already has an ESLint contract plugin; it should grow or configure a rule that blocks `apps/web/src/components/**`, `apps/web/src/pages/**`, and `apps/web/src/features/**/components/**` from importing generated DTOs directly. The only allowed exceptions should be `src/api/**`, `src/features/**/api/**`, and `src/features/**/adapters/**`.

| Transformation Concern | Standard Fabric_4L Pattern |
|---|---|
| snake_case to camelCase | Convert once in the adapter. Domain models are camelCase unless a field is a domain-standard external identifier. |
| ISO datetime strings | Keep DTO fields as strings. Domain fields should use branded `IsoDateTimeString` or explicit `Date` only when UI logic needs date arithmetic. Avoid silent `new Date()` in components. |
| Python `Decimal` and financial values | Transport as strings or structured money objects. Domain model should use `MoneyAmount = { amountMinor?: bigint; decimal: string; currency: CurrencyCode }` or a decimal-string branded type. Do not use floating-point for authoritative money. |
| Nullable vs optional | DTO mirrors backend `null`; domain uses `undefined` for absent optional UI data and reserves `null` for meaningful explicit absence. |
| Tenant-scoped IDs | Use branded identifiers such as `TenantId`, `AccountId`, `TruthId`, and composite domain keys such as `TenantScopedId<T>`. Do not pass raw tenant IDs through component props unless needed for display. |
| Provenance and evidence confidence | Normalize into a shared `Provenance` and `ConfidenceScore` domain primitive. Reject out-of-range confidence values. |
| Graph DTO vs visualization model | `GraphSubgraphResponseDto` maps to `GraphSubgraph`; visualization layout maps separately to `GraphNodeViewModel` and `GraphEdgeViewModel`. |
| Formula DTO vs calculator UI | Formula request/response DTO maps to `FormulaEvaluation`; calculator input state remains a separate view model. |
| Agent events vs stream UI | `AgentStreamEventDto` validates discriminated event envelopes; UI receives typed `AgentTimelineEvent` objects. |

Traceability should be preserved by carrying non-visual metadata through the domain model. A business-case output should retain `sourceResponseId`, `workflowInstanceId`, `traceId`, `tenantId`, `provenance`, `formulaVersion`, and `benchmarkPolicyId` as hidden but typed fields. This supports auditability without forcing components to know backend implementation details.

---

## Runtime Validation Strategy

Compile-time TypeScript types are necessary but insufficient because API responses are runtime data. Fabric_4L should validate all network responses at the trust boundary and selectively revalidate high-risk domain transformations. Zod is the right default because the current frontend already uses it, it is TypeScript-first, supports static inference, validates untrusted data, and its documentation recommends strict TypeScript mode.[^3] Valibot is a reasonable future optimization for bundle-sensitive screens, while io-ts should not be introduced because it would add a second functional-validation paradigm without clear repository benefit.

| Tool | Fabric_4L Use | Recommendation |
|---|---|---|
| **Zod** | Network response parsing, mock validation, event schemas, formula and policy guards. | **Primary runtime validation library.** |
| Valibot | Potential lightweight validation in bundle-constrained areas. | Do not adopt now; evaluate after Zod standardization. |
| io-ts | Runtime codecs with functional style. | Do not adopt; avoid additional paradigm and dependency complexity. |

Validation should run in three places. The network client should validate universal envelopes, errors, tenant context, and request identifiers. Feature API functions or TanStack Query hooks should validate endpoint-specific DTO payloads before mapping. Domain adapters should assert invariants that are not expressible in OpenAPI, such as cross-field formula requirements, graph edge references to existing nodes, or benchmark policy threshold consistency.

| Surface | Validation Mode | Failure Behavior |
|---|---|---|
| Tenant, identity, authorization-sensitive fields | Strict Zod parse plus branded ID checks. | Fail closed; show secure error state and log trace ID. |
| Formula evaluation and money fields | Strict parse; reject malformed decimal, currency, formula version, and confidence. | Fail closed; do not render ROI, value case, or calculation output. |
| Agent stream events | Discriminated union parse for every event. | Invalid event becomes an error event; malformed checkpoint/resume events fail closed. |
| Graph query responses | Parse nodes, edges, confidence, and references. | Degrade layout if optional visualization metadata fails; fail if graph identity is malformed. |
| Benchmark-policy responses | Strict parse of policy type, threshold, applicability, and decision metadata. | Fail closed because policy mistakes affect governed outputs. |
| Non-critical display metadata | Lenient optional parsing. | Degraded rendering with placeholder and validation telemetry. |
| Mock data and fixtures | Same schemas as runtime. | CI failure; mocks must not lie about contracts. |

Validation failures must be observable. Every validation error should include the layer, endpoint operation ID, request ID or trace ID, tenant context if safe, schema name, and a redacted issue summary. The frontend should not log raw sensitive payloads. For degraded rendering, the UI should explicitly distinguish **data unavailable**, **contract invalid**, and **permission denied** states, because those conditions require different operator responses.

Silent `any` fallbacks should be prohibited. TypeScript should run with strict mode, `noImplicitAny`, `noUncheckedIndexedAccess` where feasible, ESLint `no-explicit-any` for production code, and a narrow exception policy for test harnesses. Where unknown data is required, use `unknown` followed by a schema parse. The architectural slogan should be: **unknown at the boundary, parsed DTO after validation, domain model after mapping, view model inside components**.

---

## Migration Roadmap

The migration should be progressive and risk-ranked. Fabric_4L should not halt feature work while every endpoint is redesigned. Instead, every touched feature must move in the new direction, while the highest-risk contracts are stabilized first. The risk ranking should prioritize surfaces that affect tenant isolation, money, formulas, value-case generation, agent workflow resumability, evidence provenance, and benchmark policy decisions.

| Phase | Objective | Exit Criteria |
|---|---|---|
| Phase 0: Freeze new drift | Stop the bleeding before refactor begins. | No new `any`, no generated DTO imports in components, no new unvalidated API calls. |
| Phase 1: Inventory and ownership | Build a contract inventory across L1–L6. | Every endpoint has owner, OpenAPI operation ID, DTO schema, frontend consumer, and risk level. |
| Phase 2: Generated-client baseline | Regenerate per-layer clients and commit stable artifacts. | Generated files are reproducible; CI fails on stale generation. |
| Phase 3: High-risk adapter migration | Migrate L3 graph, L4 workflows, L5 ground truth, and L6 benchmark policies first. | UI consumes domain models only for critical workflows. |
| Phase 4: Legacy wrapper containment | Wrap legacy endpoints behind adapters without changing UI screens all at once. | Legacy response variants normalized in one place per domain. |
| Phase 5: Screen-by-screen migration | Convert account setup, intelligence signals, evidence, value trees, formulas, ROI, generated value case, and validation screens. | Each migrated screen has Zod parsing, mapper tests, and no raw DTO leakage. |
| Phase 6: Launch enforcement | Turn advisory checks into required launch gates. | Contract drift, stale clients, invalid mocks, and raw DTO imports block release. |

The first audit should search for direct imports from `src/api/generated`, `as any`, `: any`, handwritten `fetch` or `axios` calls outside approved API clients, snake_case fields inside components, and mappers embedded in React render logic. The repository already shows generated type files for L1–L6 and Zod-heavy contract tests; those should be treated as a foundation rather than replaced wholesale.

| Critical Workflow | First Migration Target | Reason |
|---|---|---|
| Account/prospect setup | Tenant-scoped account DTOs and domain IDs. | Prevents tenant leakage and incorrect account context. |
| Intelligence signals | Signal confidence and provenance. | Drives downstream value-case recommendations. |
| Evidence matching | `EvidenceItem` DTO/domain separation. | Evidence provenance must remain auditable. |
| Value-driver tree | Graph node/edge DTO validation. | L3 graph drift breaks value modeling UX. |
| Formula evaluation | Decimal, formula version, and confidence parsing. | Direct financial and governance risk. |
| ROI calculator | Money/value domain primitives. | Avoids floating-point and nullable-output errors. |
| Generated value case | Workflow result adapter. | Business-case output currently depends on composed workflow payloads. |
| Ground-truth validation | Truth object and validation event schemas. | L5 governs correctness and auditability. |
| Benchmark policy application | Policy DTO and decision metadata. | L6 policy drift can change product recommendations. |
| Agent stream and resume | Discriminated event schemas and checkpoint DTOs. | L4 resumability requires stable event semantics. |

---

## Code Example: Shared Contract Flow

The following example uses **EvidenceItem** because evidence sits at the intersection of L2 extraction, L3 graph context, L5 ground truth, and L4 value-case generation. The example shows the intended flow from backend DTO to generated type, runtime validation, mapper, TanStack Query hook, and React component. It is intentionally realistic rather than exhaustive.

### Backend Pydantic DTO

```python
from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

class ProvenanceDto(BaseModel):
    source_url: str | None = None
    extraction_job_id: str | None = None
    truth_id: UUID | None = None
    workflow_instance_id: str | None = None

class EvidenceItemDto(BaseModel):
    model_config = ConfigDict(json_schema_extra={"x-fabric-layer": "L5"})

    evidence_id: UUID
    tenant_id: UUID
    account_id: UUID
    claim: str = Field(min_length=5, max_length=2000)
    evidence_type: Literal["case_study", "benchmark", "customer_quote", "calculation", "source_document"]
    confidence_score: Decimal = Field(ge=Decimal("0"), le=Decimal("1"))
    provenance: ProvenanceDto
    created_at: datetime
    updated_at: datetime | None = None

class EvidenceListResponse(BaseModel):
    items: list[EvidenceItemDto]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    has_more: bool
```

### OpenAPI-Generated Frontend DTO Type

```ts
// apps/web/src/api/generated/l5-types.ts
// Generated from L5 FastAPI OpenAPI. Do not edit manually.
export type EvidenceItemDto = components["schemas"]["EvidenceItemDto"];
export type EvidenceListResponse = components["schemas"]["EvidenceListResponse"];
```

### Runtime Validator

```ts
// apps/web/src/features/evidence/api/evidence.schemas.ts
import { z } from "zod";

const uuid = z.string().uuid();
const isoDateTime = z.string().datetime();
const decimalRatioString = z.union([z.string(), z.number()]).transform((value, ctx) => {
  const text = String(value);
  const numeric = Number(text);
  if (!Number.isFinite(numeric) || numeric < 0 || numeric > 1) {
    ctx.addIssue({ code: z.ZodIssueCode.custom, message: "confidence_score must be between 0 and 1" });
    return z.NEVER;
  }
  return text;
});

export const EvidenceItemDtoSchema = z.object({
  evidence_id: uuid,
  tenant_id: uuid,
  account_id: uuid,
  claim: z.string().min(5).max(2000),
  evidence_type: z.enum(["case_study", "benchmark", "customer_quote", "calculation", "source_document"]),
  confidence_score: decimalRatioString,
  provenance: z.object({
    source_url: z.string().url().nullable().optional(),
    extraction_job_id: z.string().nullable().optional(),
    truth_id: uuid.nullable().optional(),
    workflow_instance_id: z.string().nullable().optional(),
  }),
  created_at: isoDateTime,
  updated_at: isoDateTime.nullable().optional(),
});

export const EvidenceListResponseSchema = z.object({
  items: z.array(EvidenceItemDtoSchema),
  total: z.number().int().nonnegative(),
  page: z.number().int().positive(),
  page_size: z.number().int().positive().max(100),
  has_more: z.boolean(),
});
```

### DTO-to-Domain Mapper

```ts
// apps/web/src/features/evidence/domain/evidence.mapper.ts
import type { z } from "zod";
import type { EvidenceItemDtoSchema } from "../api/evidence.schemas";

type EvidenceItemDto = z.infer<typeof EvidenceItemDtoSchema>;

export type EvidenceType = "caseStudy" | "benchmark" | "customerQuote" | "calculation" | "sourceDocument";

export interface EvidenceItem {
  id: string;
  tenantId: string;
  accountId: string;
  claim: string;
  type: EvidenceType;
  confidence: { decimal: string; percent: number };
  provenance: {
    sourceUrl?: string;
    extractionJobId?: string;
    truthId?: string;
    workflowInstanceId?: string;
  };
  createdAt: string;
  updatedAt?: string;
}

const evidenceTypeMap: Record<EvidenceItemDto["evidence_type"], EvidenceType> = {
  case_study: "caseStudy",
  benchmark: "benchmark",
  customer_quote: "customerQuote",
  calculation: "calculation",
  source_document: "sourceDocument",
};

export function mapEvidenceItemDtoToDomain(dto: EvidenceItemDto): EvidenceItem {
  const confidenceNumber = Number(dto.confidence_score);

  return {
    id: dto.evidence_id,
    tenantId: dto.tenant_id,
    accountId: dto.account_id,
    claim: dto.claim,
    type: evidenceTypeMap[dto.evidence_type],
    confidence: {
      decimal: dto.confidence_score,
      percent: Math.round(confidenceNumber * 100),
    },
    provenance: {
      sourceUrl: dto.provenance.source_url ?? undefined,
      extractionJobId: dto.provenance.extraction_job_id ?? undefined,
      truthId: dto.provenance.truth_id ?? undefined,
      workflowInstanceId: dto.provenance.workflow_instance_id ?? undefined,
    },
    createdAt: dto.created_at,
    updatedAt: dto.updated_at ?? undefined,
  };
}
```

### TanStack Query Hook

```ts
// apps/web/src/features/evidence/api/useEvidenceItems.ts
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { EvidenceListResponseSchema } from "./evidence.schemas";
import { mapEvidenceItemDtoToDomain } from "../domain/evidence.mapper";

export function useEvidenceItems(accountId: string) {
  return useQuery({
    queryKey: ["evidence", "items", accountId],
    enabled: Boolean(accountId),
    queryFn: async () => {
      const response = await apiClient.get("l5", `/evidence?account_id=${encodeURIComponent(accountId)}`);
      const parsed = EvidenceListResponseSchema.parse(response.data);
      return {
        items: parsed.items.map(mapEvidenceItemDtoToDomain),
        total: parsed.total,
        hasMore: parsed.has_more,
      };
    },
  });
}
```

### UI-Safe React Consumption

```tsx
// apps/web/src/features/evidence/components/EvidenceList.tsx
import { useEvidenceItems } from "../api/useEvidenceItems";

export function EvidenceList({ accountId }: { accountId: string }) {
  const { data, isLoading, error } = useEvidenceItems(accountId);

  if (isLoading) return <p>Loading evidence…</p>;
  if (error) return <p>Evidence is unavailable because the response contract could not be validated.</p>;

  return (
    <section>
      {data?.items.map((item) => (
        <article key={item.id}>
          <strong>{item.type}</strong>
          <p>{item.claim}</p>
          <span>{item.confidence.percent}% confidence</span>
        </article>
      ))}
    </section>
  );
}
```

The important feature is not the specific field set. The important feature is that generated DTOs and snake_case fields stop at the API/adapter boundary, while React receives product-oriented domain data with explicit invariants.

---

## Recommended Toolchain

Fabric_4L should choose a small standard toolchain and avoid parallel generators per feature. Multiple generators create inconsistent client semantics, mismatched nullability, and uneven runtime validation.

| Tool | Role | Fabric_4L Recommendation |
|---|---|---|
| Orval | Generates TypeScript clients and React Query hooks from OpenAPI. | Good candidate if Fabric_4L wants generated hooks; use only after operation IDs and schemas are stable. |
| **HeyAPI** | Generates TypeScript SDKs from OpenAPI, with strong TS ecosystem focus. | **Recommended first generator candidate** for DTO/client generation because FastAPI documents it directly for TS SDK generation.[^2] |
| openapi-typescript | Generates TypeScript types from OpenAPI. | Keep or use when Fabric_4L wants type-only output with custom hand-authored client wrappers. |
| openapi-zod-client | Generates Zod-backed clients from OpenAPI. | Evaluate for endpoint subsets; do not depend on it until OpenAPI 3.1 compatibility and output ergonomics are proven. |
| **Zod** | Runtime validation and type inference. | **Primary runtime guard.** Standardize all feature validators on it. |
| Valibot | Lightweight schema validation. | Defer; possible future optimization. |
| **Pydantic v2** | Backend DTO definition and validation. | **Primary backend model layer for API DTOs.** Require explicit request/response models. |
| **FastAPI OpenAPI export** | Produces layer OpenAPI artifacts. | **Canonical contract export path.** Must be deterministic and committed. |
| MSW | Frontend API mocking. | Required for UI tests, but mocks must validate against the same schemas. |
| Schemathesis | Property-based API testing from OpenAPI. | Add for L3–L6 high-risk endpoints after OpenAPI baseline stabilizes. |
| Dredd or Prism | Contract testing / mock server from OpenAPI. | Use Prism for local mock-server workflows if needed; Dredd only if it fits service lifecycle. |
| pytest / Vitest contract tests | Backend and frontend contract enforcement. | Keep and expand; tests should share fixtures and schema expectations. |

---

## CI/CD Enforcement Plan

The CI plan should make contract drift visible before merge and make launch gates stricter than ordinary development gates. For ordinary pull requests, CI should block new drift. For final testing and launch, CI should require evidence that every live-only gate either passed in the correct environment or is explicitly marked `REQUIRES_ENVIRONMENT`.

| Gate | Check | Failure Condition |
|---|---|---|
| OpenAPI export freshness | Start or import each FastAPI layer and export `l<n>.openapi.json`. | Export differs from committed contract without an intentional version bump. |
| Generated client freshness | Regenerate TypeScript DTO/client files. | Git diff appears under `apps/web/src/api/generated`. |
| Runtime schema tests | Run Vitest contract tests against DTO schemas, mocks, and adapters. | Invalid mock data, unhandled nullability, or mapper invariant failure. |
| Backend contract tests | Run pytest route and DTO tests. | Route returns undocumented field semantics or missing response model. |
| No raw DTO leakage | ESLint rule blocks generated imports in components/pages. | Component imports from generated API package or uses DTO suffix. |
| No `any` leakage | TypeScript and ESLint block explicit `any` outside approved test shims. | Production code introduces `any`, unsafe assertion, or unchecked JSON parse. |
| API operation governance | Operation IDs are stable, tagged, and layer-scoped. | Missing operation ID, duplicate operation ID, or untagged endpoint. |
| Tenant guard | Contract tests assert tenant fields and authorization-sensitive responses. | Tenant-scoped endpoint omits or mis-shapes tenant context. |
| Launch readiness | Final gate validates contract, generated client, mock, adapter, and environment evidence. | Live-only evidence missing or repo-owned contract checks fail. |

This plan should be implemented in stages. Initially, some rules can run in advisory mode and produce a report. After the high-risk L3–L6 migration begins, advisory checks should become required for changed files. Before launch, the checks should become repository-wide required gates.

---

## Risks and Tradeoffs

The recommended approach deliberately accepts a thin adapter layer rather than trying to eliminate all mapping. This is the right tradeoff for Fabric_4L because the backend should expose stable service contracts, while the frontend should expose product semantics. For example, a graph response optimized for Neo4j traversal is not the same as a graph visualization model, and an L4 workflow result is not the same as a generated value-case UI model.

| Risk | Impact | Mitigation |
|---|---|---|
| Generated clients expose awkward backend names | Developers may import DTOs directly into UI. | Enforce import boundaries and provide domain adapters. |
| OpenAPI reflects current mistakes | Bad schemas become formally generated. | Add schema review for high-risk layers and use versioned migration adapters. |
| Zod schemas duplicate OpenAPI schemas | Maintenance overhead. | Generate where reliable; manually author only high-risk guards and invariants. |
| Adapter layer becomes too thick | Business logic may move into frontend. | Keep mapping structural; move business composition to BFF/gateway where appropriate. |
| Strict validation breaks screens on imperfect data | Short-term UX degradation. | Use strict failure for governed fields and degraded rendering for optional display metadata. |
| Multiple layers evolve independently | Shared concepts drift. | Define shared primitives and review version changes through contract ownership. |
| Legacy endpoints delay migration | Old variants remain. | Wrap legacy endpoints behind one adapter per domain and measure remaining legacy surface. |

The largest tradeoff is that FastAPI/Pydantic-generated OpenAPI makes backend implementation discipline non-negotiable. Every route must declare response models, operation IDs must be stable, and service teams must treat OpenAPI diffs as product-impacting changes rather than incidental generated output. That discipline is exactly what Fabric_4L needs before launch.

---

## Final Recommended Architecture

The final architecture is a **contract-first, generated-client, runtime-guarded, adapter-contained frontend/backend boundary**. Each FastAPI layer publishes a deterministic OpenAPI contract generated from explicit Pydantic DTOs. The frontend generates TypeScript transport types and clients from those contracts. API functions validate responses at runtime with Zod, then map validated DTOs into frontend domain models. React components consume only domain models or view models. CI rejects contract drift, stale generated clients, invalid mocks, raw DTO leakage, `any` leakage, and unsafe tenant or money payloads.

```text
FastAPI route + Pydantic DTO
        ↓
Layer OpenAPI artifact: l1–l6.openapi.json
        ↓
Generated TypeScript DTO/client
        ↓
Zod runtime validator at network/feature boundary
        ↓
Thin DTO → domain adapter
        ↓
TanStack Query cache stores UI-safe domain data
        ↓
React components consume domain/view models only
```

The architecture should preserve Fabric_4L’s layered design rather than collapsing it into one universal schema. L1–L6 should each own their contracts, while shared domain primitives should be small, explicit, and versioned. The immediate implementation priority should be L3 graph responses, L4 agent/workflow events, L5 ground-truth validation, L6 benchmark policies, and formula/value-case money fields. Those surfaces carry the highest risk of runtime failure, tenant-governance failure, and incorrect value-model output.

| Final Rule | Meaning |
|---|---|
| **Contract-first discipline** | Every API change starts with an intentional DTO and OpenAPI diff. |
| **Generated clients** | No handwritten endpoint typing when OpenAPI can generate it. |
| **Strict runtime guards** | Compile-time types do not replace runtime validation. |
| **Thin adapters** | Mapping is centralized, structural, tested, and traceable. |
| **No raw DTOs in UI** | Components consume domain/view models only. |
| **No `any`** | Unknown data must be parsed, not asserted. |
| **No scattered manual mapping** | Endpoint-specific mapping lives in feature adapters, not components. |
| **CI drift detection** | OpenAPI, generated clients, fixtures, and mocks must stay synchronized. |
| **Progressive migration** | Legacy endpoints are wrapped and retired domain by domain. |
| **Production gates before ship** | Live-only gates require environment evidence; repo-owned checks must pass. |

---

## References

[^1]: [OpenAPI Specification 3.1.1 — Swagger](https://swagger.io/specification/)
[^2]: [Generating SDKs — FastAPI](https://fastapi.tiangolo.com/advanced/generate-clients/)
[^3]: [Intro — Zod](https://zod.dev/)
