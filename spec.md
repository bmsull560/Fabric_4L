# LLM-Powered Agent Rewrite

## Status
Draft — awaiting user confirmation

---

## Problem Statement

The Layer 4 agent system has the structural scaffolding for LLM-powered reasoning (state machines, tool registry, harness governance, provider adapter interfaces) but the actual LLM integration is incomplete:

- `BaseWorkflow._execute_llm` returns `{"status": "llm_not_implemented"}` — stub
- `ROICalculatorWorkflow` has no LLM step — purely formula-based
- `WhitespaceAnalysisWorkflow` uses LLM only for need extraction (one step), hardcoded to OpenAI
- `BusinessCaseGeneratorWorkflow` calls LLM for section generation only, hardcoded to OpenAI
- `SignalDetectionAgent` delegates to Layer 2 with no LLM reasoning step
- `NarrativeBuilderService` is template-based, not LLM-powered
- Only `OpenAIProvider` is implemented; no `TogetherAIProvider` exists
- All LLM calls bypass the Harness — no traceability, checkpointing, or governance
- `AIModel.tsx` frontend page uses entirely hardcoded mock data

The goal is to replace all of the above with a governed, provider-agnostic, full agentic reasoning loop using Together.ai as the primary LLM provider, running through the Harness.

---

## Architecture Overview

```
User / API trigger
  → HarnessRun created (SqlHarnessRegistry)
  → Harness state machine advances
  → L4 Agent invoked (ROI / Whitespace / BusinessCase / SignalDetection)
  → Agent calls GovernedLLMClient
      → GovernedLLMClient wraps TogetherAIProvider (primary)
      → Falls back to OpenAIProvider if configured
  → Tool calls registered and traced
  → Structured outputs checkpointed
  → Claims routed to L5 validation (LiveL5Validator)
  → Human gate if needed
  → Output published after validation/approval
```

---

## Requirements

### 0. Prompt Registry

**Files:**
- `services/layer4-agents/prompts/` — versioned prompt files per workflow
- `services/layer4-agents/src/harness/prompt_registry.py` — registry abstraction

**Directory structure:**
```
services/layer4-agents/prompts/
  roi_calculator/
    v1/
      system.md
      hypothesis_generation.md
      evidence_reasoning.md
      narrative_generation.md
      output_schema.json
  whitespace_analysis/
    v1/
      system.md
      extraction.md
      gap_analysis.md
      hypothesis_generation.md
      output_schema.json
  business_case/
    v1/
      system.md
      gather_inputs.md
      generate_sections.md
      validate_claims.md
      output_schema.json
  signal_detection/
    v1/
      system.md
      classification.md
      hypothesis_generation.md
      narrative.md
      output_schema.json
  narrative_builder/
    v1/
      system.md
      executive_summary.md
      value_narrative.md
      risk_narrative.md
      output_schema.json
```

**Prompt metadata** (frontmatter in each `.md` file):
```yaml
prompt_id: roi_calculator.hypothesis_generation
version: v1
workflow_type: roi_calculator_generation
model_task: reasoning          # reasoning | extraction | narrative
requires_json: true
output_schema: RoiHypothesisOutput
```

**`PromptRegistry` interface:**
```python
class PromptRegistry:
    def load(self, prompt_id: str, version: str = "v1") -> LoadedPrompt
    def list_prompts(self, workflow_type: str) -> list[PromptMetadata]
```

**Runtime use:**
```python
prompt = prompt_registry.load("roi_calculator.hypothesis_generation")
result = governed_llm.extract_structured(
    request=CompletionRequest(system=prompt.system, user=prompt.render(context)),
    schema=prompt.output_schema,
    run_context=run_context,
)
```

No prompt literals inside workflow Python files. All prompts loaded through `PromptRegistry`.

---

### 1. Together.ai Provider Adapter

**File:** `services/layer4-agents/src/services/together_provider.py`

Implement `TogetherAIProvider` using the OpenAI-compatible API:
- Base URL: `https://api.together.ai/v1`
- Auth: `TOGETHER_API_KEY` environment variable
- Implement all three adapter protocols: `CompletionAdapter`, `ToolCallingAdapter`, `StructuredOutputAdapter`
- Use `openai.AsyncOpenAI(api_key=..., base_url="https://api.together.ai/v1")` — drop-in compatible
- Default model: `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8` (configurable via `TOGETHER_DEFAULT_MODEL`; actual per-workflow model selection is owned by `harness.runtime.yaml` — see §Model Configuration)
- Normalize Together error shapes to `AdapterError` (match on HTTP status: 400, 401, 404, 429, 500, 503)
- Handle Together-specific response quirks: namespaced model IDs, `reasoning` field on assistant messages, richer `usage` fields
- Implement retry with exponential backoff for 429 and 503

**Environment variables to add to `config/settings.py`:**
```
TOGETHER_API_KEY          # required when provider=together
TOGETHER_DEFAULT_MODEL    # default: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
TOGETHER_BASE_URL         # default: https://api.together.ai/v1
LLM_PROVIDER              # "together" | "openai" — default: "together"
```

**`.env.example` update:** add all four variables with safe defaults and comments.

---

### 2. GovernedLLMClient

**File:** `services/layer4-agents/src/services/governed_llm_client.py`

