# Fabric_4L Layer Design Brief

## Working Title

**From Raw Context to Defensible Value: Layer-by-Layer Execution Architecture**

## Purpose

This brief explains how the Fabric_4L layers should work together as one integrated value-execution system.

The goal is not to describe each layer as an isolated service. The goal is to show how each layer participates in the same fluent workflow:

```text
Raw account context
→ extracted intelligence
→ structured knowledge
→ agentic reasoning
→ validated ground truth
→ benchmarks and realization feedback
→ evidence-backed business case
```

Fabric_4L should operate as a layered value engine where each layer has a clear responsibility, a clear contract, and a clear handoff to the next layer.

---

# Executive Summary

Fabric_4L is organized into layers because value justification requires more than one kind of intelligence.

Each layer answers a different question:

| Layer | Core Question |
|---|---|
| L1 Ingestion | What raw material do we know about this account, market, product, or customer? |
| L2 Extraction | What meaningful signals, entities, evidence, and claims can we extract from that raw material? |
| L3 Knowledge | How do those extracted facts connect into a reusable account/value graph? |
| L4 Agents | What reasoning, recommendations, workflows, and user-facing actions should happen next? |
| L5 Ground Truth | Which outputs are validated, trusted, approved, disputed, or corrected? |
| L6 Benchmarks | What external/internal benchmarks, patterns, and post-production comparisons improve the model? |
| Frontend Experience | How does the user move through the value journey fluently? |
| Governance Layer | How do we enforce tenant isolation, auditability, security, and production readiness? |

The system succeeds when these layers work together to produce a traceable value case:

```text
Signal discovered
→ value path classified
→ driver tree selected
→ assumptions generated
→ evidence attached
→ formulas resolved
→ scenarios calculated
→ business case generated
→ realization tracked
```

---

# Layer Design Principle

## Each Layer Must Produce a Durable Artifact

A layer should not merely process data and disappear. It should produce or update a durable artifact that downstream layers can use.

Examples:

| Layer | Durable Artifact |
|---|---|
| L1 | Ingestion job, source document, source metadata, normalized content record |
| L2 | Extracted signal, entity, claim, evidence candidate, confidence score |
| L3 | Graph node, relationship, account context, value opportunity, provenance trail |
| L4 | Agent workflow run, recommendation, approved action, generated hypothesis |
| L5 | Validation result, truth object, reviewer decision, correction, audit event |
| L6 | Benchmark dataset, comparison result, industry pattern, realization metric |
| Frontend | User decision, workflow state, selected path, edited assumption, generated deliverable |

If a layer does not produce a durable artifact, the workflow becomes hard to resume, audit, test, or explain.

---

# Canonical End-to-End Flow

```text
1. L1 Ingestion
   Collect raw context from websites, documents, CRM, notes, APIs, uploads, and connected sources.

2. L2 Extraction
   Extract entities, signals, claims, evidence candidates, personas, use cases, and value hints.

3. L3 Knowledge
   Normalize those outputs into a tenant-scoped knowledge graph with accounts, signals, stakeholders, value paths, evidence, and relationships.

4. L4 Agents
   Use graph context, value packs, and workflow state to recommend value paths, driver trees, formulas, scenarios, and business case actions.

5. L5 Ground Truth
   Validate, approve, reject, correct, and score claims, evidence, assumptions, and model outputs.

6. L6 Benchmarks
   Compare assumptions and outcomes against industry benchmarks, historical data, and post-production realization metrics.

7. Frontend Workflow
   Present the user with a guided sequence from signal discovery to budget justification and realization tracking.
```

---

# Layer 1 — Ingestion

## Mission

L1 is responsible for collecting, normalizing, and tracking raw source material.

It answers:

> What source material do we have, where did it come from, and is it ready for extraction?

## Inputs

L1 may ingest:

- Company websites
- Product pages
- Case studies
- PDFs
- Sales decks
- Discovery notes
- Call transcripts
- CRM records
- Customer success records
- Support tickets
- Public filings
- Benchmark datasets
- Uploaded documents
- Third-party API data

## Outputs

L1 should produce:

- Source records
- Ingestion jobs
- Normalized content
- Source metadata
- Content hashes
- Tenant/account/source ownership
- Processing status
- Error records
- Retry information

## Key UX Role

L1 powers the user’s confidence that the system has enough account context.

In the UI, L1 should appear as:

```text
Connected Sources
Ingestion Status
Recently Processed Material
Failed or Pending Sources
Source Coverage Score
```

The user should know:

- What has been ingested
- What is still processing
- What failed
- What source supports a later signal or evidence item

## Required Handoffs

```text
L1 source record
→ L2 extraction job
→ L2 extracted entities/signals/evidence
```

L1 must pass:

- tenantId
- accountId
- sourceId
- source type
- normalized content
- metadata
- provenance information

## Design Risks

| Risk | Impact |
|---|---|
| Raw source is ingested but not connected to an account | Downstream outputs cannot be scoped or trusted |
| Ingestion status is invisible | User does not know whether the system is working |
| Source metadata is lost | Evidence and business cases become non-auditable |
| Retry/idempotency is weak | Duplicate or inconsistent extractions |
| Tenant context is missing | Security risk and cross-tenant leakage |

## Definition of Done

L1 is complete when:

- Every source belongs to a tenant.
- Account-linked sources carry accountId.
- Ingestion status is visible.
- Failed jobs are recoverable.
- Source provenance is preserved.
- L2 can reliably consume normalized content.

---

# Layer 2 — Extraction

## Mission

L2 transforms raw content into structured intelligence.

It answers:

> What useful business signals, entities, claims, personas, evidence, and value hints exist inside this source material?

## Inputs

L2 consumes:

- Normalized content from L1
- Source metadata
- Account context
- Value Pack scope
- Extraction rules
- Ontologies
- Prompt/schema definitions

## Outputs

L2 should produce:

- Extracted entities
- Business signals
- Evidence candidates
- Claims
- Stakeholder mentions
- Persona references
- Product/use-case references
- Pain points
- Risk indicators
- Opportunity indicators
- Confidence scores
- Extraction provenance

## Key UX Role

L2 powers the Intelligence experience.

In the UI, L2 should appear as:

```text
Detected Signals
Extracted Evidence Candidates
Stakeholder Mentions
Pain/Opportunity/Risk Labels
Confidence and Source Trace
```

The user should be able to open a signal and see:

- Where it came from
- Why it was extracted
- What confidence the system has
- Which source supports it
- Whether it has already been used in a value model

## Required Handoffs

```text
L2 extracted signal
→ L3 graph node
→ L4 value-path recommendation
```

L2 must pass:

- tenantId
- accountId
- sourceId
- signal type
- extracted text/span
- confidence
- provenance
- candidate value category
- related entities

## Design Risks

| Risk | Impact |
|---|---|
| Signals are extracted but not persisted | User cannot resume or trust workflow |
| Evidence candidates are disconnected from source spans | Business case loses credibility |
| Extraction confidence is hidden | User cannot judge reliability |
| Value Pack scope is ignored | Generic outputs instead of industry-specific intelligence |
| Extracted objects are not promoted to L3 | Downstream graph/workflow cannot use them |

## Definition of Done

L2 is complete when:

- Extracted objects are structured and tenant-scoped.
- Each signal/evidence item has source provenance.
- Confidence is captured.
- Value Pack context influences extraction.
- L3 can consume outputs without manual remapping.

---

# Layer 3 — Knowledge Graph

## Mission

L3 turns extracted intelligence into connected, reusable knowledge.

It answers:

> How do accounts, signals, personas, evidence, value paths, drivers, assumptions, formulas, and business cases relate to each other?

## Inputs

L3 consumes:

- Extracted signals from L2
- Entities and relationships
- Account metadata
- Value Pack taxonomies
- User approvals/rejections
- Agent outputs
- Evidence links
- Formula references

## Outputs

L3 should produce and maintain:

- Account graph
- Entity graph
- Signal graph
- Evidence graph
- Stakeholder map
- Value opportunity nodes
- Value path relationships
- Driver tree relationships
- Assumption/evidence/formula links
- Provenance trails
- Tenant-scoped graph queries

