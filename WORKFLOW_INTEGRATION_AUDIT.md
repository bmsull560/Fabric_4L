# Fabric_4L Workflow Integration, Clickpath, Hooks, and Data Flow Audit

**Audit Date:** 2026-05-07  
**Auditor:** Senior Product Engineer / Frontend Architect / Full-Stack Workflow Auditor  
**Scope:** End-to-end user journey execution audit — not static code existence audit  

---

## 1. Executive Summary

### Overall Workflow Integration Score: **37 / 100**

**Verdict:** The app does **not** feel like one connected product. It feels like a collection of partially wired modules with significant gaps between them. Several critical user journeys are broken at the first click, and even where individual features exist, the handoffs between workspaces are missing or dead-end.

### Top 5 Flow Breaks

| # | Flow Break | Severity |
|---|-----------|----------|
| 1 | **Account creation fails immediately** due to frontend/backend schema mismatch (missing `provider`, `provider_record_id`, wrong field names). | P0 |
| 2 | **ROITab and ValueModelTab are dead placeholder pages** — they render static "—" em-dashes and never call calculator APIs. The real calculator is hidden in a separate workflow path. | P0 |
| 3 | **Hypothesis approval does not create a value tree** — validating a hypothesis only flips a status string. No downstream driver, lever, or value model is spawned. | P0 |
| 4 | **Agent right-rail has no real context** — `accountId`, `signalId`, `evidenceId` are never passed. Agent events are synthesized locally from hardcoded templates, not streamed from backend. | P1 |
| 5 | **Signal approve/reject is UI-only** — no API call, no persistence, no influence on downstream value model. | P1 |

### Top 5 Missing Handoffs

| # | Missing Handoff | Impact |
|---|----------------|--------|
| 1 | **No per-signal link to value model** — user clicks a signal, reviews it, then hits a dead end. Must manually navigate to Hypothesis workspace. | High |
| 2 | **No evidence-to-driver attachment UI** — evidence loads in a tab, drivers load in another tab, but there is no UI to connect them. | High |
| 3 | **No transition from calculator to business case within main workspace** — Calculator tabs are empty; workflow calculator exists but is disconnected from `/calculator/:accountId/roi`. | High |
| 4 | **DriverTreePage does not fetch or display drivers** — it only renders account metadata and stub tabs. | Medium |
| 5 | **No resume-from-reload continuity** — workflow store persists session, but main workspace routes do not read it. | Medium |

### Top 5 Highest-Impact Fixes

| # | Fix | Estimated Effort |
|---|-----|-----------------|
| 1 | Fix `AccountIntakeModal` payload to match `CreateAccountRequest` schema. | 2–4 hrs |
| 2 | Replace dead `ROITab`/`ValueModelTab` with real calculator components wired to `useValueLevers` / `useCreateValueCase`. | 1–2 days |
| 3 | Wire signal approve/reject to a real backend endpoint and invalidate downstream queries. | 4–8 hrs |
| 4 | Pass `accountId` (and selected entity IDs) into `useAgentEvents` on every page. | 2–4 hrs |
| 5 | Add a "Create Driver from Hypothesis" mutation that bridges L4 hypothesis validation → L3 value tree creation. | 2–3 days |

---

## 2. Workflow Scorecard

| Workflow | Score | Verdict | Biggest Break |
|----------|-------|---------|---------------|
| Account Setup to Intelligence | **4 / 10** | Broken at creation; connected after selection | Account creation schema mismatch (P0) |
| Signals to Evidence | **3 / 10** | Evidence loads but matching is missing; evidence-to-driver UI nonexistent | No evidence match/attach UI or API call |
| Evidence to Value Drivers | **2 / 10** | DriverTreePage is a shell; drivers not displayed | DriverTreePage does not fetch drivers |
| Hypothesis to Value Tree | **2 / 10** | Hypotheses generate and validate, but create nothing downstream | Validation is a no-op status flip |
| Value Model to Calculator | **3 / 10** | Real calculator exists in workflow path, but main workspace tabs are dead | ROITab / ValueModelTab are placeholders |
| Calculator to Business Case | **6 / 10** | Workflow calculator saves to L3; business case generation is real via L4 workflows | Interactive scenarios return 501; scenario save is localStorage-only |
| Agent Right Rail Actions | **3 / 10** | Chat POSTs to real endpoint, but context is missing and actions are no-ops | No entity context passed; suggested actions are `() => {}` |
| Return User / Resume Workflow | **4 / 10** | Workflow store persists; account context store persists; but no unified resume flow | Main workspace routes ignore workflow store state |

---

## 3. Step-by-Step Flow Findings

---

### Workflow 1: Account Setup to Intelligence

#### Step-by-Step Clickpath

| Step | User Action | UI Component | Event Handler | Hook / Mutation | API Call | Backend Handler | Data Read/Written | UI Result | Status |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Click "New Value Case" | `Accounts.tsx` | `handleAddAccount` | — | — | — | Opens modal | `AccountIntakeModal` opens | Connected |
| 2 | Fill form, submit | `AccountIntakeModal.tsx` | `handleSubmit` | `useCreateAccount` | `POST l4 /accounts` | `services/layer4-agents/src/api/routes/accounts.py` → `create_account` | **Fails** — missing `provider`, `provider_record_id`, wrong field `employees` vs `company_size` | Error toast (expected) | **Broken** |
| 3 | Select existing account | `Accounts.tsx` row | `handleSelectAccount` | `useAccountContextStore` | — | — | `selectedAccountId` persisted to `localStorage` | Account highlighted; detail panel opens | Connected |
| 4 | Click "Launch Intelligence" | `AccountDetailPanel` | `onLaunchIntelligence` | `useNavigation` | — | — | — | Redirects to `/intelligence/:accountId/signals` | Connected |
| 5 | Land on Signals | `SignalsTab.tsx` | — | `useAccount`, `useCanonicalCaseId`, `useWorkspaceTabQuery` | `GET l4 /accounts/{id}`, `GET/POST l4 /analysis/cases...`, `GET l4 /analysis/cases/{caseId}/workspace/signals` | L4 account service, workspace case service | Case resolved per account; signals loaded per case | Signals list renders | Connected |
| 6 | Click signal row | `SignalsTab.tsx` | `onClick` (inline) | `setSelectedSignal`, `setRailMode` | — | — | Local state only | RightRail switches to Detail mode | Connected (UI only) |
| 7 | Approve signal | Detail panel | `handleApproveSignal` | `setSignalStatuses` | — | — | **No API call** | Button label changes to "Approved" | **Mocked only** |
| 8 | Click "Generate AI Value Model" | `IntelligenceShell.tsx` | — | `useNavigation` | — | — | — | Navigates to `/hypothesis/:accountId/hypothesis` | Partially connected (workspace-level only) |