A thin wrapper that:
- Accepts a `HarnessRun` context (run_id, tenant_id, workflow_type)
- Selects provider based on `LLM_PROVIDER` env var (Together primary, OpenAI fallback)
- Emits a `TraceEvent` to the Harness registry before and after each LLM call (type: `llm_call_start` / `llm_call_complete`)
- Records token usage and cost via `LLMCostCalculator`
- Records metrics via `get_metrics()`
- Enforces budget guardrails via `get_llm_budget_guardrails()`
- Raises `LLMBudgetExceededError` if budget exceeded (agents must handle gracefully)
- Never exposes raw provider errors to callers — always wraps in `AdapterError`

Interface:
```python
class GovernedLLMClient:
    async def complete(self, request: CompletionRequest, *, run_context: HarnessRunContext) -> CompletionResult | AdapterError
    async def complete_with_tools(self, request: CompletionRequest, tools: list[dict], *, run_context: HarnessRunContext) -> CompletionResult | AdapterError
    async def extract_structured(self, request: CompletionRequest, *, schema: dict, run_context: HarnessRunContext) -> dict | AdapterError
```

---

### 3. ROI Calculator — LLM Reasoning Step

**File:** `services/layer4-agents/src/workflows/roi_calculator.py`

Add `_execute_llm` override. The LLM step runs after formula calculation and before output publication. It:

1. **Receives:** formula outputs (calculated ROI, value drivers, assumptions, benchmarks)
2. **Produces (structured JSON):**
   - `hypothesis`: one-sentence value hypothesis for this account
   - `confidence`: float 0–1 with rationale
   - `key_drivers`: list of top 3 value drivers with LLM-reasoned explanation
   - `risks`: list of identified risks from the data
   - `narrative_summary`: 2–3 sentence executive summary
   - `evidence_refs`: list of source references used in reasoning
3. **Prompt design:** system prompt establishes role as "Value Engineering Analyst"; user prompt injects formula outputs as structured context; output is strict JSON via `response_format: json_object`
4. **Fallback:** if LLM call fails or budget exceeded, return deterministic summary from formula outputs (no crash)
5. **Checkpoint:** output stored in Harness checkpoint at `QUANTIFY_IMPACT` state

---

### 4. Whitespace Analysis — Full Agentic Loop

**File:** `services/layer4-agents/src/workflows/whitespace.py`

Replace hardcoded `get_openai_provider` calls with `GovernedLLMClient`. Extend the reasoning loop:

1. **`_execute_analyze_prospect`** (existing, refactor): use `GovernedLLMClient` instead of `get_openai_provider`; add evidence refs to output
2. **`_execute_identify_gaps`** (existing, extend): add LLM reasoning step after semantic search — LLM synthesizes gap analysis across all needs, produces ranked gap list with confidence scores and evidence citations
3. **`_execute_score_opportunity`** (existing, extend): LLM produces a structured opportunity narrative alongside the numeric score; cites specific evidence from gap analysis
4. **New `_execute_generate_hypotheses`** step: LLM generates 3–5 value hypotheses from the full gap analysis, each with:
   - `hypothesis_text`
   - `supporting_evidence`: list of refs
   - `confidence`: float
   - `recommended_action`
5. All LLM outputs use `GovernedLLMClient` with Harness run context

---

### 5. Business Case Generator — Full Agentic Loop

**File:** `services/layer4-agents/src/workflows/business_case.py`

Replace `_execute_llm` stub and extend:

1. **`_execute_gather_inputs`**: LLM synthesizes inputs from multiple sources (CRM, knowledge graph, ROI outputs, whitespace analysis) into a structured brief — not just data assembly
2. **`_execute_generate_sections`** (existing, refactor): use `GovernedLLMClient`; each section prompt includes evidence refs; output includes `evidence_refs` per section
3. **New `_execute_validate_claims`**: extract all factual claims from generated sections; route each claim to `LiveL5Validator` via Harness; mark sections with validation status
4. **New `_execute_human_review_gate`**: if any claims are `NEEDS_REVIEW` or `INSUFFICIENT_EVIDENCE`, create a `HumanGate` via Harness registry; block publication until gate is decided
5. All LLM calls through `GovernedLLMClient`

---

### 6. Signal Detection Agent — LLM Reasoning Step

**File:** `services/layer4-agents/src/agents/signal_detection.py`

Add LLM reasoning layer on top of Layer 2 extraction:

1. **Receive** Layer 2 extraction outputs (entities, relationships, signals)
2. **LLM step — signal classification**: classify each signal as `pain`, `initiative`, `budget_signal`, `stakeholder_signal`, `risk`, or `opportunity`; assign confidence score
3. **LLM step — hypothesis generation**: for each high-confidence signal cluster, generate a value hypothesis with evidence refs
4. **LLM step — narrative**: produce a 1-paragraph signal summary for the account
5. All steps through `GovernedLLMClient` with Harness run context
6. Fallback: if LLM unavailable, return raw Layer 2 outputs with `llm_enrichment: false` flag

---

### 7. Degraded Output Contract

All agents must return a typed `AgentResult` wrapper. Add to `services/layer4-agents/src/agents/base.py`:

```python
@dataclass
class AgentResult(Generic[T]):
    status: Literal["completed", "degraded", "failed"]
    llm_enrichment: bool
    human_review_required: bool
    customer_facing_allowed: bool
    data: T
    degradation_reason: Literal["llm_unavailable", "validator_unavailable", "tool_unavailable"] | None = None
    skipped_sections: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
```

