# Fabric_4L No-New-Drift Policy

**Author:** Manus AI  
**Sprint:** Sprint 0, stabilization and contract inventory  
**Policy Status:** Effective for new code immediately; legacy exceptions must be inventoried and migrated progressively.

## Policy Statement

Fabric_4L treats frontend-backend type alignment as a product safety, governance, and launch-readiness concern. New work must not increase drift between backend FastAPI/Pydantic contracts and frontend domain models. Generated DTOs may exist at API and adapter boundaries, but they must not become component contracts. Runtime payloads must be validated before entering feature logic, and DTOs must be mapped into frontend-safe domain or view models before React components render them.

> **No new drift means new code may not introduce raw DTO leakage, unvalidated API response consumption, unauthorized production `any`, duplicate handwritten response types, or backend-shaped `snake_case` fields in UI domain models.**

## Immediate Rules for New Code

| Rule | Required Behavior | Disallowed Behavior | Current Enforcement |
|---|---|---|---|
| Generated DTO boundary | Generated types from `apps/web/src/api/generated/**` may be used in API modules, adapter modules, mapper tests, and explicit migration shims. | React pages, generic components, feature components, and view models must not import generated DTOs directly. | Policy now; lint enforcement targeted for Sprint 11. |
| Runtime response validation | API responses that cross into feature logic must be parsed with a schema or an approved validation helper. | Treating network JSON as trusted domain data is not allowed for new high-risk work. | Policy now; shared helper targeted for Sprint 3. |
| DTO-to-domain mapping | Backend field names, nullability, enums, and transport envelopes must be normalized through mappers. | React components must not perform ad hoc DTO normalization. | Policy now; adapter architecture targeted for Sprint 4. |
| No new production `any` | New production frontend code must use precise types, `unknown` at boundaries, or approved generics. | `: any`, `as any`, and blanket `unknown as` casts are not allowed unless explicitly documented as a temporary migration exception. | `@typescript-eslint/no-explicit-any` is already configured as an error; cast-specific enforcement is future work. |
| No duplicate handwritten response types | New response shapes should come from OpenAPI-generated DTOs or be explicitly documented as temporary migration shims. | Handwritten types that duplicate backend response contracts without traceability are not allowed. | Policy now; inventory review required. |
| No backend-shaped UI domain leakage | Frontend domain and view-model fields should be camelCase and presentation-safe. | New UI-facing models must not expose raw `snake_case` backend fields unless they are explicitly transport DTOs. | Policy now; lint or grep checks targeted for later enforcement. |

## Approved Import Boundary Map

| Location | Generated DTO Imports | Rationale |
|---|---|---|
| `apps/web/src/api/**` | Allowed | API modules are a transport boundary and may name generated DTOs while validating and adapting responses. |
| `apps/web/src/features/**/api/**` | Allowed | Feature API modules may use generated DTOs as transport contracts. |
| `apps/web/src/features/**/adapters/**` | Allowed | Adapters are responsible for translating DTOs into domain models. |
| `apps/web/src/features/**/domain/**/*.mapper.ts` | Allowed | Mapper files may import DTOs to produce domain models. |
| `apps/web/src/**/*.mapper.test.ts` and contract tests | Allowed with care | Tests may assert mapping and validation behavior at the contract boundary. |
| `apps/web/src/components/**` | Disallowed | Components must consume domain or view models. |
| `apps/web/src/pages/**` | Disallowed | Pages must not bind directly to transport contracts. |
| `apps/web/src/features/**/components/**` | Disallowed | Feature components must not import backend DTOs. |
| `apps/web/src/features/**/screens/**` | Disallowed | Screens must consume domain or view models. |
| General hooks outside API folders | Review required | Hooks can be API-boundary hooks or UI-facing hooks; each generated DTO import in hooks must be classified. |

## High-Risk Surfaces

The following surfaces must be treated as P0 for type alignment because invalid transport assumptions can affect tenant safety, governed decisions, financial outputs, workflow correctness, or evidence traceability.

| Surface | Required Treatment |
|---|---|
| Tenant and account identity | Validate IDs and preserve scope through DTO, domain, and telemetry paths. |
| L3 graph topology | Validate nodes, edges, references, confidence, provenance, and topology consistency before visualization. |
| L4 agent and workflow events | Use typed event envelopes and discriminated unions; malformed checkpoint or resume events must fail closed. |
| L5 truth and evidence | Preserve evidence provenance, status semantics, confidence, freshness, and audit metadata. |
| L6 benchmark policy decisions | Validate policy type, thresholds, dataset references, entitlements, effective dates, and decision metadata. |
| Formula, ROI, money, and value cases | Use decimal strings or structured money primitives for authoritative values; malformed financial payloads must not render as valid. |

## Temporary Exception Process

A temporary exception is allowed only when the migration cannot be completed in the current change without excessive risk. The exception must be narrow, documented near the code, added to the contract inventory or backlog, owned by a team, and linked to a target sprint or removal condition. Exceptions must not be used to normalize new design choices that bypass the contract boundary.

| Exception Field | Required Content |
|---|---|
| Owner | Team or named engineering owner responsible for removal. |
| Reason | Why the exception is necessary and why a mapper/schema is not being added immediately. |
| Scope | File, function, endpoint, or test harness where the exception applies. |
| Risk | P0, P1, or P2 classification. |
| Removal Condition | Sprint, ticket, or technical condition that allows the exception to be removed. |

## Pull Request Checklist Addition

Every PR that touches frontend API consumption, backend DTOs, route handlers, OpenAPI artifacts, generated clients, high-risk feature screens, or mocks should answer the following before review.

| Question | Required Answer |
|---|---|
| Does this change alter a backend request or response contract? | If yes, identify the OpenAPI artifact and generated TypeScript impact. |
| Are generated DTOs imported only in approved boundary locations? | If no, explain the temporary exception and removal condition. |
| Is the API response validated before feature logic consumes it? | If no, explain whether this is legacy code or an approved staged migration. |
| Does React consume domain/view models rather than raw DTOs? | If no, add an adapter task before merge or document a time-boxed exception. |
| Does the change introduce `any`, `as any`, or broad `unknown as` casts? | If yes, document the owner, risk, and removal condition. |
| Does the change touch tenant, money, benchmark policy, evidence, workflow, or graph data? | If yes, classify as P0 and require explicit validation/mapper review. |

## Relationship to Existing Tooling

The frontend ESLint configuration already treats `@typescript-eslint/no-explicit-any` as an error and consumes the Fabric contracts plugin. This policy extends the governance surface by defining generated DTO import boundaries and runtime validation expectations that will become progressively enforceable after the inventory, generated-client pipeline, validation foundation, and adapter architecture are stable.