## Key UX Role

L3 powers context continuity.

In the UI, L3 should make it possible to say:

```text
This signal came from these sources.
It relates to this stakeholder.
It maps to this value path.
It supports this driver.
It was used in this scenario.
It appears in this business case.
```

L3 is what prevents Fabric_4L from becoming disconnected screens.

## Required Handoffs

```text
L3 account graph
→ L4 agent workflow
→ L5 validation
→ L6 benchmark comparison
→ Frontend workflow state
```

L3 must pass:

- tenant-scoped graph context
- account context
- signal relationships
- evidence relationships
- value-path relationships
- provenance chain
- graph query results

## Design Risks

| Risk | Impact |
|---|---|
| Graph queries are not tenant-scoped | Critical security risk |
| Signals/evidence do not become graph nodes | Downstream reasoning loses context |
| Relationships are missing | User cannot trace business case back to sources |
| Graph is read-only from user decisions | Approvals and corrections do not improve the model |
| Cypher construction is unsafe | Injection and tenant escape risk |

## Definition of Done

L3 is complete when:

- Every tenant-owned node and edge is scoped.
- Cypher execution is tenant-safe.
- Signals, evidence, stakeholders, opportunities, and models are connected.
- L4 agents can retrieve current workflow context.
- Business cases are traceable back through the graph.

---

# Layer 4 — Agents and Workflows

## Mission

L4 orchestrates reasoning, recommendations, and user-facing workflow actions.

It answers:

> Given the current account, graph context, value pack, and user workflow state, what should happen next?

## Inputs

L4 consumes:

- L3 graph context
- Value Pack definitions
- Current workflow state
- User intent
- Agent prompts/tools
- Evidence candidates
- Existing value models
- Scenario results
- Validation feedback from L5
- Benchmarks from L6

## Outputs

L4 should produce:

- Value hypotheses
- Value path recommendations
- Driver tree suggestions
- Evidence matching actions
- Formula recommendations
- Scenario suggestions
- Business case drafts
- Agent action logs
- Workflow run records
- Human approval requests

## Key UX Role

L4 powers the agentic experience.

In the UI, L4 appears as:

```text
Right Rail Agent
Recommended Next Action
Generated Hypotheses
Suggested Driver Trees
Evidence Finder
Business Case Drafting Assistant
Workflow Automation
```

The agent should not behave like a generic chat window. It should understand the current page/entity/workflow context.

## Required Handoffs

```text
L4 recommendation/action
→ Frontend decision
→ L5 validation
→ L3 graph update
→ L6 benchmark comparison
```

L4 must pass:

- workflowRunId
- tenantId
- accountId
- current entity context
- recommendation payload
- confidence/rationale
- tool call trace
- approval status

## Design Risks

| Risk | Impact |
|---|---|
| Agents generate text but do not mutate real state | App feels impressive but not executable |
| Agent lacks current account/signal/model context | Recommendations are generic or wrong |
| Agent side effects are not idempotent | Duplicate models or corrupted workflow state |
| No approval gates | Risky autonomous changes |
| Prompt/tool versions are not tracked | Outputs become non-auditable |

## Definition of Done

L4 is complete when:

- Agents operate with explicit tenant/account/workflow context.
- Agent actions can update real app state.
- Human approval gates exist for important changes.
- Workflows can checkpoint and resume.
- Tool calls are auditable.
- Outputs are validated before persistence.

---

# Layer 5 — Ground Truth and Validation

## Mission

L5 determines what is trusted, approved, rejected, corrected, or validated.

It answers:

> Which claims, assumptions, evidence items, recommendations, and model outputs are reliable enough to use?

## Inputs

L5 consumes:

- Extracted claims
- Evidence candidates
- User approvals/rejections
- Agent-generated hypotheses
- Scenario assumptions
- Business case outputs
- Validation rules
- Reviewer decisions
- Historical corrections

## Outputs

L5 should produce:

- Validation records
- Truth objects
- Approval/rejection decisions
- Confidence adjustments
- Correction records
- Reviewer comments
- Quality scores
- Audit trail
- Model feedback signals

## Key UX Role