**Rules:**
- `llm_enrichment=False` → `customer_facing_allowed=False` always
- `llm_enrichment=False` → `human_review_required=True` always
- Degraded output may be checkpointed and used for internal workflow continuity
- Degraded output must not be published as customer-facing output without explicit human gate approval
- The Harness handles retries, telemetry, and routing around degraded results

**Fallback behavior per agent:**
- All agents: return deterministic partial state (tool outputs, source inventory, validated facts) with `llm_enrichment=False`
- Skipped sections listed explicitly in `skipped_sections`
- Warning message: `"LLM was unavailable. No agentic reasoning or narrative synthesis was performed."`

---

### 8. Narrative Builder Service — LLM Rewrite

**File:** `services/layer4-agents/src/services/narrative_builder_service.py`

Replace template-based assembly with LLM generation:

1. Accept structured inputs: ROI outputs, whitespace analysis, business case sections, signal summary
2. LLM produces: executive summary, value narrative, risk narrative, oversight summary
3. Each output section includes `evidence_refs` and `confidence`
4. Template fallback retained for when LLM is unavailable — returns `AgentResult` with `llm_enrichment=False`
5. Uses `GovernedLLMClient` — requires a `HarnessRunContext` to be passed in
6. Prompts loaded from `prompts/narrative_builder/v1/`

---

### 9. Provider Selection and Configuration

**File:** `services/layer4-agents/src/services/llm_provider.py`

Add factory function:
```python
def get_llm_provider(config=None) -> CompletionAdapter & ToolCallingAdapter & StructuredOutputAdapter:
    provider = os.getenv("LLM_PROVIDER", "together")
    if provider == "together":
        return TogetherAIProvider()
    elif provider == "openai":
        return get_openai_provider(config)
    raise ValueError(f"Unknown LLM_PROVIDER: {provider}")
```

Replace all direct `get_openai_provider()` calls in workflows with `get_llm_provider()`.

---

### 10. Model Configuration in harness.runtime.yaml

Add an `llm` top-level section to `services/layer4-agents/config/harness.runtime.yaml`:

```yaml
llm:
  provider: together
  default_model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8

  # Task-type routing — agents declare a task type, not a model literal
  task_models:
    reasoning:
      model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
      fallback_model: meta-llama/Llama-3.3-70B-Instruct-Turbo
      temperature: 0.2
      max_tokens: 6000
    extraction:
      model: meta-llama/Llama-4-Scout-17B-16E-Instruct
      fallback_model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
      temperature: 0.0
      max_tokens: 3000
    evidence_reasoning:
      model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
      fallback_model: meta-llama/Llama-3.3-70B-Instruct-Turbo
      temperature: 0.1
      max_tokens: 5000
    narrative:
      model: meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8
      temperature: 0.3
      max_tokens: 5000
```

**Model selection rule:** agents declare a `model_task` (from prompt metadata), not a model literal. `GovernedLLMClient` resolves the model from `harness.runtime.yaml` at call time. No model names in agent Python code.

**`generate_harness_docs.py`** check: add validation that `harness.runtime.yaml` contains a top-level `llm` key with `provider` and `task_models`.

---

### 11. LLM Cost Calculator — Together.ai Pricing

**File:** `services/layer4-agents/src/metrics/llm_cost_calculator.py`

Add Together.ai model pricing entries for:
- `meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8`
- `meta-llama/Llama-4-Scout-17B-16E-Instruct`
- `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo`
- `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo`

Provider key: `"together"`.

---

### 12. Frontend — AIModel.tsx Status Wire-up

**File:** `apps/web/src/workflow/pages/AIModel.tsx`

Connect to real Harness/L4 run status. Do **not** rewrite the UX or hypothesis editor.

Add:
- `useHarnessRuns({ workflow_type: 'roi_calculator_generation' | 'business_case_generation', limit: 5 })` to fetch recent runs for the current account
- Display run status badge: `QUEUED` / `RUNNING` / `WAITING_FOR_VALIDATION` / `HUMAN_REVIEW_REQUIRED` / `FAILED` / `CANCELLED` / `COMPLETE`
- Map `HarnessRun.current_state` to human-readable status using `HARNESS_STATE_LABELS` constant
- Show last-run timestamp and workflow type
- Poll at `POLL_INTERVALS.workflows` (5 s) for non-terminal states
- Show error message if run is in `FAILED` state
- Keep all existing mock hypothesis/model UI unchanged — only add the status panel

Pattern: follow `useHarnessRuns` → `harnessApi.listRuns` → `apiClient.get('l4', ...)` established in the Harness integration.

---

### 13. Documentation Updates

- `docs/architecture/harness-agent-integration.md`: add section on `GovernedLLMClient` and Together.ai integration
- `services/layer4-agents/docs/harness-runbook.md`: add Together.ai env vars, model selection, cost monitoring
- `.env.example`: add `TOGETHER_API_KEY`, `TOGETHER_DEFAULT_MODEL`, `TOGETHER_BASE_URL`, `LLM_PROVIDER`

---

## Acceptance Criteria

### Provider
- [ ] `TogetherAIProvider` implements all three adapter protocols
- [ ] `TOGETHER_API_KEY` read from env, never hardcoded
- [ ] `LLM_PROVIDER=together` routes all calls to Together.ai
- [ ] `LLM_PROVIDER=openai` routes to existing OpenAI provider (backward-compatible)
- [ ] Together error shapes normalized to `AdapterError`
- [ ] Retry on 429/503 with exponential backoff