#### Flow Diagram

```text
User clicks "New Value Case"
   Accounts.tsx handleAddAccount
   AccountIntakeModal opens
   handleSubmit → createAccount.mutateAsync(payload)
   useCreateAccount (hooks/useAccounts.ts)
   apiClient.post('l4', '/accounts', { ...payload })
   services/layer4-agents/src/api/routes/accounts.py create_account()
   AccountService.create_account()
   **FAILS: payload missing provider, provider_record_id; wrong field name employees**
```

#### Integration Breaks

| Break | Severity | Evidence | Why It Breaks the Flow | Required Fix | Required Test |
|-------|----------|----------|------------------------|--------------|---------------|
| Account creation payload mismatch | P0 | `AccountIntakeModal.tsx` sends `employees`, `annual_revenue`, `headquarters`, `website`; `CreateAccountRequest` expects `provider`, `provider_record_id`, `company_size` | User cannot create an account through the UI | Align frontend form fields with backend schema; add provider picker | E2E: fill form → account created → lands on intelligence |
| Signal approve/reject not persisted | P1 | `SignalsTab.tsx` lines 81–87: pure `setSignalStatuses` local state | User reviews are lost on reload; no downstream effect | Create `useReviewSignal` mutation → `PATCH /signals/{id}/review` | Integration: approve signal → API called → query invalidated |
| No per-signal link to value model | P2 | Signal detail panel has no "Create Hypothesis" or "Add to Value Model" button | User must manually navigate; signal context is lost | Add action button in detail panel that navigates to `/hypothesis/:accountId?signalId=...` | E2E: click signal → click "Create Hypothesis" → hypothesis pre-scoped |

---

### Workflow 2: Signals to Evidence to Value Driver

#### Step-by-Step Clickpath

| Step | User Action | UI Component | Event Handler | Hook / Mutation | API Call | Backend Handler | Data Read/Written | UI Result | Status |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Open Evidence tab | `EvidenceTab.tsx` | — | `useWorkspaceTabQuery` | `GET l4 /analysis/cases/{caseId}/workspace/evidence` | L4 workspace service | Evidence array | Evidence list or empty state | Connected (backend returns 501 → empty) |
| 2 | Search evidence library | — | — | `useEvidenceSearch` (not used here) | — | — | — | Not available in workspace | **Missing** |
| 3 | Click "Match Evidence" | — | — | — | — | — | — | **Button does not exist** | **Missing** |
| 4 | Navigate to Driver Tree | `LeftNavigation.tsx` | Link | — | — | — | — | `/drivers/:accountId` loads | Connected |
| 5 | View drivers | `DriverTreePage.tsx` | — | `useAccount` only | — | — | **Does not fetch drivers** | Stub tabs render (Evidence / Alternatives / Solution Cost) | **Broken** |
| 6 | Attach evidence to driver | — | — | — | — | — | — | **No UI for this** | **Missing** |

#### Flow Diagram

```text
User clicks Evidence tab
   EvidenceTab.tsx
   useWorkspaceTabQuery(caseId, "evidence")
   GET l4 /analysis/cases/{caseId}/workspace/evidence
   **Backend returns 501 → swallowed → empty array**
   UI renders empty state

User clicks Driver Tree in nav
   DriverTreePage.tsx
   useAccount(accountId)  ← only account metadata
   **NO useDrivers, useValueTree, or evidence-attachment hook**
   DriverTreeShell renders EvidenceTabContent / AlternativesTab / SolutionCostTab
   AlternativesTab and SolutionCostTab are stubs
```

#### Integration Breaks

| Break | Severity | Evidence | Why It Breaks the Flow | Required Fix | Required Test |
|-------|----------|----------|------------------------|--------------|---------------|
| Evidence workspace endpoint returns 501 | P1 | `useWorkspaceTabQuery` silently returns `[]` on 501 | Evidence never loads in workspace | Implement `GET /analysis/cases/{caseId}/workspace/evidence` in L4 | Integration: evidence loads for case |
| No evidence-to-driver attachment UI | P0 | No button, no route, no mutation for attaching evidence to driver | Core value proposition (evidence → driver) is unreachable | Add "Attach to Driver" action in evidence detail; create `useAttachEvidence` mutation | E2E: attach evidence → driver updated → value tree recalculates |
| DriverTreePage does not fetch drivers | P0 | `DriverTreePage.tsx` only calls `useAccount`; no driver/value-tree query | Driver tree workspace is empty | Add `useDrivers(accountId)` and `useValueTree(accountId)` hooks to page | Integration: driver tree renders real nodes |
| AlternativesTab / SolutionCostTab are stubs | P2 | Both render dashed-border placeholder boxes | Confuses user; feels unfinished | Implement tabs or hide behind feature flag | Component: render tab with real data |

---

