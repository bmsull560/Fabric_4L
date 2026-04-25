# Platform Contract Ratification Memo

_For circulation and sign-off. Scope: foundational architectural commitments for Fabric 4L._

***

## The Reframe

This is not a "missing contract" problem — it is a **contract alignment** problem. Two overlapping truths are in play:

1. The earlier canonical vision — root `contract.md`, `DEPRECATIONS.md`, `examples/canonical/*` (TypeScript), the ESLint plugin, the `@tool` runtime guard, and `contract-compliance.yml`.
2. The newer package-based work — `packages/platform-contract/*`, Python canonical implementations, broader Python lint, updated contributor guidance.

The real question is not _which files to keep_ but **which architectural choices become the ratified standard**, and **how the contract expresses the gap between today's reality and tomorrow's ambition** without collapsing into drift.

***

## Step 1 — What Shipped Code Has Already Decided

Four decisions are baked into production. Reversing them is expensive; ratifying them is free.

| # | Decision                                                                                                                                                                                                                      | Evidence                                                                                                                  | External Validation                                                                                                                                                             |
| - | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1 | **Explicit context via** **`Depends()`** **+** **`RequestContext`** — context is a dependency, not ambient state; every entry point (HTTP, WebSocket, background task, CLI) declares its context needs at the signature level | 47+ function signatures; FastAPI DI graph; `get_current_context()` read through ContextVar but always accessed explicitly | Industry consensus (incl. MCP Python SDK) is actively migrating _away_ from ambient ContextVar for domain logic due to hidden dependencies, memory-leak risk, and untestability |
| 2 | **Single in-app** **`GovernanceMiddleware`** **with mandatory phase hooks; phase decomposition realized at the edge gateway**                                                                                                 | `shared/identity/middleware.py` = 666 lines; gateway already handles auth/rate-limit/IP-filter at the perimeter           | See §Step 1a below — this is the one ratification that required reconciliation with external research                                                                           |
| 3 | **PostgreSQL RLS via** **`SET LOCAL`**                                                                                                                                                                                        | RLS working in L4/L5 today; zero pool-routing code exists                                                                 | Named "mathematically necessary" for shared-schema multi-tenancy at our scale                                                                                                   |
| 4 | **Runtime** **`@tool`** **decorator enforcement**, with schema-first envelopes layered on top (defense in depth)                                                                                                              | `tool_contract.py` = 351 lines of runtime guards, AST-checked in CI                                                       | Runtime guards + pre-execution schema validation is the prevailing pattern for agentic systems; the two layers are complementary, not competing                                 |

**Implication:** every day the spec stays aspirational, new code is written against the real (divergent) pattern and the gap widens.

### Step 1a — Middleware Realization Model (Ratified)

Fabric 4L **retains the 8-phase governance pipeline as the logical architecture**, but realizes it as a **distributed control plane**: gateway-native phases (auth, rate-limit, IP filter, transformation pre-processing) execute at the edge, while residual phases (domain execution, observability, audit) execute in-app through canonical `GovernanceMiddleware`.

This is not a rejection of the 8-phase model; it is its production realization through edge distribution plus in-app phase seams.

`GovernanceMiddleware` **MUST** expose internal phase hooks — `_pre_auth`, `_post_auth`, `_pre_rls`, `_post_rls` — to preserve decomposability, enable focused testing, and maintain a reversible path toward fuller phase decomposition if operational scale or control complexity requires it. Hooks are internal by design: any second consumer requires review-gate approval, and this policy is enforced to prevent the well-known failure mode where internal hooks silently ossify into a de facto public API.

**Canonical consequence:** no new in-app middleware chain may be introduced for concerns already assigned to the logical pipeline without explicitly declaring whether that concern belongs at the edge, in `GovernanceMiddleware`, or in a phase hook extension point.

***

## Step 2 — Decisions Genuinely Open

Only three decisions are not yet settled by shipped code at scale.

### A. Frontend navigation model

\~56 navigation instances. The real question is product-shaped: is this a wizard-heavy platform (Value Pilot 7-step, Value Studio 6-stage) or a CRUD app with a few wizards?
→ **Hybrid: Finite State Machine mandatory for named wizard surfaces; wouter + Zustand for everything else.** FSM is the right tool for multi-step conditional flows (guarded transitions, impossible-state elimination, resumable state); it is overkill for dashboards and CRUD pages.

### B. Enforcement layer for tool/agent boundaries

Runtime guard (`@tool`) and schema-first (Pydantic envelopes) defend different layers.
→ **Both.** Schema defines the shape; runtime enforces the behavior; CI checks both. The Pydantic envelopes must match the `ToolResult<T>` shape exactly — unified, not parallel.

### C. Python canonical reference location

Today there are zero Python reference implementations in `examples/canonical/` (all TS); `packages/platform-contract/src/python/canonical/` fills a real gap.
→ **Fold into `examples/canonical/python/`.** Two canonical locations is strictly worse than either alone.

***

## Step 3 — The Layered Canon

Should the contract describe what CI can block today, or what the architecture aspires to become? Both — but they must live in different places with different authority.