### GovernedLLMClient
- [ ] Every LLM call emits `llm_call_start` and `llm_call_complete` trace events to Harness
- [ ] Token usage and cost recorded per call
- [ ] Budget guardrails enforced
- [ ] No raw provider errors exposed to callers

### Agents
- [ ] `ROICalculatorWorkflow._execute_llm` produces structured hypothesis + narrative
- [ ] `WhitespaceAnalysisWorkflow` uses `GovernedLLMClient`; adds hypothesis generation step
- [ ] `BusinessCaseGeneratorWorkflow` uses `GovernedLLMClient`; adds claim validation + human gate
- [ ] `SignalDetectionAgent` adds LLM classification + hypothesis + narrative steps
- [ ] `NarrativeBuilderService` uses LLM with template fallback
- [ ] All agents fall back gracefully when LLM is unavailable (no crash, degraded output flagged)
- [ ] All LLM outputs include `evidence_refs` and `confidence` fields

### Harness integration
- [ ] All production LLM calls carry a `HarnessRunContext` (run_id, tenant_id)
- [ ] LLM call trace events appear in `harness_trace_events` table
- [ ] Claims from business case routed to L5 validation via Harness
- [ ] Human gate created when claims need review

### Frontend
- [ ] `AIModel.tsx` shows real Harness run status for relevant workflow types
- [ ] Status polls for non-terminal states
- [ ] Existing mock hypothesis UI unchanged

### Prompt Registry
- [ ] `PromptRegistry.load()` resolves prompt files from disk by `prompt_id` and `version`
- [ ] All workflow prompt directories exist with `system.md` and `output_schema.json`
- [ ] No prompt literals inside workflow Python files

### Degraded Output
- [ ] All agents return `AgentResult` wrapper
- [ ] `llm_enrichment=False` always sets `customer_facing_allowed=False` and `human_review_required=True`
- [ ] Degraded results are checkpointed and traceable in Harness

### Model Configuration
- [ ] `harness.runtime.yaml` contains `llm.provider` and `llm.task_models`
- [ ] No model name literals in agent Python code — all resolved from config
- [ ] `generate_harness_docs.py --check` validates `llm` key presence

### Tests
- [ ] `TogetherAIProvider` unit tests: success path, 429 retry, 503 retry, auth error normalization
- [ ] `GovernedLLMClient` unit tests: trace event emission, budget enforcement, model resolution from config
- [ ] `PromptRegistry` unit tests: load by id/version, missing prompt raises clear error
- [ ] Each workflow's LLM step has a unit test with mocked `GovernedLLMClient`
- [ ] `AgentResult` degraded output: unit test that `llm_enrichment=False` enforces `customer_facing_allowed=False`
- [ ] `AIModel.tsx` status panel has a render test

---

## Implementation Steps

1. **`PromptRegistry` + prompt files** — create `src/harness/prompt_registry.py`; scaffold all prompt directories and seed initial `system.md` + `output_schema.json` per workflow
2. **`AgentResult` degraded output contract** — add to `src/agents/base.py`
3. **`TogetherAIProvider`** — implement adapter in `src/services/together_provider.py`; add env vars to `settings.py` and `.env.example`; add pricing to `LLMCostCalculator`
4. **`harness.runtime.yaml` LLM section** — add `llm.provider`, `llm.task_models`; update `generate_harness_docs.py` check
5. **`GovernedLLMClient`** — implement in `src/services/governed_llm_client.py`; wire to Harness trace events; resolve model from `harness.runtime.yaml` task type
6. **Provider factory** — add `get_llm_provider()` to `llm_provider.py`; replace `get_openai_provider()` calls in all workflows
7. **ROI Calculator LLM step** — implement `_execute_llm` override using `GovernedLLMClient` + `PromptRegistry`
8. **Whitespace Analysis refactor** — replace provider calls; add hypothesis generation step
9. **Business Case refactor** — replace provider calls; add claim validation + human gate steps
10. **Signal Detection LLM layer** — add classification, hypothesis, narrative steps
11. **Narrative Builder rewrite** — replace template assembly with LLM generation + fallback
12. **Frontend AIModel.tsx** — add status panel wired to `useHarnessRuns`
13. **Tests** — unit tests for provider, client, prompt registry, each workflow LLM step, frontend status panel
14. **Documentation** — update arch doc, runbook, `.env.example`

---

## Out of Scope

- Full hypothesis editor rewrite in `AIModel.tsx`
- Full value model editor replacement
- Full evidence matching UI
- Full formula/calculator integration UI
- Full business case publishing flow UI
- Anthropic provider implementation
- Together.ai batch API or fine-tuning
- Streaming SSE to frontend (status polling is sufficient for this phase)

---

## [ARCHIVED] Previous Spec

The content below is the previous Harness UI production signoff spec, preserved for reference.

## Status
Confirmed — ready for implementation

---

## Current State

All harness integration work is complete and committed on `feat/harness-live-l5-validator`. The following was delivered:

- `services/layer4-agents/src/harness/api_models.py` — Pydantic request/response models
- `services/layer4-agents/src/api/routes/harness.py` — 12 FastAPI endpoints
- `services/layer4-agents/src/api/routers.py` — harness router registered at `/v1`
- `apps/web/src/api/harness.ts` — TypeScript types and `harnessApi` client
- `apps/web/src/hooks/useHarness.ts` — TanStack Query hooks with polling
- `apps/web/src/hooks/queryKeys.ts` — `QK.harness.*` key group
- `apps/web/src/components/HarnessRunDetail.tsx` — Sheet with state progress, gates, checkpoints
- `apps/web/src/pages/AgentWorkflows.tsx` — "Harness Runs" tab, updated KPI card
- `services/layer4-agents/config/harness.runtime.yaml` — per-workflow-type runtime config
- `services/layer4-agents/config/harness.service.yaml` — service deployment config
- `docs/architecture/harness-agent-integration.md` — architecture doc with API reference
- `services/layer4-agents/docs/harness-runbook.md` — operator runbook
- `scripts/generate_harness_docs.py` — validation script (`--check` / `--fix` modes)
- `Makefile` — `docs-harness` target wired into `make verify`

Two bugs were found and fixed during regression testing:

1. **`useHarness.ts`**: `POLL_INTERVALS` was imported from `./useApiShared` (does not export it). Fixed to import from `./usePolling`.
2. **`AgentWorkflows.tsx`**: Harness `DataTable` passed `headers={...}` instead of `columns={...}`. Fixed to `columns={...}`.

Two regression test files were added:

- `apps/web/src/hooks/useHarness.test.ts` — 15 tests (import smoke, layer key, path, polling guards, mutation call signatures)
- `apps/web/src/pages/AgentWorkflows.harness.test.tsx` — 8 tests (tab render, empty/loading/error states, View opens sheet, Cancel calls transition mutation)

---

## Problem Statement

TypeScript verification (`pnpm tsc --noEmit`) could not be confirmed in the session environment (Node 20, project requires ≥22). The `tsc` binary was run directly from `node_modules` and produced **zero harness-related errors** — all errors are pre-existing in unrelated files (`useValueSignals.ts`, `TargetsAdmin.*`, `valueSignal.ts`). Production signoff requires confirming this in a proper Node ≥22 environment and fixing any harness-specific errors that surface.

---

## Requirements

### 1. TypeScript Verification

**Accepted approach (confirmed):** TypeScript verification is complete via `node_modules/.bin/tsc --noEmit` run under Node 20. This is accepted because:

1. `node_modules/.bin/tsc --noEmit` ran successfully
2. It produced zero harness-related errors
3. Harness-specific unit and page tests passed
4. The prior blocker was inability to run TypeScript at all — that blocker is resolved
5. Node 20 vs project-required Node ≥22 is an environment caveat, not a harness implementation failure

**Final report must state:**
- TypeScript: passed via `node_modules/.bin/tsc --noEmit`
- Harness-related TypeScript errors: 0
- Environment caveat: run under Node 20; project package policy expects Node ≥22
- Recommended CI confirmation: re-run under Node ≥22 in normal CI/dev environment

**If a Node ≥22 run later reveals harness-specific errors**, the fix scope is:

- Harness files directly changed or added: `harness.ts`, `useHarness.ts`, `HarnessRunDetail.tsx`, `AgentWorkflows.tsx`, harness tests
- Shared types/utilities **only** where harness integration exposed or broke an existing contract: query key types, `DataTable` prop typing, API client layer/path typing, shared polling constants/types, shared test fixtures used by harness tests
- Do not broaden into unrelated app-wide TypeScript cleanup
- Do not revert harness changes unless errors reveal a fundamental integration mistake that cannot be fixed surgically
- If shared types are touched, the final report must explain: which harness usage required the change, why it is backward-compatible, which existing tests confirm no regression

### 2. Bug Fix Preservation

The following fixes must remain intact:

| File | Fix |
|---|---|
| `apps/web/src/hooks/useHarness.ts` | `POLL_INTERVALS` imported from `./usePolling`, not `./useApiShared` |
| `apps/web/src/pages/AgentWorkflows.tsx` | Harness `DataTable` uses `columns={...}`, not `headers={...}` |

### 3. Test Preservation

The following test files must remain and continue to pass:

| File | Tests |
|---|---|
| `apps/web/src/hooks/useHarness.test.ts` | 15 tests |
| `apps/web/src/pages/AgentWorkflows.harness.test.tsx` | 8 tests |

### 4. No Mock State (confirm unchanged)

- All harness data flows through `harnessApi` → `apiClient` → real `/v1/harness/*` endpoints
- Gate approve/reject calls `useDecideGate` → `harnessApi.decideGate`
- Polling stops when `isTerminalState(run.current_state)` returns true
- Pending gates poll at `POLL_INTERVALS.workflows` (5 s) and stop when no pending gates remain

---

## Acceptance Criteria

- [ ] `pnpm tsc --noEmit` run in Node ≥22 environment
- [ ] Zero TypeScript errors attributable to harness files
- [ ] Pre-existing TypeScript errors documented and left untouched
- [ ] `useHarness.test.ts`: 15/15 passing
- [ ] `AgentWorkflows.harness.test.tsx`: 8/8 passing
- [ ] `make docs-harness` exits 0
- [ ] Both bug fixes confirmed present in final state

---

## Implementation Steps

1. Run `pnpm tsc --noEmit` in a Node ≥22 environment
2. Triage errors: separate harness-introduced from pre-existing
3. Fix harness-introduced errors only (if any)
4. Re-run harness tests to confirm fixes did not break coverage
5. Re-run `make docs-harness` to confirm doc validation still passes
6. Produce final verification report

