---
description: Assess production readiness across all 5 layers and generate a sprint plan to address critical blockers
---

# Fabric_4L Launch Readiness Assessment & Sprint Plan

Use this workflow to assess the current production readiness of the Value Fabric platform and generate a concrete sprint plan to address critical blockers.

## Activation Criteria

Manual activation:
- Pre-release readiness reviews
- Quarterly planning sessions
- After completing major roadmap tasks
- When preparing for production deployment

## Workflow Steps

1. **Initialize Context**
   // turbo
   - Read `ROADMAP.md` from repository root
   - Read `Phase2_Readiness_Status.md` if it exists
   - Extract current completion percentages per layer (L1-L5, Frontend, DevOps)
   - Identify critical path tasks (P0) and their current status
   - Map test suite status from recent test runs

2. **Assess Readiness Level**
   Calculate overall readiness weighted by layer:
   - L1 Ingestion (target: 90%)
   - L2 Extraction (target: 95%)
   - L3 Knowledge Graph (target: 90%)
   - L4 Agents (target: 85%)
   - L5 Ground Truth (target: 100% - already complete)
   - Frontend (target: 85%)
   - DevOps (target: 80%)

3. **Identify Top 5 Risks Blocking Launch**
   Based on ROADMAP.md gaps and test failures:
   - Missing cross-layer integration verification (Smoke Gate)
   - Neo4j Vector Index E2E not fully verified
   - Frontend still using mock data on key screens
   - CI/CD pipeline not implemented
   - Test suite instability (flaky L3 E2E tests)

4. **Define Critical Missing Capabilities**
   Map to actual ROADMAP.md tasks:
   - Task 25: Vector Index E2E Verification (L3)
   - Task 26: Cross-Layer Production Smoke Gate (DevOps)
   - Task 27: Frontend Reality Pass - Static Screens (Frontend)
   - Task 14: CI/CD Pipeline (DevOps)
   - Task 22: Workflow Control API Parity (L4)

5. **Generate Sprint Plan**
   Create 5 sprints aligned to critical path:

   **Sprint 1 — L3 Vector E2E & Neo4j Verification**
   - Goal: Complete Task 25 - verify vector indexes with real embeddings
   - Tasks:
     - [ ] Vector index creation verified with real embeddings in Neo4j 5.x
     - [ ] `POST /v1/ingest` creates nodes with embedding property
     - [ ] `POST /v1/search/hybrid` returns vector+graph ranked results
     - [ ] E2E test passes: Extract → Ingest → Hybrid Search
   - Exit Criteria: `test_vector_e2e.py` passes; hybrid search returns real results

   **Sprint 2 — Cross-Layer Integration & Smoke Gate**
   - Goal: Complete Task 26 - repeatable cross-layer verification
   - Tasks:
     - [ ] Create `scripts/smoke/production_smoke.ps1` for single-command validation
     - [ ] Validate L2 extract → L3 ingest → Graph query → Hybrid search happy path
     - [ ] GitHub Actions workflow `smoke-gate.yml` runs against docker-compose
     - [ ] JSON artifact stores pass/fail + timing per stage
   - Exit Criteria: CI fails on contract/status code regressions; smoke gate passes

   **Sprint 3 — Frontend Reality Pass**
   - Goal: Complete Task 27 - replace static/demo data with real API data
   - Tasks:
     - [ ] `GraphExplorer` consumes real `POST /v1/graph/query` data
     - [ ] `ExtractionEngine` consumes real `GET /v1/jobs/{id}` + SSE events
     - [ ] `BusinessCase` fetches from `GET /v1/business-cases/{id}`
     - [ ] `DecisionTrace` shows real provenance from `GET /v1/provenance/{entity_id}`
     - [ ] Loading/error/empty states for all updated screens
   - Exit Criteria: All 4 screens show real data; error boundaries active

   **Sprint 4 — L4 Workflow Controls & CI/CD**
   - Goal: Complete Task 22 + Task 14 - operator controls + automation
   - Tasks:
     - [ ] `POST /v1/workflows/{id}/pause` implemented (Task 28 already done)
     - [ ] Document resume contract in endpoint docstrings
     - [ ] `GET /v1/workflows/active` and `GET /v1/workflows/{id}/events` examples
     - [ ] GitHub Actions PR checks (lint, test, build)
     - [ ] Main branch builds and pushes to container registry
   - Exit Criteria: Pause/resume controls functional; CI green on PRs

   **Sprint 5 — Final Polish & Production Hardening**
   - Goal: Complete remaining gaps and execute production deployment
   - Tasks:
     - [ ] Task 29: Formula + Value Tree Backend Contracts (L3)
     - [ ] Task 13: Monitoring + Health Dashboards (Prometheus/Grafana)
     - [ ] Task 24: Coverage/Quality Enforcement in CI (80% threshold)
     - [ ] Task 10: Extraction Streaming + Job Status (L2/Frontend)
     - [ ] Final security audit and dependency updates
   - Exit Criteria: All P0 tasks complete; production checklist passes

