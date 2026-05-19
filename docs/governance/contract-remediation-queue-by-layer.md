# Contract Remediation Queue by Layer (From 2026-05-02 Audit)

Source: `reports/CONTRACT_AUDIT_REPORT.md`.

## Prioritized Queue (highest risk + lowest compliance first)

### Layer 4 (current score: 45%)
Owner: Layer 4 Platform Team (`@layer4-agents`)

- **Cluster L4-C1: Tool exceptions violate Contract §2.4**
  - Scope: `services/layer4-agents/src/**`
  - Current: ~27 high-severity throws in tools.
  - Required closure set: runtime tool boundary wrappers + schema-aligned `ToolResult` + frontend/tool consumers + regression tests.
- **Cluster L4-C2: Agent output parsing via `json.loads` violates Contract §2.5**
  - Scope: layer4 agent output handlers.
  - Current: part of 49 backend matches (report isolates ~8 high-priority).
  - Required closure set: runtime structured generation + contract schema sync + frontend consumer compatibility + regression tests.

Targets/deadlines:
- **2026-05-23:** 45% → 58%
- **2026-06-06:** 58% → 70%
- **2026-06-27:** 70% → 85%

### Layer 2 (current score: 58%)
Owner: Layer 2 Extraction Team (`@layer2-extraction`)

- **Cluster L2-C1: Agent output `json.loads` usage (§2.5)**
- **Cluster L2-C2: Tenant context propagation drift (§2.1)**

Targets/deadlines:
- **2026-05-30:** 58% → 65%
- **2026-06-13:** 65% → 75%
- **2026-07-04:** 75% → 85%

### Layer 1 (current score: 62%)
Owner: Layer 1 Ingestion Team (`@layer1-ingestion`)

- **Cluster L1-C1: Tenant context parameterization drift (§2.1)**
- **Cluster L1-C2: DB session isolation gaps (§2.2)**

Targets/deadlines:
- **2026-05-30:** 62% → 70%
- **2026-06-20:** 70% → 80%
- **2026-07-11:** 80% → 85%

### Frontend (current score: 67%)
Owner: Web Platform Team (`@web-platform`)

- **Cluster FE-C1: Imperative navigation (§2.6)**
- **Cluster FE-C2: URL string concatenation (§2.6)**

Targets/deadlines:
- **2026-05-30:** 67% → 72%
- **2026-06-20:** 72% → 80%
- **2026-07-11:** 80% → 85%

### Layer 3 (current score: 71%)
Owner: Layer 3 Knowledge Team (`@layer3-knowledge`)

- **Cluster L3-C1: Agent output parsing drift (§2.5)**
- **Cluster L3-C2: Tenant/DB contract drift (§2.1/§2.2)**

Targets/deadlines:
- **2026-05-30:** 71% → 76%
- **2026-06-20:** 76% → 82%
- **2026-07-11:** 82% → 88%

### Layer 5 (current score: 85%)
Owner: Ground Truth Team (`@layer5-ground-truth`)

- Sustainment only: no regressions, close residual partials.

Targets/deadlines:
- **2026-06-06:** 85% → 87%
- **2026-06-27:** 87% → 90%

### Layer 6 (current score: 90%)
Owner: Benchmarks Team (`@layer6-benchmarks`)

- Sustainment only: maintain green baseline and guardrails.

Targets/deadlines:
- **2026-06-27:** Maintain ≥90%

## Cluster Closure Rule (No Partial Drift)
Each cluster is only marked closed when all are merged together:
1. Runtime contract-aligned backend change.
2. Updated schema/type artifacts.
3. Updated consumers (frontend and/or downstream service).
4. Regression tests proving non-reintroduction.


## Tenant Isolation Coverage Remediation Queue (endpoint-level)

Last updated: 2026-05-18.

| Layer | Uncovered endpoint/route-group backlog | Owner | Due date | Notes |
|---|---|---|---|---|
| L1 | Ingestion exports/admin compatibility surfaces not yet in hostile matrix | @layer1-ingestion | 2026-05-30 | Add route-level hostile tests + matrix row updates. |
| L2 | Secondary extraction admin/reporting routes missing explicit cross-tenant/missing-context assertions | @layer2-extraction | 2026-06-13 | Extend matrix to include remaining status/admin endpoints. |
| L3 | Non-product graph search/subgraph endpoints missing route-level hostile tests in matrix | @layer3-knowledge | 2026-06-20 | Add tenant-hostile coverage for list/read/search variants. |
| L4 | Workflow adjunct endpoints (stream/replay/archive variants) require full matrix mapping | @layer4-agents | 2026-06-06 | Align with existing security invariants suite; add missing fail-closed cases. |
| L5 | Bulk/sync expansion endpoints need explicit endpoint rows tied to hostile tests | @layer5-ground-truth | 2026-06-06 | Keep matrix current for new bulk/sync operations. |
| L6 | Compare/industry-list/validation endpoint families not fully represented in cross-layer matrix | @layer6-benchmarks | 2026-06-27 | Add route-specific hostile + missing-context tests. |