---

## Final Verification Report Template

```
## Harness UI — Final Verification Report

### Bug Fixes (preserved)
- useHarness.ts: POLL_INTERVALS from ./usePolling ✅
- AgentWorkflows.tsx: DataTable columns= prop ✅

### Harness-specific tests
- useHarness.test.ts: 15/15 ✅
- AgentWorkflows.harness.test.tsx: 8/8 ✅

### Broader suite baseline (pre-existing, not caused by harness work)
- Baseline before harness work: 19 test files failing / 122 tests failing
- After harness work: 16 test files failing / 100 tests failing (net improvement from DataTable bug fix)
- Harness-introduced regressions: 0

### TypeScript verification
- Command: node_modules/.bin/tsc --noEmit
- Harness-related errors: 0
- Pre-existing errors (not touched): useValueSignals.ts, TargetsAdmin.*, valueSignal.ts
- Environment: Node 20 (project requires ≥22 — environment caveat, not a harness failure)
- Result: PASSED
- Recommended CI confirmation: re-run under Node ≥22

### make docs-harness
- Result: all checks passed ✅

### Production signoff
- Frontend Harness UI verification: COMPLETE
- Classification: Harness UI regression coverage complete; production signoff pending Node ≥22 CI confirmation
```

---

## Out of Scope

- Fixing pre-existing TypeScript errors in `useValueSignals.ts`, `TargetsAdmin.*`, `valueSignal.ts`
- Cleaning the broader test suite baseline (100 pre-existing failures)
- Any new harness features or UI changes

---

## [ARCHIVED] Original Implementation Spec

The sections below are the original implementation spec, preserved for reference. All items were completed.

### 1. Backend — FastAPI Harness Routes

Create `services/layer4-agents/src/api/routes/harness.py` and register it in `src/api/routers.py` under prefix `/v1`.

**Run management:**
- `POST   /v1/harness/runs` — create a new `HarnessRun`
- `GET    /v1/harness/runs` — list runs for authenticated tenant (filterable by `status`, `workflow_type`)
- `GET    /v1/harness/runs/{run_id}` — get a single run
- `POST   /v1/harness/runs/{run_id}/transition` — advance state machine (`to_state`, optional `validation_results`, `human_override`, `state_payload`)
- `DELETE /v1/harness/runs/{run_id}` — cancel/archive a run

**Checkpoints:**
- `GET    /v1/harness/runs/{run_id}/checkpoints` — list checkpoints for a run
- `GET    /v1/harness/runs/{run_id}/checkpoints/latest` — get latest checkpoint

**Human gates:**
- `GET    /v1/harness/runs/{run_id}/gates` — list gates for a run
- `POST   /v1/harness/runs/{run_id}/gates` — create a gate (`gate_type`)
- `POST   /v1/harness/gates/{gate_id}/decide` — approve / reject / modify / expire a gate

**Validation:**
- `POST   /v1/harness/runs/{run_id}/validate` — validate claims for a run (delegates to `ValidationHook`)

**Health:**
- `GET    /v1/harness/health` — returns `validation_available`, `l5_healthy`, `db_healthy`

**Constraints:**
- All routes must extract `tenant_id` from authenticated context (never from request body).
- All routes must use `make_live_l5_registry` (or `make_sql_registry` when L5 is not configured) injected via FastAPI dependency.
- Error responses must follow the existing error shape used by `/v1/workflows/*`.
- All Pydantic request/response models must live in `src/harness/api_models.py` (new file).

### 2. OpenAPI Contract Update

After routes are registered, regenerate `contracts/openapi/layer4-agents.json` via `make contracts`. The harness paths must appear in the contract. The frontend generated client (`apps/web/src/api/generated/l4/`) must be regenerated via `make contract-freshness`.

### 3. Frontend — TypeScript API Client

Create `apps/web/src/api/harness.ts`:
- TypeScript types mirroring `HarnessRun`, `HarnessCheckpoint`, `HumanGate`, `ClaimValidationResult`, `HarnessState`, `HarnessRunStatus`, `GateStatus`, `GateType`, `ValidationState`
- `harnessApi` object with typed functions for each route group (runs, checkpoints, gates, validate, health)
- Follows the existing pattern in `apps/web/src/api/workflows.ts`

### 4. Frontend — React Query Hooks

Create `apps/web/src/hooks/useHarness.ts`:
- `useHarnessRuns({ status?, workflow_type?, limit, offset })` — paginated list
- `useHarnessRun(runId)` — single run with polling when status is non-terminal
- `useHarnessCheckpoints(runId)` — checkpoint list
- `useHarnessGates(runId)` — gate list
- `useCreateHarnessRun()` — mutation
- `useTransitionHarnessRun()` — mutation (advance state)
- `useDecideGate()` — mutation (approve/reject/modify/expire)
- `useValidateHarnessClaims()` — mutation
- Follows the existing patterns in `apps/web/src/hooks/useWorkflows.ts` (TanStack Query, `QK` query keys, `STALE_TIME`, `POLL_INTERVALS`)

### 5. Frontend — AgentWorkflows.tsx Extension

Extend `apps/web/src/pages/AgentWorkflows.tsx` to add a **"Harness Runs"** tab alongside the existing "Workflow Dashboard", "Whitespace Analysis", and "Business Cases" tabs.