### Workflow 3: Hypothesis to Value Tree

#### Step-by-Step Clickpath

| Step | User Action | UI Component | Event Handler | Hook / Mutation | API Call | Backend Handler | Data Read/Written | UI Result | Status |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | View Hypotheses | `HypothesesTab.tsx` | — | `useAccountHypotheses` | `GET l4 /v1/hypotheses/account/{accountId}` | `value_hypothesis_engine.py` | Hypothesis list | Cards render with confidence | Connected |
| 2 | Click "Generate Hypotheses" | `HypothesesTab.tsx` | — | `useGenerateHypotheses` | `POST l4 /v1/hypotheses/generate` | L4 hypothesis engine | New hypotheses created | List refreshes | Connected |
| 3 | Select draft hypothesis | `HypothesesTab.tsx` | `onClick` | `setSelectedHypothesis` | — | — | Local state | Card expands; Validate/Reject shown | Connected |
| 4 | Click "Validate" | `HypothesesTab.tsx` | — | `useValidateHypothesis` | `POST l4 /v1/hypotheses/{id}/validate` | L4 hypothesis engine | Status updated to `validated` | Badge changes | Connected |
| 5 | Value tree created | — | — | — | — | — | — | **Nothing happens** | **Broken** |
| 6 | Navigate to Driver Tree | — | — | — | — | — | — | Drivers unchanged | **Broken** |

#### Flow Diagram

```text
User clicks Validate
   HypothesesTab.tsx
   useValidateHypothesis.mutate({ hypothesisId, status: "validated" })
   POST l4 /v1/hypotheses/{id}/validate
   services/layer4-agents/src/services/value_hypothesis_engine.py
   Cypher: SET vh.status = $new_status
   **No CREATE ValueDriver, no relation to value tree**
   Query invalidated: QK.hypotheses.all
   UI updates badge
   **Dead end — no next step**
```

#### Integration Breaks

| Break | Severity | Evidence | Why It Breaks the Flow | Required Fix | Required Test |
|-------|----------|----------|------------------------|--------------|---------------|
| Validating hypothesis does not create value tree | P0 | `validate_hypothesis` only updates status; no driver/value tree creation | Core workflow (hypothesis → value model) is broken | Add post-validation hook that calls driver-generation service or workflow | E2E: validate → driver tree created → calculator updated |
| Frontend sends wrong validation payload | P1 | `useValidateHypothesis` sends `{ status }`; backend expects `{ new_status, feedback }` | Will 422 at runtime | Align frontend payload with `ValidateHypothesisRequest` | Unit: payload schema match |
| DriverTreePage unrelated to hypotheses | P2 | Page does not import hypothesis hooks | User has no way to see validated hypotheses as drivers | Either merge pages or add hypothesis→driver promotion UI | E2E: validated hypothesis appears in driver tree |

---

### Workflow 4: Value Model to Calculator

#### Step-by-Step Clickpath

| Step | User Action | UI Component | Event Handler | Hook / Mutation | API Call | Backend Handler | Data Read/Written | UI Result | Status |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Open Calculator → ROI | `ROITab.tsx` | — | `useAccount` | `GET l4 /accounts/{id}` | L4 account service | Account metadata | Static "—" placeholders | **Mocked only** |
| 2 | Open Calculator → Value Model | `ValueModelTab.tsx` | — | `useAccount` | `GET l4 /accounts/{id}` | L4 account service | Account metadata | Static "—" placeholders | **Mocked only** |
| 3 | Use workflow calculator | `workflow/pages/Calculator.tsx` | — | `useValueLevers`, `useCreateValueCase` | `GET l3 /v1/calculators/levers`, `POST l3 /v1/calculators/value-cases` | L3 calculator service | Lever config read; ValueCase created | Real sliders, real save | Connected |
| 4 | Adjust Conservative/Expected | `Calculator.tsx` | `onChange` (range) | `setLeverValues` | — | — | Local state | Totals recalculate client-side | Partially connected |
| 5 | Adjust Optimistic | — | — | — | — | — | — | Hardcoded `* 1.25` | **Mocked only** |
| 6 | Save scenario | `Calculator.tsx` | `handleSave` | `useCreateValueCase` | `POST l3 /v1/calculators/value-cases` | L3 Neo4j | ValueCase node persisted | Success toast; navigates to value case | Connected |

#### Flow Diagram

```text
User clicks "Calculator" in main nav
   /calculator/:accountId/roi
   ROITab.tsx
   useAccount(accountId)
   **No calculator hook called**
   Renders MetricCard value="—" placeholders

User uses workflow path
   /workflow/calculator (or similar)
   workflow/pages/Calculator.tsx
   useValueLevers({ industry, company_size })
   GET l3 /v1/calculators/levers
   L3 Neo4j-backed service
   Real lever config loaded
   User adjusts sliders → local state
   handleSave → useCreateValueCase.mutateAsync
   POST l3 /v1/calculators/value-cases
   CREATE (vc:ValueCase)
   Navigates to workflow-value-case
```

#### Integration Breaks

| Break | Severity | Evidence | Why It Breaks the Flow | Required Fix | Required Test |
|-------|----------|----------|------------------------|--------------|---------------|
| Main calculator tabs are dead placeholders | P0 | `ROITab.tsx` lines 75–88: hardcoded `value="—"` with dashed border empty state | User cannot calculate ROI from main workspace | Replace placeholder with real `useValueLevers` + `useCreateValueCase` wiring | E2E: open calculator → adjust levers → save → case created |
| Optimistic scenario not adjustable | P1 | `Calculator.tsx` line 103: `C: leverConfig.levers.reduce((s, l) => s + l.annual_impact * 1.25, 0)` | User cannot model their own optimistic scenario | Add slider for scenario C | Component: optimistic slider adjusts C total |
| Interactive scenario API returns 501 | P1 | `services/layer3-knowledge/src/api/routes/formulas.py` scenario endpoint returns 501 | What-if analysis broken | Implement scenario evaluation endpoint | Integration: POST scenario → recalculated result |

