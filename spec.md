# Spec: 4-Sprint MVP Delivery Roadmap (Value Fabric)

## Status
Ready for review — pending user confirmation

---

## Problem Statement

Value Fabric is a six-layer enterprise SaaS platform currently at ~90–95% completion (per `docs/readiness/current.md`). The existing `ROADMAP.md` tracks layer-by-layer completion percentages and a prior 3-sprint hardening plan (Tasks 92–108). However, the team lacks a structured, sprint-cadenced delivery plan that maps remaining gaps to concrete sprint backlogs, defines done criteria per sprint, and includes a retrospective template to capture feedback and adjust velocity.

This spec defines the work to **append a 4-sprint MVP delivery roadmap section to `ROADMAP.md`**. Each sprint is 3 weeks. The roadmap is grounded in the real platform state (confirmed gaps from the live codebase audit), targeted at the internal dev team, and includes a per-sprint retrospective template.

---

## Scope

### In scope
- Appending a new `## 4-Sprint MVP Delivery Roadmap` section to `ROADMAP.md`
- Sprint 1 (weeks 1–3): Foundations — test infrastructure, CI/CD, environment provisioning
- Sprint 2 (weeks 4–6): Core fixes — functional test failures, Pydantic v2 migration, CoreferenceResolver
- Sprint 3 (weeks 7–9): Feature expansion & integration — Layer 3 gaps, k8s hardening, frontend tests, L2→L3 pipeline
- Sprint 4 (weeks 10–12): Polish & release — E2E tests, tenant isolation audit, telemetry, release candidate, UAT
- Per-sprint retrospective template (What went well / What didn't / Action items)
- Sprint demo checklist at the end of each sprint

### Out of scope
- Implementing the work items themselves (this spec covers the roadmap document only)
- Modifying any source code, tests, or infrastructure files
- Stakeholder presentation deck (internal dev team audience only)

---

## Platform State (as of 2026-05-17)

Confirmed gaps that the sprint roadmap must address:

| Gap | Location | Sprint |
|---|---|---|
| `make test-layer*` targets use global pytest, missing service venvs | `Makefile:260–277` | S1 |
| `structlog`, `prometheus_client`, `testcontainers` not in global env | global env | S1 |
| `HarnessRunRepository.list()` returns tuple; 3 tests iterate as list | `services/layer4-agents/src/harness/repositories.py:291` | S2 |
| Stale `get_openai_provider` mock patch in langgraph execution tests | `services/layer4-agents/tests/test_langgraph_execution.py:107` | S2 |
| `BusinessCaseInputData` fixture missing required field | `test_langgraph_execution.py` | S2 |
| `SignalDetectionAgent` returns 0 signals (parsing regression) | `services/layer4-agents/` | S2 |
| `CoreferenceResolver.resolve()` is a no-op | `services/layer2-extraction/` | S2 |
| `packages/platform-contract` uses Pydantic v1 validators | `packages/platform-contract/` | S2 |
| `formulas.py:579` category filter is `pass` (unimplemented) | `services/layer3-knowledge/` | S3 |
| `k8s/base/` and top-level manifests use local image paths | `k8s/` | S3 |
| `k8s/layer4-agents.yml` references stale `openai-secret`/`anthropic-secret` | `k8s/layer4-agents.yml` | S3 |
| `apps/web` has ~100 failing tests (MSW mismatches, auth redirects) | `apps/web/` | S3 |
| `SqlTelemetryEmitter.get_events()` raises `NotImplementedError` | Layer 1 telemetry | S4 |
| Layer 3 Neo4j queries not audited for `tenant_id` filters | `services/layer3-knowledge/` | S4 |
| Golden path J1 E2E test not in CI | `tests/` | S4 |
| Layer 2 → Layer 3 pipeline integration test missing | `tests/` | S4 |

---

## Requirements

### R1 — Sprint structure

**R1.1** — The new section must be appended to `ROADMAP.md` under a top-level heading `## 4-Sprint MVP Delivery Roadmap`.

**R1.2** — Each sprint must include:
- Sprint number, focus area, and date range (relative: "Weeks N–N")
- Goal statement (one sentence)
- Backlog: ordered list of work items with owner hint (layer/team) and priority (P0/P1/P2)
- Done criteria: explicit, testable conditions that define sprint completion
- Demo checklist: what to show at the end-of-sprint demo
- Retrospective template (inline, to be filled in after the sprint)

**R1.3** — Sprint cadence: 3 weeks per sprint, 4 sprints = 12 weeks total.

**R1.4** — Sprints must build on each other: Sprint 1 unblocks Sprint 2, Sprint 2 unblocks Sprint 3, Sprint 3 unblocks Sprint 4.

**R1.5** — Work items must be grounded in the confirmed platform gaps listed above. No invented or generic backlog items.

**R1.6** — Each sprint must include a note on flexibility: items that can slip to the next sprint if velocity is lower than expected.

---

### R2 — Sprint 1: Foundations & Test Infrastructure (Weeks 1–3)

**Goal:** Every service test suite runs from the repo root without manual venv activation. CI pipeline is green. New contributors can onboard in one command.

**Backlog (ordered by priority):**
1. [P0] Add `make setup` target — bootstraps all service venvs via `pip install -e ".[dev]"` for each service
2. [P0] Fix `test-layer*` Makefile targets to invoke pytest through service venvs
3. [P0] Scope root `pytest.ini` `addopts` to avoid injecting missing plugins into service runs
4. [P1] Verify `make test-layer1`, `test-layer4`, `test-layer5`, `test-layer6` all pass with zero collection errors
5. [P1] Confirm CI pipeline (`build-deploy.yml`) runs `make setup && make test` end-to-end
6. [P2] Document `make setup && make test` in `CONTRIBUTING.md` as the canonical onboarding flow

**Done criteria:**
- `make setup && make test-layer1 test-layer4 test-layer5 test-layer6` completes with zero collection errors on a clean checkout
- CI pipeline passes on `main`
- `CONTRIBUTING.md` reflects the updated onboarding command

**Demo checklist:**
- [ ] Run `make setup` from scratch on a clean environment — show it completes without errors
- [ ] Run `make test-layer4` — show zero collection errors
- [ ] Show CI pipeline green on latest commit

**Flexibility:** Item 6 (CONTRIBUTING.md update) can slip to Sprint 2 if velocity is constrained.

**Retrospective template:**
```
### Sprint 1 Retrospective

**What went well:**
-

**What didn't go well:**
-

**Blockers encountered:**
-

**Action items for Sprint 2:**
-

**Velocity note:** Estimated X items; completed Y. Slipped items: [list or none]
```

---

### R3 — Sprint 2: Core Fixes & Architecture (Weeks 4–6)

**Goal:** All Layer 4 tests pass. CoreferenceResolver deduplicates entities. Platform-contract is Pydantic v2 clean. No functional no-ops in the critical path.

**Backlog (ordered by priority):**
1. [P0] Fix `HarnessRunRepository.list()` tuple mismatch — unpack tuple in 3 failing tests (Option A)
2. [P0] Fix stale `get_openai_provider` mock patch in `test_analyze_prospect_returns_complete_result`
3. [P0] Fix `BusinessCaseInputData` fixture — add missing required field
4. [P1] Fix `SignalDetectionAgent` 0-signal parsing regression
5. [P1] Resolve 8 Layer 4 collection failures (`testcontainers`, tracing module)
6. [P1] Implement `CoreferenceResolver.resolve()` — name+type deduplication with provenance merge
7. [P2] Migrate `packages/platform-contract` from Pydantic v1 validators to `@field_validator` / `@model_validator`

**Done criteria:**
- `make test-layer4` passes 226/226 harness tests
- `test_analyze_prospect_returns_complete_result`, `test_business_case_handles_all_sections_failing`, `test_detect_signals_returns_complete_result` all pass
- `CoreferenceResolver` unit tests pass: passthrough, exact-dup merge, partial-match no-merge
- Zero Pydantic deprecation warnings in contract test output

**Demo checklist:**
- [ ] Show `make test-layer4` output: 226/226 passing
- [ ] Show `CoreferenceResolver` test run with deduplication cases
- [ ] Show contract tests passing with zero deprecation warnings

**Flexibility:** Item 7 (Pydantic v2 migration) can slip to Sprint 3 if items 1–6 consume the full sprint.

**Retrospective template:**
```
### Sprint 2 Retrospective

**What went well:**
-

**What didn't go well:**
-

**Blockers encountered:**
-

**Action items for Sprint 3:**
-

**Velocity note:** Estimated X items; completed Y. Slipped items: [list or none]
```

---

### R4 — Sprint 3: Feature Expansion & Integration (Weeks 7–9)

**Goal:** Layer 3 gaps closed. k8s manifests are cluster-deployable. Frontend tests pass. Layer 2→3 pipeline verified end-to-end.

**Backlog (ordered by priority):**
1. [P0] Fix `apps/web` failing tests — update MSW handlers to match current API shapes; fix auth redirect fixtures
2. [P1] Implement Layer 3 formula category filter (`formulas.py:579`)
3. [P1] Refactor k8s image references to Kustomize `images:` overlay pattern (remove `services/<name>:*` paths)
4. [P1] Update Layer 4 k8s secret names: `openai-secret` → `llm-provider-secret`; add `TOGETHER_API_KEY` to `k8s/secrets.yml.template`
5. [P2] Verify GHCR base image access (public vs PAT-gated); document in workflow comments
6. [P2] Write Layer 2 → Layer 3 pipeline integration test (tenant scoping + provenance preservation)

**Done criteria:**
- `pnpm --dir apps/web test` passes (all tests green)
- `GET /formulas/variables?category=<x>` returns only matching variables
- All `k8s/base/` and top-level manifests use Kustomize image placeholders
- `k8s/secrets.yml.template` includes `TOGETHER_API_KEY`
- Layer 2 → Layer 3 integration test passes with correct tenant scoping

**Demo checklist:**
- [ ] Show `pnpm --dir apps/web test` passing
- [ ] Show `GET /formulas/variables?category=Financial` returning filtered results
- [ ] Show `kubectl kustomize k8s/base/` rendering valid image references
- [ ] Run Layer 2 → Layer 3 integration test live

**Flexibility:** Item 6 (L2→L3 integration test) can slip to Sprint 4 if frontend test fixes are larger than estimated. Note: frontend tests require Node 22 — coordinate with devcontainer upgrade.

**Retrospective template:**
```
### Sprint 3 Retrospective

**What went well:**
-

**What didn't go well:**
-

**Blockers encountered:**
-

**Action items for Sprint 4:**
-

**Velocity note:** Estimated X items; completed Y. Slipped items: [list or none]
```

---

### R5 — Sprint 4: Polish & Release Preparation (Weeks 10–12)

**Goal:** Platform meets its own production-readiness checklist. Release candidate build produced. UAT completed. Next iteration planned.

**Backlog (ordered by priority):**
1. [P0] Layer 3 tenant isolation audit — enumerate all Cypher queries; verify `tenant_id` filters; add hostile cross-tenant tests
2. [P0] Golden path J1 E2E test — ROI workflow completes end-to-end with live Layer 4 backend; add to CI as smoke test
3. [P1] Resolve `SqlTelemetryEmitter.get_events()` — implement or remove with callers updated
4. [P1] Bug fixing and QA pass — address any issues surfaced during Sprints 1–3
5. [P1] Finalize documentation — update `docs/readiness/current.md`, `CONTRIBUTING.md`, `k8s/README.md`
6. [P2] Produce release candidate build — tag `v1.0.0-rc.1`, verify Docker images build and push to GHCR
7. [P2] User acceptance testing — run golden path J1 with a real tenant account; capture feedback
8. [P2] Plan next iteration — document top 3 items for Sprint 5 based on UAT feedback

**Done criteria:**
- All Layer 3 Neo4j queries verified to filter by `tenant_id`; hostile cross-tenant tests added and passing
- Golden path J1 ROI workflow completes in CI smoke test
- `SqlTelemetryEmitter.get_events()` implemented or removed (no `NotImplementedError` in production path)
- `docs/readiness/current.md` updated to reflect final state
- Release candidate tag `v1.0.0-rc.1` exists with passing CI
- UAT sign-off documented

**Demo checklist:**
- [ ] Show hostile cross-tenant test failing before fix, passing after
- [ ] Show golden path J1 smoke test passing in CI
- [ ] Show `v1.0.0-rc.1` tag and passing CI pipeline
- [ ] Present UAT feedback summary and Sprint 5 candidate items

**Flexibility:** Items 7–8 (UAT and next-iteration planning) can extend into a brief post-sprint wrap-up if the release candidate is delayed.

**Retrospective template:**
```
### Sprint 4 Retrospective

**What went well:**
-

**What didn't go well:**
-

**Blockers encountered:**
-

**Next iteration candidates (Sprint 5):**
1.
2.
3.

**Velocity note:** Estimated X items; completed Y. Slipped items: [list or none]
```

---

## Acceptance Criteria

| ID | Criterion |
|---|---|
| AC-01 | `ROADMAP.md` contains a new `## 4-Sprint MVP Delivery Roadmap` section appended at the end |
| AC-02 | Each sprint section includes: goal, ordered backlog with priorities, done criteria, demo checklist, retrospective template |
| AC-03 | All backlog items map to confirmed platform gaps (no invented items) |
| AC-04 | Sprint cadence is 3 weeks × 4 sprints = 12 weeks total |
| AC-05 | Sprint 1 backlog items are prerequisites for Sprint 2 (test infra unblocks functional fixes) |
| AC-06 | Sprint 2 backlog items are prerequisites for Sprint 3 (core fixes unblock integration work) |
| AC-07 | Sprint 3 backlog items are prerequisites for Sprint 4 (integration unblocks release prep) |
| AC-08 | Each sprint includes a flexibility note identifying items that can slip |
| AC-09 | Retrospective template is consistent across all 4 sprints |
| AC-10 | The new section does not modify any existing content in `ROADMAP.md` |

---

## Implementation Approach

1. **Read the tail of `ROADMAP.md`** — confirm the last line and identify the exact append point (after the final `---` separator).
2. **Append the `## 4-Sprint MVP Delivery Roadmap` section** — write the full section as specified in R2–R5 above, including all sprint subsections, backlogs, done criteria, demo checklists, and retrospective templates.
3. **Verify structure** — view the appended section to confirm all 4 sprints are present, headings are correct, and no existing content was modified.
4. **Cross-check backlog items against confirmed gaps** — verify every backlog item in the appended section maps to a row in the Platform State table above.
5. **Confirm `ROADMAP.md` is valid Markdown** — no broken tables, unclosed code fences, or heading level errors.