The Harness Runs tab must display:
- A paginated list of harness runs (run ID, workflow type, current state, status badge, created at)
- Per-run inline actions: **Resume** (transition to next state), **Retry** (re-enter failed state), **Cancel** (transition to CANCELLED)
- A **View** button that opens a `HarnessRunDetail` sheet showing:
  - Run metadata (ID, tenant, workflow type, initiated by, trace ID)
  - Current state and status with visual state machine progress
  - Checkpoint list (state name, created at, input hash)
  - Human gate list (gate type, status, decision by, decision reason) with **Approve** / **Reject** actions for `PENDING` gates
  - Validation outcomes (claim ID, state, confidence, validator, reason)
  - Available control actions based on current state

**Constraints:**
- Preserve existing page structure, `PageHeader`, `Tabs`, `SectionCard`, `DataTable`, `StatusBadge`, `QueryState` primitives from `WfPrimitives`
- Do not introduce new UI libraries
- Add loading, empty, and error states consistent with existing patterns
- The "Human-in-Loop Pending" KPI card on the dashboard tab should count pending harness gates in addition to workflow pending count

### 6. YAML Configuration Files

#### `services/layer4-agents/config/harness.runtime.yaml`

Agent/workflow runtime configuration. Must include:
- `schema_version`
- Per-workflow-type sections (`roi_calculator`, `whitespace_analysis`, `business_case`, `orchestrator`) each with:
  - `allowed_tools` list
  - `denied_tools` list
  - `budget`: `max_steps`, `max_retries`, `timeout_seconds`, `max_cost_usd`
  - `invariants`: `require_human_approval` (list of states), `max_tool_calls_per_run`
  - `validation`: `require_l5_validation` (bool), `stale_threshold_hours`
  - `checkpointing`: `enabled` (bool), `checkpoint_on_states` (list)
  - `failure_policy`: `on_l5_unavailable` (`degrade` | `block`), `on_gate_timeout` (`expire` | `block`)
  - `audit`: `emit_trace_events` (bool), `log_level`
- References to corresponding `.abom.json` manifests in `services/layer4-agents/manifests/`

#### `services/layer4-agents/config/harness.service.yaml`

Service deployment configuration. Must include:
- `schema_version`
- `service`: name, version, port
- `database`: pool size, timeout, migration auto-run
- `l5_integration`: base_url env var, service_token env var, stale_threshold_hours, health_check_interval_seconds
- `queue`: concurrency, max_retries, retry_backoff_seconds
- `timeouts`: default_run_timeout_seconds, gate_decision_timeout_seconds
- `feature_flags`: `harness_enabled`, `live_l5_validation_enabled`, `sql_registry_enabled`
- `observability`: log_level, trace_sampling_rate, emit_metrics
- `security`: require_tenant_context, validate_claim_tenant_on_submit
- `health`: readiness_checks list

### 7. Documentation

#### `docs/architecture/harness-agent-integration.md` (new file)

Architecture-level document covering:
- Harness purpose and role in the six-layer pipeline
- Relationship to LangGraph workflows and existing `/v1/workflows/*` surface
- Key concepts: runs, state machine, transitions, checkpoints, human gates, validation hook, LiveL5Validator
- Data flow diagram (text/ASCII): UI → API → SqlHarnessRegistry → L5 → UI
- Tenant isolation model
- Security and RBAC notes
- Extension points (custom validators, new workflow types, pack integration)

#### `services/layer4-agents/docs/harness-runbook.md` (new file)

Operator/developer runbook covering:
- Setup and environment variables (`L5_BASE_URL`, `L5_SERVICE_TOKEN`, `DATABASE_URL`)
- Factory selection: `make_in_memory_registry` vs `make_sql_registry` vs `make_live_l5_registry`
- API reference: all `/v1/harness/*` endpoints with method, path, request schema, response schema, status codes, and example payloads
- Common workflows: create run → transition → validate → gate → complete
- Human gate lifecycle: create → pending → approve/reject → effect on run
- Validation outcomes: state mapping table, staleness behavior, fallback behavior
- Checkpoint usage: deterministic hashing, replay, verify_payload_unchanged
- Failure modes: L5 unavailable, gate timeout, state machine violation, tenant mismatch
- Recovery procedures: how to resume a stuck run, how to expire a stale gate
- Observability: trace events, structured logs, metrics emitted
- Testing guidance: unit (MockValidator), integration (SQLite), contract, E2E expectations
- Known limitations and future extension points

### 8. Generation and Validation Script

#### `scripts/generate_harness_docs.py`

A Python script that:
1. **Validates** required documentation files exist and are non-empty:
   - `docs/architecture/harness-agent-integration.md`
   - `services/layer4-agents/docs/harness-runbook.md`
2. **Validates** required YAML config files exist, are syntactically valid YAML, and contain required top-level keys:
   - `services/layer4-agents/config/harness.runtime.yaml` — required keys: `schema_version`, `workflows`
   - `services/layer4-agents/config/harness.service.yaml` — required keys: `schema_version`, `service`, `l5_integration`, `feature_flags`
3. **Generates** a Markdown table of all harness API endpoints (method, path, summary) by introspecting the FastAPI router from `src/api/routes/harness.py` and writes it to `services/layer4-agents/docs/harness-api-table.md`
4. **In `--check` mode** (default for CI): compares the generated endpoint table against the committed file and fails with a diff if stale
5. **In `--fix` mode**: overwrites the committed file with the freshly generated output
6. Exits non-zero with clear, actionable error messages on any failure