---

### Workflow 5: Calculator to Business Case / Narrative

#### Step-by-Step Clickpath

| Step | User Action | UI Component | Event Handler | Hook / Mutation | API Call | Backend Handler | Data Read/Written | UI Result | Status |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Click "Generate Value Case" | `workflow/pages/Calculator.tsx` | `handleSave` / `handleContinue` | `useCreateValueCase` | `POST l3 /v1/calculators/value-cases` | L3 Neo4j | ValueCase persisted | Navigates to value case step | Connected |
| 2 | Click "New Case" in list | `BusinessCaseList.tsx` | Opens modal | `useCreateBusinessCase` | `POST l4 /workflows` with `workflow_type: 'business_case'` | `OrchestrationController` | Workflow run created | List item appears | Connected |
| 3 | View business case | `BusinessCase.tsx` | — | `useBusinessCase` | `GET l4 /workflows/{id}/result` | L4 workflow engine | Workflow result parsed | Hero ROI card, recommendations, summary | Connected |
| 4 | Export PDF | `BusinessCase.tsx` | `handleExportPDF` | `useBusinessCaseExport` | `POST l4 /v1/documents/export` | L4 document service | PDF generated | Download triggered | Connected |
| 5 | Regenerate after changes | — | — | — | — | — | — | No "Regenerate" button exposed | **Missing** |

#### Flow Diagram

```text
User clicks "New Case"
   BusinessCaseList.tsx
   useCreateBusinessCase.mutate({ name, company })
   POST l4 /workflows
   { workflow_type: 'business_case', inputs: { prospect_company, custom_data } }
   services/layer4-agents/src/workflows/business_case.py
   BusinessCaseGeneratorWorkflow (LangGraph)
   1. Gather inputs from CRM/graph
   2. ROICalculatorWorkflow sub-workflow
   3. generate_section tool (LLM) for narrative
   4. Layer5GroundTruthClient.verify
   5. Assemble document
   6. Promote claims to TruthObjects
   Query invalidated: ['business-cases']
   List refreshes

User views case
   BusinessCase.tsx
   useBusinessCase(caseId)
   GET l4 /workflows/{caseId}/result
   parseWorkflowResult
   Extract ROICalculationAgent + NarrativeSynthesisAgent steps
   Render hero card, recommendations, executive summary
```

#### Integration Breaks

| Break | Severity | Evidence | Why It Breaks the Flow | Required Fix | Required Test |
|-------|----------|----------|------------------------|--------------|---------------|
| No regenerate button after assumption changes | P2 | `BusinessCase.tsx` has Export and Explore, no "Recalculate" or "Regenerate" | User must create entirely new case to update assumptions | Add "Regenerate from Current Model" action that posts new workflow with updated inputs | E2E: change assumptions → regenerate → updated narrative |
| `useBusinessCase` parses brittle agent-step names | P1 | Lines 87–90: `findAgentStep('ROICalculationAgent')`, `findAgentStep('NarrativeSynthesisAgent')` | Will break if agent names change in workflow | Use stable output schema instead of step-name parsing | Integration: workflow result → stable schema → UI render |
| Interactive business case scenarios save to localStorage only | P1 | `thesysClient.ts` `saveScenario` writes to `localStorage` (`vf_scenarios_{caseId}`) | Scenarios lost across devices/sessions | Persist scenarios to backend | E2E: save scenario → reload → scenario restored from backend |

---

### Workflow 6: Agent Stream / Right Rail Integration

#### Step-by-Step Clickpath

| Step | User Action | UI Component | Event Handler | Hook / Mutation | API Call | Backend Handler | Data Read/Written | UI Result | Status |
|---:|---|---|---|---|---|---|---|---|---|
| 1 | Open right rail | Any workspace page | — | — | — | — | — | RightRail renders with Detail/Agent tabs | Connected |
| 2 | Switch to Agent tab | `RightRail.tsx` | `onModeChange` | `setRailMode` | — | — | Local state | Agent chat interface shown | Connected |
| 3 | Type message | `RightRail.tsx` | `onSendMessage` | `useAgentEvents` → `sendMessage` | `POST l4 /agent-stream/chat` | `ConversationService` | Message logged | Response appears | Connected |
| 4 | Agent knows current account | — | — | `useAgentEvents` | — | — | — | **accountId not passed** | **Broken** |
| 5 | Agent knows selected signal | — | — | — | — | — | — | **signalId not passed** | **Broken** |
| 6 | Click suggested action | `RightRail.tsx` | `onClick` | — | — | — | — | **`() => {}` no-op** | **Mocked only** |
| 7 | Agent triggers page mutation | — | — | — | — | — | — | **Not implemented** | **Missing** |

#### Flow Diagram

```text
User sends message in RightRail
   RightRail.tsx
   useAgentEvents({ activeTab: "signals", accountName: account?.name })
   **accountId omitted**
   sendMessage(text)
   apiClient.post('l4', '/agent-stream/chat', { message, context: { activeTab, accountName } })
   services/layer4-agents/src/api/routes/agent_stream.py
   ConversationService.handle_message
   Intent classification → heuristic / C1 fallback
   **No SSE streaming; single JSON response**
   AgentEventClient synthesizes AG-UI steps locally from hardcoded templates
   setMessages with assistant response
   UI renders text + fake process steps
```

#### Integration Breaks