| Layer                         | Purpose                                           | Authority                    | Physical Home                                                    |
| ----------------------------- | ------------------------------------------------- | ---------------------------- | ---------------------------------------------------------------- |
| **Enforced Canon**            | What CI blocks on every PR; must match production | Merge-blocking               | `contract.md` (root) + `examples/canonical/{typescript,python}/` |
| **Target Architecture**       | Future-state patterns with owners and milestones  | Advisory, reviewed quarterly | `examples/experimental/` — cited by contract, not merge-blocking |
| **Reference Implementations** | One authoritative example per language            | Cited by contract            | `examples/canonical/`                                            |
| **Deprecation Register**      | Explicit deadlines + owning teams                 | Tracked                      | `DEPRECATIONS.md`                                                |

### Sunset Rule (Critical Discipline)

**Target Architecture items without an active migration milestone within 12 months are automatically demoted to "rejected alternatives" and removed from `contract.md`.**

Without this rule, Target Architecture degrades into the exact drift problem the layered model was designed to solve: dormant aspirations cited by contributors in code review to justify non-canonical patterns ("but the target architecture says…"). The sunset rule forces each Target entry to earn its place every year.

***

## Step 4 — The Path

**Hybrid, weighted toward ratification.** \~2 weeks of work.

| Path                     | Cost                          | Verdict                                                                                                            |
| ------------------------ | ----------------------------- | ------------------------------------------------------------------------------------------------------------------ |
| Ratify reality entirely  | \~1 day                       | Loses the north star                                                                                               |
| Pursue the spec entirely | 6–12 weeks across every layer | Team burns cycles on refactors instead of product                                                                  |
| **Hybrid (recommended)** | **\~2 weeks**                 | **Ratify context + middleware + DB +** **`@tool`** **as-is; pursue wizard FSM + schema-first envelope as targets** |

Decisions 1–4 are sunk; rewriting them buys purity, not product value. The wizard FSM is the one place where aspirational patterns demonstrably help users — guarded transitions matter in a 7-step flow in a way they do not on a dashboard, and 56 instances is tractable. Schema-first + runtime guard is nearly free: the runtime layer already exists; Pydantic envelopes just add a boundary check. The cost is aligning shapes, not building machinery.

***

## Step 5 — Consolidation (Executable in One PR)

With the meta-decision resolved, every file question answers itself.

**Delete:**

* `packages/platform-contract/CONTRACT.md` → root `contract.md` is canonical
* `docs/platform-contract/DEPRECATION_MAP.md` → root `DEPRECATIONS.md` is canonical
* `.github/workflows/platform-contract-gate.yml` → fold into `contract-compliance.yml`

**Keep and relocate:**

* Python canonical implementations → move to `examples/canonical/python/` and align with the runtime `@tool` decorator so they are correct references, not parallel ones
* `platform_contract_lint.py` → rename to `check_platform_contracts.py`, wire into existing CI alongside `check_tool_contracts.py` (covers DB session, context, and raw-dict patterns the tool check doesn't)
* TypeScript type definitions in `packages/platform-contract/src/typescript/` → keep as the packageable type surface; have `examples/canonical/` TS files import from it

**Rewrite:**

* **`contract.md`** — correct the four aspirational sections to match shipped reality; add §2.1 service-layer justification for explicit context; document the middleware realization model (§Step 1a above) including the edge/in-app phase allocation; move residual ambitions into the Target Architecture section with owners and 12-month milestones
* **`DEPRECATIONS.md`** — remove "eliminate `tenant_id` parameters"; retain wizard-surface navigation migration and the 27 throwing tools
* **`AGENTS.md` + `Makefile`** — point to the single authoritative contract and consolidated lint entry point

**Unify:**

* One merge-blocking CI gate; multiple checks beneath it (ESLint plugin, tool AST check, new platform lint, canonical examples test)

***

## Sequencing

1. Ratify the four shipped patterns in `contract.md` — unlocks everything else
2. Document the middleware realization model and phase hooks — same PR
3. Split contract into Enforced Canon vs Target Architecture; scaffold `examples/experimental/`; adopt sunset rule — same PR
4. Consolidate artifacts per Step 5
5. Scope wizard FSM migration to named surfaces only — design doc, then execute across the \~20–30 genuinely wizard-shaped instances among the 56
6. Align schema-first envelopes with `@tool` runtime shape

***

## Sign-Off Lines

| # | Ratification                                                                                                            | Owner | Sign-Off | Date |
| - | ----------------------------------------------------------------------------------------------------------------------- | ----- | -------- | ---- |
| 1 | Explicit context via `Depends()` + `RequestContext` as service-layer boundary guarantee                                 | ​     | ​        | ​    |
| 2 | Single in-app `GovernanceMiddleware` with mandatory internal phase hooks; phase decomposition realized via edge gateway | ​     | ​        | ​    |
| 3 | PostgreSQL RLS via `SET LOCAL` as canonical multi-tenant isolation                                                      | ​     | ​        | ​    |
| 4 | Runtime `@tool` decorator enforcement with schema-first envelopes layered on top                                        | ​     | ​        | ​    |
| 5 | Hybrid frontend: FSM mandatory for named wizard surfaces, wouter + Zustand elsewhere                                    | ​     | ​        | ​    |

***

## The Bottom Line

**Ratify reality for context, middleware, DB, and tool runtime. Pursue FSM for wizards only. Adopt schema-first envelopes on top of the existing runtime guard. Decide phase hooks explicitly rather than punt. Express the gap between today and tomorrow as a layered canon with a sunset rule, not as a single document pretending to be both.**

The cheapest, highest-integrity next move is sign-off on the five lines above. Every remaining question — which files to delete, which lint rules to promote, which examples to keep — flows deterministically from this single commitment.