#### Makefile target

```makefile
.PHONY: docs-harness
docs-harness: ## Validate harness docs and config; regenerate API table
	python scripts/generate_harness_docs.py --check
```

Wire `docs-harness` into the existing `verify` target by appending it to the `verify` recipe dependencies.

---

## Acceptance Criteria

### Backend
- [ ] `GET /v1/harness/runs` returns 200 with paginated run list scoped to authenticated tenant
- [ ] `POST /v1/harness/runs/{run_id}/transition` advances state and returns updated run + trace event
- [ ] `POST /v1/harness/gates/{gate_id}/decide` with `approved` transitions gate and is reflected in run
- [ ] `POST /v1/harness/runs/{run_id}/validate` returns `ClaimValidationResult` list
- [ ] All routes return 403/404 (not 500) on tenant mismatch or missing resource
- [ ] Harness paths appear in `contracts/openapi/layer4-agents.json` after `make contracts`

### Frontend
- [ ] "Harness Runs" tab is visible on `AgentWorkflows.tsx` and renders paginated run list
- [ ] Run detail sheet shows checkpoints, gates, and validation outcomes
- [ ] Approve/Reject gate actions call the API and optimistically update the UI
- [ ] Resume/Retry/Cancel actions call the correct transition endpoint
- [ ] Loading, empty, and error states are present and consistent with existing page patterns
- [ ] No new UI libraries introduced

### YAML Config
- [ ] `harness.runtime.yaml` is syntactically valid and contains all required sections
- [ ] `harness.service.yaml` is syntactically valid and contains all required sections
- [ ] Both files are committed to `services/layer4-agents/config/`

### Documentation
- [ ] `docs/architecture/harness-agent-integration.md` covers all required sections
- [ ] `services/layer4-agents/docs/harness-runbook.md` covers all required sections including full API reference
- [ ] `services/layer4-agents/docs/harness-api-table.md` is generated and committed

### Automation
- [ ] `python scripts/generate_harness_docs.py --check` exits 0 when all files are present and current
- [ ] `python scripts/generate_harness_docs.py --check` exits non-zero with actionable message when a file is missing or stale
- [ ] `make docs-harness` invokes the script successfully
- [ ] `make verify` includes `docs-harness` and fails if harness docs/config are missing or stale

---

## Implementation Order

1. **`src/harness/api_models.py`** — Pydantic request/response models for all harness routes
2. **`src/api/routes/harness.py`** — FastAPI router with all 12 endpoints; inject `SqlHarnessRegistry` via dependency
3. **`src/api/routers.py`** — register harness router at `/v1`
4. **`make contracts`** — regenerate `contracts/openapi/layer4-agents.json`
5. **`make contract-freshness`** — regenerate `apps/web/src/api/generated/l4/`
6. **`apps/web/src/api/harness.ts`** — TypeScript types and `harnessApi` client
7. **`apps/web/src/hooks/useHarness.ts`** — TanStack Query hooks
8. **`apps/web/src/components/HarnessRunDetail.tsx`** — detail sheet component (checkpoints, gates, validation)
9. **`apps/web/src/pages/AgentWorkflows.tsx`** — add "Harness Runs" tab; update KPI card
10. **`services/layer4-agents/config/harness.runtime.yaml`** — agent runtime config
11. **`services/layer4-agents/config/harness.service.yaml`** — service deployment config
12. **`docs/architecture/harness-agent-integration.md`** — architecture doc
13. **`services/layer4-agents/docs/harness-runbook.md`** — operator runbook
14. **`scripts/generate_harness_docs.py`** — validation + generation script
15. **`Makefile`** — add `docs-harness` target; wire into `verify`
16. **Run `make docs-harness`** — confirm script passes against committed files

---

## Files Created / Modified

| File | Action |
|---|---|
| `services/layer4-agents/src/harness/api_models.py` | Create |
| `services/layer4-agents/src/api/routes/harness.py` | Create |
| `services/layer4-agents/src/api/routers.py` | Modify (register router) |
| `contracts/openapi/layer4-agents.json` | Regenerated |
| `apps/web/src/api/generated/l4/index.ts` | Regenerated |
| `apps/web/src/api/harness.ts` | Create |
| `apps/web/src/hooks/useHarness.ts` | Create |
| `apps/web/src/components/HarnessRunDetail.tsx` | Create |
| `apps/web/src/pages/AgentWorkflows.tsx` | Modify (add tab + KPI update) |
| `services/layer4-agents/config/harness.runtime.yaml` | Create |
| `services/layer4-agents/config/harness.service.yaml` | Create |
| `docs/architecture/harness-agent-integration.md` | Create |
| `services/layer4-agents/docs/harness-runbook.md` | Create |
| `services/layer4-agents/docs/harness-api-table.md` | Generated |
| `scripts/generate_harness_docs.py` | Create |
| `Makefile` | Modify (add `docs-harness`, wire into `verify`) |

---

## Out of Scope

- New top-level navigation page for harness (deferred)
- CommandCenter right-rail harness panel (deferred — noted as future extension)
- Real-time SSE streaming for harness state transitions (deferred — polling sufficient for MVP)
- Harness-to-LangGraph bridge (harness and LangGraph workflows remain separate surfaces)
- Frontend tests beyond existing `AgentWorkflows.tsx` patterns