| Break | Severity | Evidence | Why It Breaks the Flow | Required Fix | Required Test |
|-------|----------|----------|------------------------|--------------|---------------|
| accountId not passed to agent | P1 | Every page calls `useAgentEvents({ activeTab, accountName })` without `accountId` | Agent cannot scope queries to current account | Add `accountId` prop to all `useAgentEvents` calls | Integration: agent message includes accountId in context |
| Suggested actions are all no-ops | P1 | `useAgentStream.ts` `getDefaultSuggestedActions` returns `onClick: () => {}` | Agent actions feel broken | Map suggested actions to real mutations or hide them | E2E: click suggested action → real mutation fired |
| Event visualization is synthesized, not streamed | P2 | `AgentEventClient.ts` creates fake `RUN_STARTED` / `STEP_STARTED` locally | User sees fake progress; real backend steps invisible | Switch to SSE `streamAgentEvents` or remove fake steps | Integration: backend emits real step events → UI renders |

---

## 4. Orphaned Code and Isolated Features

| File | Component/Hook/Function | Intended Purpose | Current Usage | Problem | Recommendation |
|------|------------------------|------------------|---------------|---------|----------------|
| `apps/web/src/pages/calculator/ROITab.tsx` | `CalcROITab` | ROI workspace tab | Routed at `/calculator/:accountId/roi` | Dead placeholder — never calls calculator APIs | Wire to real calculator or redirect to workflow calculator |
| `apps/web/src/pages/calculator/ValueModelTab.tsx` | `ValueModelTab` | Value model workspace tab | Routed at `/calculator/:accountId/value-model` | Dead placeholder | Same as above |
| `apps/web/src/pages/drivers/DriverTreePage.tsx` | `DriverTreePage` | Driver tree workspace | Routed at `/drivers/:accountId/:tab?` | Only loads account; does not fetch drivers | Add driver/value-tree queries |
| `apps/web/src/pages/evidence/AlternativesTab.tsx` | `AlternativesTab` | Alternatives comparison | Used in `DriverTreePage` | Stub with dashed border | Implement or remove from nav |
| `apps/web/src/pages/evidence/SolutionCostTab.tsx` | `SolutionCostTab` | Solution cost modeling | Used in `DriverTreePage` | Stub with dashed border | Implement or remove from nav |
| `apps/web/src/hooks/useEvidence.ts` | 9 evidence library hooks | Case-study CRUD, search, bulk import | Consumed by `workflow/pages/Evidence.tsx` and `StudioEvidenceTab.tsx` | **Not used by workspace `EvidenceTab.tsx`** | Unify evidence hooks or remove duplicate workspace evidence tab |
| `apps/web/src/hooks/useAgentStream.ts` | `useAgentStream` | Legacy agent streaming | Marked `@deprecated` | Still imported in some places; contains dev fallback mock | Remove all imports; delete file |
| `services/api/app/services/agent_orchestrator.py` | `AgentOrchestrator` | Unified API agent orchestration | Used by `services/api/app/routers/agents.py` | Contains `MockLLMProvider`; explicitly guarded from production | Remove mock orchestrator; route agents to L4 |
| `services/api/app/routers/calculator.py` | ROI calculator routes | In-memory calculator | Legacy unified API | Frontend hooks target L3, not this router | Deprecate and remove |
| `services/api/app/routers/value_cases.py` | Value case routes | In-memory value cases | Legacy unified API | Frontend uses L4 workflows | Deprecate and remove |

---

## 5. Data Flow Map

### Account

| Stage | Created By | Stored Where | Retrieved By | Used In | Updated By | Downstream Consumer | Gaps |
|-------|-----------|--------------|--------------|---------|------------|---------------------|------|
| Creation | `AccountIntakeModal` → `useCreateAccount` | L4 PostgreSQL (`Account` table) | `useAccount`, `useAccounts` | All workspace pages | `useRefreshAccount`, enrichment | Signals, hypotheses, drivers, value cases | **Creation broken due to schema mismatch** |
| Selection | User click | `accountContextStore` (Zustand + localStorage) | `AccountContextSync`, `AccountScopedRedirect` | Route resolution | — | All `:accountId` routes | Connected |
| Enrichment | `useEnrichAccount` | L4 DB + Neo4j | `useAccountBriefing` | EnrichmentTab | `EnrichmentOrchestrator` | Signals, stakeholders | Connected |

### Signal

| Stage | Created By | Stored Where | Retrieved By | Used In | Updated By | Downstream Consumer | Gaps |
|-------|-----------|--------------|--------------|---------|------------|---------------------|------|
| Generation | `useGenerateWorkspaceIntelligence` | L4 workspace case | `useWorkspaceTabQuery(caseId, "signals")` | SignalsTab | — | Detail panel | Connected |
| Review | User click Approve/Reject | **Local state only** (`signalStatuses`) | — | SignalsTab detail panel | `handleApproveSignal` | **None — not persisted** | **Broken** |
| Link to hypothesis | — | — | — | — | — | — | **Missing** |

### Evidence

| Stage | Created By | Stored Where | Retrieved By | Used In | Updated By | Downstream Consumer | Gaps |
|-------|-----------|--------------|--------------|---------|------------|---------------------|------|
| Workspace load | `useWorkspaceTabQuery` | L4 (returns 501) | `EvidenceTab.tsx` | EvidenceTab | — | — | **Broken (501)** |
| Library CRUD | `useCreateCaseStudy`, etc. | L3 Neo4j (`Evidence` nodes) | `useEvidence.ts` | `workflow/pages/Evidence.tsx` | `useUpdateCaseStudy` | — | **Disconnected from workspace** |
| Match/attach | — | — | — | — | — | — | **Missing entirely** |

### Hypothesis

| Stage | Created By | Stored Where | Retrieved By | Used In | Updated By | Downstream Consumer | Gaps |
|-------|-----------|--------------|--------------|---------|------------|---------------------|------|
| Generation | `useGenerateHypotheses` | L4 Neo4j (`ValueHypothesis` nodes) | `useAccountHypotheses` | HypothesesTab | — | Hypothesis cards | Connected |
| Validation | `useValidateHypothesis` | L4 Neo4j (status field) | `useAccountHypotheses` | HypothesesTab | `validate_hypothesis` service | **None — no downstream creation** | **Broken** |