L5 powers trust.

In the UI, L5 should appear as:

```text
Evidence Quality
Assumption Confidence
Approved / Rejected / Needs Review
Validation Warnings
Ground Truth History
Reviewer Notes
```

A user should know whether a number in a business case is:

- benchmark-derived
- user-entered
- agent-estimated
- evidence-backed
- validated
- disputed
- stale

## Required Handoffs

```text
L5 validation result
→ L3 graph relationship update
→ L4 agent refinement
→ Frontend trust indicators
→ Business case traceability
```

L5 must pass:

- validation status
- reviewer decision
- confidence score
- correction payload
- audit event
- source object reference

## Design Risks

| Risk | Impact |
|---|---|
| Generated assumptions are never validated | Business case may not be credible |
| Evidence approval is local-only | Downstream model does not know what is trusted |
| Corrections do not feed back into graph/agents | System does not improve |
| Validation state is invisible | User cannot trust outputs |
| Audit trail is incomplete | Enterprise governance gap |

## Definition of Done

L5 is complete when:

- Important outputs have validation state.
- User decisions persist.
- Corrections update downstream context.
- Trust indicators are visible in the UI.
- Validation records are auditable.
- Business cases can cite approval status.

---

# Layer 6 — Benchmarks and Realization

## Mission

L6 provides benchmark comparison, industry context, and post-production value learning.

It answers:

> How do this account’s assumptions and outcomes compare to credible benchmarks and realized value?

## Inputs

L6 consumes:

- Industry benchmark datasets
- Value Pack benchmark policies
- Scenario assumptions
- Historical customer outcomes
- Realization metrics
- Post-sale performance data
- Ground truth feedback

## Outputs

L6 should produce:

- Benchmark comparisons
- Industry ranges
- Assumption reasonableness scores
- Realization tracking metrics
- Variance analysis
- Outcome comparisons
- Benchmark-backed recommendations
- Post-production learning signals

## Key UX Role

L6 powers credibility and continuous improvement.

In the UI, L6 should appear as:

```text
Benchmark Range
Assumption Reasonableness
Industry Comparison
Expected vs Actual Value
Realization Dashboard
Variance Analysis
```

The user should be able to see whether an assumption is aggressive, conservative, or aligned with benchmark norms.

## Required Handoffs

```text
L6 benchmark comparison
→ L4 recommendation
→ L5 validation status
→ Frontend scenario warning
→ Business case support
```

L6 must pass:

- tenantId
- benchmark dataset ID
- industry
- value path
- driver/assumption reference
- comparison result
- confidence/range
- benchmark provenance

## Design Risks

| Risk | Impact |
|---|---|
| Benchmark queries are not tenant-scoped | Cross-tenant leakage risk |
| Benchmarks are generic and not tied to Value Packs | Weak credibility |
| Calculator does not consume benchmark ranges | Scenario modeling becomes arbitrary |
| Realization metrics do not feed back into future models | System does not learn |
| Benchmark provenance is hidden | CFO-level trust is reduced |

## Definition of Done

L6 is complete when:

- Benchmarks are tenant-safe.
- Benchmark source/provenance is visible.
- Value Packs influence benchmark selection.
- Scenario assumptions can be compared to benchmark ranges.
- Realized value feeds future models.
- Business cases can cite benchmark support.

---

# Frontend Experience Layer

## Mission

The frontend turns the layered architecture into a fluent user journey.

It answers:

> Can a real user move from account intelligence to a defensible business case without manually stitching the system together?

## Responsibilities

The frontend should:

- Guide the user through the value workflow
- Preserve context across screens
- Make next actions obvious
- Show source/evidence/provenance
- Display validation status
- Expose benchmark context
- Let the agent act in current context
- Support resume and revision
- Make the final business case traceable

## Recommended UX Flow

```text
Account Overview
→ Signals
→ Opportunities
→ Value Paths
→ Driver Tree
→ Evidence
→ Assumptions
→ Scenarios
→ Business Case
→ Realization
```

## Critical Context to Preserve

Every major route/hook/mutation should preserve:

- tenantId
- accountId
- valuePackId
- sourceId
- signalId
- opportunityId
- valuePath
- driverTreeId
- assumptionId
- evidenceId
- scenarioId
- businessCaseId
- workflowRunId

## Design Risks

| Risk | Impact |
|---|---|
| Pages exist but do not hand off data | App feels like disconnected modules |
| Buttons update local state only | Workflow cannot persist or resume |
| Agent right rail lacks page context | Agent gives generic answers |
| Calculator uses mock data | Business case is not traceable |
| Cache invalidation is missing | User sees stale or inconsistent state |

## Definition of Done

The frontend is complete when:

- Every workflow step has a primary next action.
- Every action has a real handler/hook/API chain.
- Every mutation updates state and downstream screens.
- Loading/error/empty states are consistent.
- Resume works after refresh.
- Business case output is traceable to source data.

---

# Governance, Security, and Observability Layer

## Mission

The governance layer ensures that Fabric_4L is safe, auditable, tenant-isolated, and production-ready.

It answers:

> Can this system safely process enterprise customer data and prove how decisions were made?

## Responsibilities

Governance should enforce:

- Tenant isolation
- Auth and authorization
- Request context propagation
- Rate limiting
- Audit logging
- Secret management
- Trace IDs and request IDs
- Policy gates
- Production readiness checks
- Contract enforcement
- Observability and alerts

## Cross-Layer Requirements

Every layer must support:

- tenantId propagation
- requestId / traceId propagation
- structured logging
- health checks
- readiness checks
- metrics
- safe error handling
- audit events for sensitive operations

## Design Risks

| Risk | Impact |
|---|---|
| Tenant context is dropped between layers | Security breach |
| Logs lack correlation IDs | Debugging and incident response suffer |
| No audit trail for generated outputs | Enterprise trust gap |
| Health checks are shallow | Deployments appear healthy while workflows fail |
| CI gates do not run meaningful tests | False production readiness |

## Definition of Done

Governance is complete when:

- Tenant context is mandatory across all tenant-owned operations.
- Cross-layer calls are traceable.
- Sensitive actions are audited.
- Health/readiness/metrics are consistent.
- CI gates enforce security, contract, and workflow correctness.

---

# Cross-Layer Data Contracts

## Required Context Envelope

Every cross-layer call should carry a context envelope:

```json
{
  "tenantId": "tenant_123",
  "accountId": "account_456",
  "userId": "user_789",
  "requestId": "req_abc",
  "workflowRunId": "wf_001",
  "valuePackId": "vp_saas_ai",
  "source": "frontend|agent|batch|api"
}
```

## Required Artifact Metadata

Every durable artifact should include:

```json
{
  "id": "artifact_id",
  "tenantId": "tenant_123",
  "accountId": "account_456",
  "createdAt": "timestamp",
  "updatedAt": "timestamp",
  "createdBy": "user_or_agent",
  "sourceIds": ["source_1"],
  "provenance": {},
  "validationStatus": "unreviewed|approved|rejected|needs_review",
  "confidence": 0.84
}
```

## Required Handoff Pattern

Each layer handoff should be explicit:

```text
Input artifact
→ transformation or reasoning step
→ output artifact
→ persisted state
→ downstream reference
→ visible UI state
```

---

# Layer-by-Layer Handoff Map

| Handoff | Required Artifact | UX Result |
|---|---|---|
| L1 → L2 | Normalized source content | Source becomes extractable |
| L2 → L3 | Extracted signal/evidence/entity | Signal appears in Intelligence |
| L3 → L4 | Account/value graph context | Agent can reason in context |
| L4 → L5 | Recommendation/hypothesis/assumption | User can approve or validate |
| L5 → L3 | Validation status/correction | Graph trust state updates |
| L3/L5 → L6 | Assumptions and drivers | Benchmarks compare model reasonableness |
| L6 → L4 | Benchmark result | Agent refines scenarios |
| L4/L6 → Frontend | Recommended action/context | User sees next best action |
| Frontend → L3/L5 | User decision | Workflow state and trust state persist |

---

# Testing Implications by Layer

## L1 Tests

- Ingestion job creation
- Source ownership and tenant scoping
- Retry/idempotency
- Failed source recovery
- Provenance preservation

