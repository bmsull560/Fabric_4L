# Type Alignment Sprint 6 Stream Boundary Evidence

Author: **Manus AI**
Date: 2026-05-05
Repository: `bmsull560/Fabric_4L`

## Summary

Sprint 6 completed the next open type-alignment item by migrating high-risk **stream JSON trust boundaries** behind runtime validation. The sprint targeted AGUI agent events, extraction job SSE messages, and Layer 4 workflow SSE messages because these paths parse long-lived stream payloads that can be malformed, partial, or schema-incompatible at runtime.

The implementation adds `apps/web/src/agui/eventSchemas.ts` as the AGUI event schema module and updates stream consumers so parsed JSON must pass Zod validation before it reaches hook state or event handlers. Job-stream and workflow stream helpers now return `null` for malformed JSON or structurally invalid payloads, preserving existing runtime resilience while replacing unvalidated parsing and casting with explicit parser functions.

## Changed Files

| File | Purpose |
|---|---|
| `apps/web/src/agui/eventSchemas.ts` | Adds AGUI event discriminated-union schemas, `parseAgentEvent`, `parseAgentEventJson`, and a centralized `parseJsonValue` helper used by stream boundaries. |
| `apps/web/src/agui/eventSchemas.test.ts` | Adds positive and negative parser coverage for AGUI events, extraction job SSE events, and workflow SSE payload envelopes. |
| `apps/web/src/agui/AgentEventClient.ts` | Refactors AGUI stream parsing to validate each SSE payload through `parseAgentEventJson` before dispatching it to listeners. |
| `apps/web/src/hooks/useJobStream.ts` | Refactors extraction job stream parsing so malformed JSON and invalid event shapes are rejected by `parseJobStreamEventJson`. |
| `apps/web/src/hooks/useWorkflows.ts` | Refactors workflow SSE parsing through `parseWorkflowSseMessageJson` and adds runtime parsers for workflow detail and workflow-type response boundaries encountered during the stream cleanup. |

## Boundary Scope

Sprint 6 covers stream-oriented trust boundaries rather than a single REST hook domain. This intentionally prioritizes JSON parsing locations that were identified as high risk in the Sprint 6–9 inventory.

| Boundary Area | Runtime Validation Outcome |
|---|---|
| AGUI agent event stream | Every parsed AGUI event must match a known `AgentEventType` discriminant and the required fields for that event variant. |
| Extraction job SSE stream | Job stream messages must include a known stream event type and a payload envelope before hook state is updated. |
| Workflow SSE stream | Workflow SSE payloads must be JSON objects with a validated payload envelope before normalization into frontend workflow state. |
| Workflow detail response | Workflow detail data is normalized only after the response includes a usable workflow identifier. |
| Workflow type-list response | Workflow type-list data is parsed from the backend `{ workflows: [...] }` envelope before it is adapted to the frontend `{ types: [...] }` shape. |

## Parser Test Coverage

The stream parser suite exercises successful backend-shaped stream payloads and malformed data that should never reach React state as trusted domain objects.

| Parser Suite | Positive Coverage | Negative Coverage |
|---|---|---|
| `eventSchemas.test.ts` | AGUI run, text, and tool-call events; job-stream status/progress payloads; workflow SSE payload envelopes. | Unknown AGUI event discriminants, missing required event fields, malformed JSON, unsupported job-stream event types, and missing workflow SSE payload envelopes. |

## Validation Evidence

Validation was run after formatting the touched Sprint 6–9 TypeScript files and after the Sprint 6 leakage cleanup moved direct JSON parsing out of hook modules. The final combined validation for Sprints 6–9 passed from the working tree that includes this sprint.

| Check | Result | Evidence |
|---|---:|---|
| Focused parser tests | PASS | `pnpm vitest run src/agui/eventSchemas.test.ts src/lib/schemas/healthMonitor.test.ts src/lib/schemas/integrations.test.ts src/lib/schemas/provenance.test.ts` completed with **4 passed files** and **18 passed tests**. |
| Frontend typecheck | PASS | `pnpm check` completed successfully in `apps/web`. |
| Stream leakage check | PASS | `grep -R "response\.data as \|JSON\.parse" src/agui/AgentEventClient.ts src/hooks/useJobStream.ts src/hooks/useWorkflows.ts src/hooks/useHealthMonitor.ts src/hooks/useIntegrations.ts src/hooks/useProvenance.ts` returned no matches. |
| Contract freshness gate | PASS | `scripts/ci/check_contract_freshness.sh` completed with exit status `0` and reported that OpenAPI contracts and generated frontend DTO types are current. |
| Whitespace check | PASS | `git diff --check` reported no whitespace errors. |

> Sprint 6 validation concluded with the repository contract gate reporting: `Contract freshness gate passed: OpenAPI contracts and generated frontend DTO types are current.`

## Residual Risks and Follow-Up

The stream schemas validate the discriminants and critical fields that frontend logic consumes. Several event variants intentionally keep `output`, `result`, `delta`, `snapshot`, and custom payloads as `unknown` or flexible record values because those payloads are domain-specific and can vary by agent workflow. A later hardening sprint can introduce workflow-specific payload schemas once those payload contracts are stable.

| Follow-Up | Recommended Priority | Rationale |
|---|---:|---|
| Add a reusable no-direct-stream-parse lint rule | P1 | Sprint 6 centralizes stream parsing, and a guard would prevent future hooks from calling direct JSON parsing in SSE handlers. |
| Add workflow-specific payload schemas | P2 | Current stream validation protects envelope correctness; deeper workflow payload validation should follow once event payload contracts are stable. |
| Consider moving job-stream schemas into `src/lib/schemas` | P2 | Job stream schemas remain local to the hook to minimize churn, but they can be extracted if more consumers need the same event parser. |

## Handoff Recommendation

Sprint 7 should continue with a compact hook domain that still publishes cast-derived API response data. Health monitoring is an appropriate next target because the public hook surface is small, response payloads are user-visible, and parser tests can cover both healthy and malformed alert/metric shapes without requiring broader consumer rewrites.