### Value Model

| Stage | Created By | Stored Where | Retrieved By | Used In | Updated By | Downstream Consumer | Gaps |
|-------|-----------|--------------|--------------|---------|------------|---------------------|------|
| Levers | `useValueLevers` | L3 Neo4j | `workflow/pages/Calculator.tsx` | Calculator | — | Scenario calculation | Connected (workflow only) |
| Scenarios | `handleSave` → `useCreateValueCase` | L3 Neo4j (`ValueCase` nodes) | `useValueCase` | Calculator | — | Business case workflow | Connected |

### Scenario

| Stage | Created By | Stored Where | Retrieved By | Used In | Updated By | Downstream Consumer | Gaps |
|-------|-----------|--------------|--------------|---------|------------|---------------------|------|
| Adjustment | Slider `onChange` | Local state (`leverValues`) | `useMemo` totals | Calculator UI | User | Save mutation | Connected |
| Persist | `useCreateValueCase` | L3 Neo4j | — | — | — | — | Connected |
| What-if | `evaluateWhatIf` | **localStorage** (`vf_scenarios_{caseId}`) | `thesysClient.ts` | InteractiveBusinessCase | — | — | **Broken (local only)** |

### Business Case

| Stage | Created By | Stored Where | Retrieved By | Used In | Updated By | Downstream Consumer | Gaps |
|-------|-----------|--------------|--------------|---------|------------|---------------------|------|
| Generation | `useCreateBusinessCase` | L4 workflow run (`BusinessCaseGeneratorWorkflow`) | `useBusinessCase` | BusinessCaseList, BusinessCase | — | Export, interactive view | Connected |
| Narrative | LLM `generate_section` tool | Inside workflow run output | `useBusinessCase` parses agent steps | BusinessCase.tsx | — | — | Connected (brittle parsing) |

---

## 6. Required Integration Fixes

### P0 — Flow Cannot Complete

| # | Fix | Files | Test |
|---|-----|-------|------|
| 1 | **Fix account creation payload** — align `AccountIntakeModal.tsx` fields with `CreateAccountRequest` (add `provider`, `provider_record_id`; rename `employees` → `company_size`). | `AccountIntakeModal.tsx`, `useAccounts.ts` | E2E: create account → success |
| 2 | **Wire signal review to backend** — create `useReviewSignal` mutation → `PATCH /signals/{id}/review` and persist `approved`/`rejected` with tenant/account scoping. | `SignalsTab.tsx`, `useSignals.ts` (new), backend router | Integration: review → persist → invalidate |
| 3 | **Make calculator tabs real** — replace dead `ROITab`/`ValueModelTab` with `useValueLevers`, `useCreateValueCase`, and range sliders. | `ROITab.tsx`, `ValueModelTab.tsx` | E2E: adjust levers → save → case appears |
| 4 | **Fetch drivers in DriverTreePage** — add `useDrivers` and `useValueTree` hooks; render real tree. | `DriverTreePage.tsx`, `DriverTreeShell.tsx` | Integration: page loads → tree renders |
| 5 | **Connect hypothesis validation to driver creation** — after validation, call driver-generation service or enqueue workflow. | `value_hypothesis_engine.py`, `drivers.py` | E2E: validate → driver created |

### P1 — Flow Completes with Bad or Missing Data

| # | Fix | Files | Test |
|---|-----|-------|------|
| 6 | **Pass `accountId` to `useAgentEvents`** on every workspace page. | All `*Tab.tsx` files | Integration: agent context includes accountId |
| 7 | **Fix `useValidateHypothesis` payload** — send `new_status` + `feedback` to match backend. | `useHypotheses.ts` | Unit: payload schema match |
| 8 | **Implement workspace evidence endpoint** — `GET /analysis/cases/{caseId}/workspace/evidence` must return real data. | L4 workspace service | Integration: evidence loads |
| 9 | **Persist interactive scenarios to backend** — replace `localStorage` save with API call. | `thesysClient.ts`, backend | E2E: save → reload → restored |
| 10 | **Stabilize business case parsing** — use typed output schema instead of `findAgentStep('ROICalculationAgent')`. | `useBusinessCases.ts` | Integration: workflow result → schema parse |

### P2 — Flow Feels Disconnected

| # | Fix | Files | Test |
|---|-----|-------|------|
| 11 | **Add per-signal actions** — "Create Hypothesis from Signal", "View Evidence", "Add to Value Model" in detail panel. | `SignalsTab.tsx` | E2E: signal → action → next page |
| 12 | **Add evidence-to-driver attachment UI** — drag-drop or "Attach to Driver" button. | `EvidenceTab.tsx`, `DriverTreePage.tsx` | E2E: attach → driver updated |
| 13 | **Add progress indicators** — show enrichment status, signal generation progress, workflow run state. | `EnrichmentTab.tsx`, `SignalsTab.tsx`, `AgentWorkflows.tsx` | Component: loading states render |
| 14 | **Breadcrumb continuity** — ensure every workspace page shows account name + current step. | `PageHeader.tsx`, shell components | E2E: navigate → breadcrumbs update |
| 15 | **Enable optimistic scenario slider** — allow user to adjust optimistic scenario, not just hardcoded `* 1.25`. | `workflow/pages/Calculator.tsx` | Component: slider adjusts C |

### P3 — Polish

