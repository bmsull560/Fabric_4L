# Route → Layer Dependency Map (P0/P1)

**Owner:** Frontend Platform  
**Last updated:** May 7, 2026  
**Purpose:** Define route-family dependencies across Layers 1–6 and the required UI fallback mode when each dependency fails.

## Fallback mode definitions

- **Retry:** transient error; UI must provide retry action/auto-refetch.
- **Degraded mode:** route still renders with partial data and explicit stale/partial status.
- **Blocking gate:** workflow step cannot proceed until dependency recovers.
- **Read-only mode:** existing data can be viewed, but edits/mutations are disabled.

## P0 route families

| Route family (P0) | Primary dependency layers | Secondary dependency layers | Required fallback behavior |
|---|---|---|---|
| `/accounts`, `/workflow/prospect`, `/workflow/value-case`, `/value-case/:accountId`, `/deliverables/cases/:caseId` | **L4** orchestration/workflow state, **L3** account graph context | **L1** ingestion freshness, **L5** ground-truth approvals | L4 failure = **blocking gate** for progression; L3 failure = **degraded mode** with stale snapshot banner; L1/L5 failure = **read-only mode** plus **retry** for freshness checks. |
| `/calculator/:accountId`, `/calculator/:accountId/roi`, `/workflow/calculator`, `/workflow/evidence`, `/realization/:accountId` | **L3** formulas/graph/value data, **L4** orchestration for run state | **L5** evidence truth validation, **L6** benchmark datasets | L3 compute read failure = **blocking gate** for save/export; L4 run failure = **retry** with preserved inputs; L5/L6 failure = **degraded mode** with assumptions badge and no final approval action. |
| `/governance`, `/governance/traces`, `/deliverables`, `/deliverables/cases/:caseId` | **L5** review and audit controls, **L4** decision workflows | **L3** evidence lineage context | L5 failure = **blocking gate** for approval/export; L4 failure = **read-only mode** for prior decisions; L3 failure = **degraded mode** hiding deep lineage drill-down with **retry** affordance. |
| `/workflow/intelligence`, `/context/agents`, `/governance/evidence`, `/governance/traces` | **L4** agent orchestration + guardrails, **L5** policy/governance checks | **L3** retrieval context, **L2** extraction artifacts | L4 guardrail timeout/failure = **blocking gate** for AI output publication; L5 policy check failure = **blocking gate**; L3/L2 failure = **degraded mode** with unsupported-claim warnings and explicit **retry**. |
| `/context/*`, `/workflow/*`, `/studio/:accountId/*`, `/command-center` | **L4** route-level orchestrated workflow state, **L3** knowledge views | **L1/L2** pipeline status, **L5** governance state, **L6** benchmark overlays | Primary data failures = **degraded mode** with scoped panels; mutation intents are **read-only mode** until primary recovers; upstream pipeline errors show **retry** at panel scope; governance denials enforce **blocking gate** where required. |

## P1 route families

| Route family (P1) | Primary dependency layers | Secondary dependency layers | Required fallback behavior |
|---|---|---|---|
| `/intelligence/:accountId*` | **L4**, **L3** | **L2**, **L5** | L4 generation paths use **retry** then **degraded mode**; L3 retrieval gaps show partial cards; L5 policy failures enforce **blocking gate** for publish/export. |
| `/studio/:accountId*` | **L4**, **L3** | **L5**, **L6** | Studio edits become **read-only mode** on L4 mutation failure; L3 miss = **degraded mode**; L5 approval failures are **blocking gate** for release actions; L6 miss allows **retry** and assumption fallback. |
| `/context/sources`, `/context/extraction`, `/context/ontology`, `/context/formulas`, `/context/models`, `/context/packs` | **L1**, **L2**, **L3** | **L4**, **L5** | Source/extraction job failures use **retry** with job status retention; schema/catalog outages = **read-only mode**; governance-enforced writes remain behind **blocking gate**. |
| `/personal/*`, `/settings/*`, `/settings/team/*`, `/settings/governance/*`, `/settings/data/*` | **L4** admin/workflow APIs, **L5** audit/policy | **L3** lookups | Sensitive setting write failures default to **read-only mode**; policy/audit dependency failures enforce **blocking gate** on privileged actions; lookup failures are **degraded mode**. |
| `/command-center`, `/governance/evidence`, `/governance/traces`, `/context/*` | **L3** retrieval/search, **L4** ranking/orchestration | **L5** permission checks | Search backend failures = **retry** + empty-safe **degraded mode**; permission uncertainty = **blocking gate** for restricted results. |
| `/deliverables`, `/deliverables/cases/:caseId`, `/workflow/value-case` | **L4**, **L5** | **L3**, **L6** | Publish/export steps require **blocking gate** on L5; L4 generation issues support **retry**; L3/L6 gaps render **degraded mode** and freeze finalization in **read-only mode**. |

## Layer ownership quick reference

| Layer | Responsibility (UI dependency lens) |
|---|---|
| L1 | Source ingestion status and source configuration fidelity. |
| L2 | Extraction jobs/artifacts and parsed document state. |
| L3 | Knowledge graph, formulas, retrieval context, and value models. |
| L4 | Agent/workflow orchestration, generation, and cross-route progression state. |
| L5 | Governance, policy, approvals, audits, and ground-truth controls. |
| L6 | Benchmarks/comparators used for scenario assumptions and normalization. |