## L2 Tests

- Extraction schema validity
- Confidence scoring
- Source-span provenance
- Value Pack scoped extraction
- Promotion to L3 format

## L3 Tests

- Tenant-scoped graph queries
- Cypher injection protection
- Relationship integrity
- Signal/evidence/value path linkage
- Graph query contract tests

## L4 Tests

- Workflow checkpoint/resume
- Tool-call tenant propagation
- Agent output validation
- Human approval gates
- Idempotent side effects

## L5 Tests

- Validation record creation
- Approve/reject/correct flows
- Trust state propagation
- Audit logging
- Downstream graph updates

## L6 Tests

- Tenant-scoped benchmark access
- Dataset comparison isolation
- Industry benchmark selection
- Reasonableness scoring
- Realization feedback loop

## Frontend Tests

- Clickpath tests
- Hook/mutation/API chain tests
- Query invalidation
- Route context preservation
- Resume workflow
- Business case traceability

## Governance Tests

- Auth required
- Tenant context mandatory
- Dev bypass blocked in production
- Secret leakage checks
- CI gate collection guards
- OpenAPI contract enforcement

---

# Production Readiness Criteria by Layer

| Layer | Production-Ready When... |
|---|---|
| L1 | Ingestion is tenant-scoped, observable, retry-safe, and provenance-preserving |
| L2 | Extraction is structured, source-grounded, value-pack aware, and graph-ready |
| L3 | Knowledge graph is tenant-safe, connected, queryable, and traceable |
| L4 | Agents act in context, checkpoint safely, and mutate state through approved workflows |
| L5 | Trust decisions persist, audit trails exist, and corrections feed downstream systems |
| L6 | Benchmarks are scoped, credible, explainable, and tied to model assumptions/outcomes |
| Frontend | User can complete the full value workflow through real clicks and persisted state |
| Governance | Security, observability, auditability, and CI gates enforce correctness continuously |

---

# Recommended Layer Ownership

| Area | Primary Owner | Secondary Owner |
|---|---|---|
| L1 Ingestion | Data Platform | Backend |
| L2 Extraction | AI/Data Engineering | Ontology/Value Pack Owner |
| L3 Knowledge | Graph/Backend Platform | Security |
| L4 Agents | Agent Platform | Product/UX |
| L5 Ground Truth | Trust/Governance | Product Operations |
| L6 Benchmarks | Data/Analytics | Value Engineering |
| Frontend | Product Engineering | Design |
| Governance | Security/Platform | QA/Release |

---

# Design Review Questions by Layer

## L1

- Can the user see what sources were ingested?
- Can failed sources be retried?
- Is every source traceable to a tenant/account?

## L2

- Can the user inspect why a signal was extracted?
- Does each extracted object have source evidence?
- Are outputs shaped for downstream graph use?

## L3

- Can the user trace a business case back to signals and evidence?
- Are graph queries tenant-safe?
- Are relationships rich enough to support workflow continuity?

## L4

- Does the agent know the current account, signal, and workflow step?
- Can agent actions update real state?
- Are approvals required before important changes?

## L5

- Can the user see what is trusted, disputed, or unreviewed?
- Do approvals and corrections persist?
- Does validation state appear in the business case?

## L6

- Can the user see whether assumptions are reasonable?
- Are benchmarks scoped to the right industry/value pack?
- Does realized value improve future recommendations?

## Frontend

- Is the next action obvious?
- Does the app preserve context between screens?
- Can the user resume later?

## Governance

- Is tenant context mandatory?
- Are decisions auditable?
- Do CI gates prove the system is safe?

---

# Final Positioning

Fabric_4L is not merely a multi-service architecture. It is a layered value justification engine.

Each layer exists to move the user closer to a credible business outcome:

```text
Ingest context
→ extract meaning
→ connect knowledge
→ reason with agents
→ validate trust
→ compare to benchmarks
→ generate defensible value
→ track realized outcomes
```

The architecture is successful only when the layers operate as one fluent system that helps enterprise teams quantify, defend, and prove business value across revenue uplift, cost savings, and risk reduction.