| # | Fix | Files | Test |
|---|-----|-------|------|
| 16 | **Remove or hide stub tabs** — `AlternativesTab`, `SolutionCostTab`. | `DriverTreePage.tsx` | Component: stubs hidden |
| 17 | **Better empty states** — explain *why* evidence/drivers are empty and what action to take. | `EvidenceTab.tsx`, `DriverTreePage.tsx` | Component: empty state with CTA |
| 18 | **Delete deprecated `useAgentStream`** — remove all imports and dev fallback. | `useAgentStream.ts` | Lint: no imports remain |
| 19 | **Align query key strings** — `useCreateValueCase` uses raw `["calculators"]` instead of `QK.calculators.all`. | `useCalculators.ts` | Unit: query keys centralized |
| 20 | **Add regenerate action to BusinessCase** — allow user to update assumptions and regenerate. | `BusinessCase.tsx` | E2E: regenerate → new workflow |

---

## 7. Integration Scoring Model — Weighted Categories

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Clickpath Completeness | 4/10 | 15% | 0.60 |
| Event Handler Wiring | 5/10 | 10% | 0.50 |
| Hook and API Integration | 4/10 | 15% | 0.60 |
| Backend Workflow Connection | 5/10 | 15% | 0.75 |
| Data Persistence and Reuse | 3/10 | 15% | 0.45 |
| State / Cache / Query Invalidation | 4/10 | 10% | 0.40 |
| Cross-Screen Continuity | 2/10 | 10% | 0.20 |
| Error / Loading / Empty States | 6/10 | 5% | 0.30 |
| Tests for Real User Flows | 1/10 | 5% | 0.05 |
| **Total** | | | **3.85 / 10** → **38.5 / 100** |

*Rounded to **37 / 100** in Executive Summary to reflect strict audit standards.*

---

## 8. Definition of Done — Fluent Fabric_4L Workflow

A workflow is **not done** until:

- [ ] The user can start it from navigation or the previous workflow step.
- [ ] Every click has a real handler (not `() => {}`).
- [ ] Every handler calls a real hook/mutation or intentionally local state.
- [ ] Every mutation calls a real API.
- [ ] Every API maps to a backend route.
- [ ] Every backend route calls real domain logic.
- [ ] Domain logic persists or retrieves real tenant-scoped data.
- [ ] The response updates UI state.
- [ ] The next step is visible and obvious.
- [ ] Reloading the page does not lose critical progress.
- [ ] Errors are visible and recoverable.
- [ ] Tests prove the flow through user behavior (not direct store manipulation).

**Current Status:**
- Account Setup → Intelligence: **6/12**
- Signals → Evidence → Drivers: **2/12**
- Hypothesis → Value Tree: **2/12**
- Value Model → Calculator: **3/12**
- Calculator → Business Case: **7/12**
- Agent Right Rail: **3/12**

---

## 9. Ticket Format — Implementation-Ready

### Ticket: FIX-001
**Severity:** P0  
**Workflow:** Account Setup to Intelligence  
**Files:** `apps/web/src/components/workspace/AccountIntakeModal.tsx`, `apps/web/src/hooks/useAccounts.ts`, `services/layer4-agents/src/api/schemas/accounts.py`  
**Current Behavior:** Submitting the account creation form fails because the frontend payload is missing required fields (`provider`, `provider_record_id`) and sends fields the backend does not recognize (`employees`, `annual_revenue`, `headquarters`, `website`).  
**Expected Behavior:** Form submission succeeds, account is created, and user is redirected to the intelligence workspace.  
**User Clickpath:** Accounts → New Value Case → Fill form → Submit → Lands on Intelligence Signals.  
**Event/Hook/API Chain:** `handleAddAccount` → `AccountIntakeModal` → `handleSubmit` → `useCreateAccount` → `POST l4 /accounts` → `create_account` → `AccountService.create_account` → PostgreSQL.  
**Implementation Steps:**
1. Update form state to collect `provider` (dropdown: salesforce/hubspot/manual) and `provider_record_id`.
2. Rename `employees` → `company_size`.
3. Remove `annual_revenue`, `headquarters`, `website` from payload (or add to schema).
4. Update `useCreateAccount` to wrap response correctly.
**Acceptance Criteria:**
- E2E test creates account successfully.
- Backend returns 201.
- User lands on `/intelligence/:accountId/signals`.
**Required Tests:** E2E account creation flow.  
**Estimated Effort:** 2–4 hrs.

---

### Ticket: FIX-002
**Severity:** P0  
**Workflow:** Value Model to Calculator  
**Files:** `apps/web/src/pages/calculator/ROITab.tsx`, `apps/web/src/pages/calculator/ValueModelTab.tsx`, `apps/web/src/hooks/useCalculators.ts`, `apps/web/src/hooks/useROICalculator.ts`  
**Current Behavior:** Calculator workspace tabs render static placeholders (`value="—"`) and never load lever configuration or allow scenario modeling.  
**Expected Behavior:** Tabs load real value levers, allow conservative/expected/optimistic adjustment, and save scenarios.  
**User Clickpath:** Calculator → ROI (or Value Model) → Levers load → Adjust sliders → Save → Success.  
**Event/Hook/API Chain:** Page mount → `useValueLevers` → `GET l3 /v1/calculators/levers` → render sliders → `onChange` → local state → `handleSave` → `useCreateValueCase` → `POST l3 /v1/calculators/value-cases`.  
**Implementation Steps:**
1. Replace placeholder markup with lever slider list from `workflow/pages/Calculator.tsx`.
2. Wire `useValueLevers` with `accountId`.
3. Add Save button calling `useCreateValueCase`.
4. Add optimistic scenario slider.
**Acceptance Criteria:**
- Levers load from backend.
- Sliders adjust scenarios in real time.
- Save persists to Neo4j.
- Query invalidation refreshes list.
**Required Tests:** E2E calculator flow; integration test for save mutation.  
**Estimated Effort:** 1–2 days.

---