6. **Define Cross-Cutting Tracks**
   - **Test Reliability**: Zero-tolerance for new flaky tests; mandatory coverage for critical paths
   - **Observability Rollout**: OpenTelemetry tracing and Prometheus metrics across all layers
   - **API Contract Stability**: Backward-compatible changes only; smoke gate enforced
   - **Documentation**: Inline docstrings + API docs for all new endpoints

7. **Calculate Critical Path**
   Identify longest dependency chain:
   1. Sprint 1: Vector E2E (unblocks hybrid search)
   2. Sprint 2: Smoke Gate (unblocks CI confidence)
   3. Sprint 3: Frontend Reality Pass (unblocks user testing)
   4. Sprint 5: Final contracts (unblocks production)

8. **Identify Quick Wins**
   High impact / low effort items from ROADMAP.md:
   - Fix structured logging misuse (logger.error kwargs)
   - Add `pythonpath` to `pyproject.toml` for test collection
   - Update endpoint docstrings for pause/resume contract
   - Create smoke gate script using existing test patterns

9. **Generate Final Launch Checklist**
   - [ ] All P0 tasks completed and verified
   - [ ] Smoke gate passes consistently in CI
   - [ ] No cross-layer data contract violations
   - [ ] Frontend shows real data on all critical screens
   - [ ] Test suite >80% coverage on touched modules
   - [ ] CI pipeline green (lint, typecheck, tests, security)
   - [ ] Docker Compose stack starts all services cleanly
   - [ ] Health checks return actual dependency status
   - [ ] Prometheus metrics endpoints return real counters
   - [ ] Documentation updated for all new endpoints

10. **Present Assessment & Await Approval**
    - Display readiness percentage by layer
    - Show top 5 risks with mitigation strategies
    - Present sprint plan with dependencies visualized
    - Ask: "Approve this sprint plan and readiness assessment?"
    - Only on explicit "yes": proceed to create artifacts

11. **Create Artifacts (on approval)**
    // turbo
    - Save assessment report to `.windsurf/plans/launch-readiness-{date}.md`
    - Update `Phase2_Readiness_Status.md` if it exists
    - Stage changes for user commit

## Constraints

- **Maximum 5 P0 tasks per sprint**: Prevent over-prioritization
- **Time-boxed sprints**: 1-2 weeks each
- **Dependency-aware**: Never schedule downstream work before upstream blockers
- **Measurable exit criteria**: Every sprint must have verifiable completion conditions
- **Test-driven**: Every sprint must include test coverage for new code

## Output Format

```markdown
# Launch Readiness Assessment - {YYYY-MM-DD}

**Overall Readiness: {N}%**

| Layer | Current | Target | Gap |
|-------|---------|--------|-----|
| L1 Ingestion | {N}% | 90% | {N}% |
| L2 Extraction | {N}% | 95% | {N}% |
| L3 Knowledge | {N}% | 90% | {N}% |
| L4 Agents | {N}% | 85% | {N}% |
| L5 Ground Truth | 100% | 100% | 0% |
| Frontend | {N}% | 85% | {N}% |
| DevOps | {N}% | 80% | {N}% |

## Top 5 Risks
1. [Risk description] -> [Mitigation from ROADMAP.md Task X]
...

## Sprint Plan Summary
- Sprint 1: [Focus] ([dates]) -> [Exit criteria]
...

## Quick Wins
- [ ] [Quick win 1]
...

## Launch Checklist
- [ ] [Criterion 1]
...
```

## Execution Log Format

Present progress using this structured format:

```
[INIT] Reading ROADMAP.md - Current overall: ~{N}% complete
[ASSESS] Layer readiness: L1={N}% L2={N}% L3={N}% L4={N}% L5=100% FE={N}% DO={N}%
[RISKS] Identified top 5 risks blocking launch
[PLAN] Generated 5 sprints with dependency ordering
[CHECKLIST] Final launch checklist: {N}/{total} criteria currently met
[REVIEW] Presenting to user for approval...
[ARTIFACTS] User approved - Creating assessment report
[COMPLETE] Assessment saved, changes staged for commit
```

## Concrete Actions Checklist

Ensure measurable outcomes:

- [ ] Read and analyzed `ROADMAP.md` current state
- [ ] Calculated readiness percentage per layer
- [ ] Identified top 5 risks with ROADMAP.md task mappings
- [ ] Generated 5 sprints with clear exit criteria
- [ ] Mapped quick wins from existing task list
- [ ] Created final launch checklist with {N}/{total} current status
- [ ] Presented assessment to user and awaited explicit approval
- [ ] Only after approval: created artifact in `.windsurf/plans/`
- [ ] Verified formatting matches existing workflow style

## Safety Rules

1. **Never create artifacts without explicit user approval**
2. **Preserve existing ROADMAP.md structure** - do not modify during assessment
3. **Use actual ROADMAP.md task numbers** (Task 20-29) when referencing work
4. **Base readiness percentages on ROADMAP.md completion table** (lines 15-24)
5. **Log all risk mitigations** with specific task references