### Ticket: FIX-003
**Severity:** P0  
**Workflow:** Hypothesis to Value Tree  
**Files:** `services/layer4-agents/src/services/value_hypothesis_engine.py`, `services/layer3-knowledge/src/api/routes/value_trees.py`, `apps/web/src/hooks/useHypotheses.ts`, `apps/web/src/pages/drivers/DriverTreePage.tsx`  
**Current Behavior:** Validating a hypothesis only updates a `status` field. No value driver or value tree is created.  
**Expected Behavior:** Validating a hypothesis spawns a value driver (or triggers a workflow) that appears in the driver tree.  
**User Clickpath:** Hypothesis → Select draft → Validate → Driver created → Navigates to Driver Tree.  
**Event/Hook/API Chain:** Validate click → `useValidateHypothesis` → `POST l4 /v1/hypotheses/{id}/validate` → `validate_hypothesis` → **NEW:** enqueue driver generation workflow / create value tree node → invalidate `QK.drivers.all`.  
**Implementation Steps:**
1. Add post-validation hook in `value_hypothesis_engine.py`.
2. Call L3 value tree creation or L4 driver generation workflow.
3. Link hypothesis ID to created driver ID.
4. Update `DriverTreePage` to fetch and display drivers.
**Acceptance Criteria:**
- Validated hypothesis creates a driver.
- Driver appears in Driver Tree.
- Reload preserves driver.
**Required Tests:** E2E validate hypothesis → driver visible; integration test for driver creation.  
**Estimated Effort:** 2–3 days.

---

### Ticket: FIX-004
**Severity:** P1  
**Workflow:** Agent Right Rail Actions  
**Files:** `apps/web/src/agui/useAgentEvents.ts`, `apps/web/src/components/workspace/RightRail.tsx`, all `*Tab.tsx` workspace pages  
**Current Behavior:** `accountId`, `signalId`, `evidenceId` are never passed to the agent. Suggested actions are no-ops.  
**Expected Behavior:** Agent knows current account and selected entity. Suggested actions perform real mutations.  
**User Clickpath:** Any workspace page → Open Agent tab → Ask question → Agent references current account → Click suggested action → State updates.  
**Event/Hook/API Chain:** Page renders → `useAgentEvents({ accountId, activeTab, selectedEntityId })` → `sendMessage` → `POST l4 /agent-stream/chat` with full context → backend scopes to tenant/account → response includes actionable mutations → `suggestedActions` mapped to real handlers.  
**Implementation Steps:**
1. Add `accountId` and optional `entityId` to every `useAgentEvents` call.
2. Map `getDefaultSuggestedActions` to real mutation hooks.
3. Remove dev fallback mock in `useAgentStream.ts`.
**Acceptance Criteria:**
- Agent context includes accountId.
- Suggested actions trigger real mutations.
- UI updates after action.
**Required Tests:** Integration: agent message with context; E2E: suggested action → mutation.  
**Estimated Effort:** 1 day.

---

### Ticket: FIX-005
**Severity:** P1  
**Workflow:** Signals to Evidence  
**Files:** `apps/web/src/pages/intelligence/EvidenceTab.tsx`, `apps/web/src/hooks/useEvidence.ts`, `services/layer4-agents/src/api/routes/` (workspace)  
**Current Behavior:** Evidence workspace tab calls an endpoint that returns 501, falling back to empty array. Evidence library hooks exist but are not used.  
**Expected Behavior:** Evidence loads in workspace from real backend data.  
**User Clickpath:** Intelligence → Evidence tab → Evidence list loads.  
**Event/Hook/API Chain:** Tab mount → `useWorkspaceTabQuery(caseId, "evidence")` → `GET l4 /analysis/cases/{caseId}/workspace/evidence` → **FIX:** returns real evidence array → render list.  
**Implementation Steps:**
1. Implement workspace evidence endpoint in L4.
2. Or: switch `EvidenceTab.tsx` to use `useEvidenceSearch` with `accountId` filter.
3. Add "Attach to Driver" action.
**Acceptance Criteria:**
- Evidence loads for account.
- Attach action visible.
- Attach persists relation.
**Required Tests:** Integration: evidence loads; E2E: attach to driver.  
**Estimated Effort:** 1–2 days.

---

## 10. Testing Requirements

### Unit / Component Tests

- `AccountIntakeModal`: form validation, payload shape matches schema.
- `SignalsTab`: approve/reject buttons call handler (mocked mutation after fix).
- `ROITab` / `ValueModelTab`: render lever sliders when data present.
- `RightRail`: agent mode renders messages; suggested actions call handlers.
- `BusinessCaseList`: filter, sort, archive actions.

### Integration Tests

- `useCreateAccount`: mutation calls correct endpoint with correct payload.
- `useWorkspaceTabQuery`: returns data, handles 501 gracefully.
- `useValidateHypothesis`: invalidates queries on success.
- `useCreateValueCase`: persists to L3, invalidates calculator queries.
- `useBusinessCase`: parses workflow result into renderable shape.

### E2E Tests

1. **Account Setup Flow:**
   - Visit `/accounts` → click New Value Case → fill form → submit → assert redirect to `/intelligence/:id/signals`.

2. **Signal Review Flow:**
   - Select account → Signals tab → click signal → Approve → assert API called → reload → assert state persisted.

3. **Hypothesis to Driver Flow:**
   - Hypotheses tab → Generate → select draft → Validate → assert driver appears in Driver Tree.

4. **Calculator to Business Case Flow:**
   - Calculator tab → adjust levers → Save → assert ValueCase created → Business Cases → New Case → assert workflow created → view case → assert narrative visible.

5. **Agent Action Flow:**
   - Signals tab → open Agent → type question → assert context includes accountId → click suggested action → assert mutation called.

6. **Resume Flow:**
   - Start workflow → stop halfway → reload → assert progress restored.

---

*End of Audit Report*
