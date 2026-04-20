# Value Fabric — Refactored Navigation Model

**Based on:** Mental model of "Define → Build → Deliver → Prove"  
**Date:** April 20, 2026

---

## The Narrative Arc

This navigation tells a story:

1. **Context Engine** — *"What does the system know and how does it reason?"*
2. **Value Studio** — *"How do I create and prove value for this specific deal?"*
3. **Delivery Orchestrator** — *"How does value leave the system and create impact?"*
4. **Governance & Observability** — *"Can I trust this, and can I prove it?"*

---

## 1. Context Engine (Foundation Layer)

> The "data + meaning factory" — everything that feeds intelligence into the system.

### 1.1 Ontology & Schema
*The system's understanding of the world.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/context/ontology` | `OntologyEditor` | Advanced | Core schema, entity types, relationships |
| `/context/ontology/entities` | `EntityBrowser` | Advanced | Browse and manage entity instances |
| `/context/ontology/graph` | `GraphExplorer` | Advanced | **View** — graph visualization (not nav item) |

**Note:** Graph is infrastructure, not navigation. Accessible as a view *within* ontology.

### 1.2 Integrations & Sources
*How data enters the system.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/context/integrations` | `Integrations` | Admin | CRM connections (Salesforce, HubSpot) |
| `/context/sources` | `SourceConfiguration` | Admin | Data ingestion sources |
| `/context/ingestion/jobs` | `IngestionJobs` | Advanced | Monitor ingestion pipelines |
| `/context/extraction` | `ExtractionEngine` | Advanced | Text extraction from unstructured data |

### 1.3 Knowledge & Logic
*Canonical knowledge and reasoning rules.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/context/packs` | `ValuePacks` | All | Knowledge Packs (industry verticals) |
| `/context/models` | `MyModels` | All | Model library (reusable templates) |
| `/context/formulas` | `FormulaList` | Advanced | Canonical formulas (system logic) |
| `/context/formulas/:id` | `FormulaBuilder` | Advanced | Edit formula definitions |
| `/context/agents` | `AgentWorkflows` | Advanced | Agent configuration, capabilities, roles |

**Migration from current routes:**
- `/library/packs` → `/context/packs`
- `/library/models` → `/context/models`
- `/model/value-studio/formulas` → `/context/formulas`
- `/deliver/agents` → `/context/agents` (configuration mode)
- `/discover/knowledge/*` → `/context/ontology/*`
- `/discover/integrations` → `/context/integrations`
- `/discover/sources` → `/context/sources`
- `/discover/extraction` → `/context/extraction`

---

## 2. Value Studio (Core Workflow Layer)

> The heart of the product — a workspace for building value, not just viewing pages.

### 2.1 Deal Context
*Select and understand the customer.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/studio/deals` | `OpportunityFinder` | All | Browse opportunities/accounts |
| `/studio/deals/:id` | `Accounts` | All | Account detail & CRM data |
| `/studio/deals/:id/whitespace` | `WhitespaceAnalysis` | Advanced | Gap analysis for this account |

### 2.2 Value Construction
*Build the value argumentation.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/studio/build` | → `/studio/build/discovery` | Advanced | Entry to 6-stage pipeline |
| `/studio/build/discovery` | `Stage1Discovery` | Advanced | Stage 1: Discovery |
| `/studio/build/mapping` | `Stage2Mapping` | Advanced | Stage 2: Mapping |
| `/studio/build/modeling` | `Stage3Modeling` | Advanced | Stage 3: Modeling |
| `/studio/build/validation` | `Stage4Validation` | Advanced | Stage 4: Validation |
| `/studio/build/narrative` | `Stage5Narrative` | Advanced | Stage 5: Narrative |
| `/studio/build/tracking` | `Stage6Tracking` | Advanced | Stage 6: Tracking |

### 2.3 Value Exploration
*Navigate and refine the value model.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/studio/trees` | `ValueTreeExplorer` | Advanced | Browse value trees |
| `/studio/trees/:id` | `ValueTreeExplorer` | Advanced | Specific value tree view |
| `/studio/scenarios` | `InteractiveBusinessCase` | Advanced | Scenario modeling workspace |

**Migration from current routes:**
- `/discover/accounts` → `/studio/deals`
- `/discover/accounts/:id` → `/studio/deals/:id`
- `/deliver/whitespace` → `/studio/deals/:id/whitespace` (contextual)
- `/model/value-studio/*` → `/studio/build/*`
- `/model/value-studio/explorer` → `/studio/trees`
- `/deliver/cases/explore` → `/studio/scenarios`

---

## 3. Delivery Orchestrator (Activation Layer)

> Where value becomes usable and distributable — not just "reports."

### 3.1 Executive Outputs
*Board-ready artifacts.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/deliver/cases` | `BusinessCaseList` | All | Business case library |
| `/deliver/cases/:id` | `BusinessCase` | All | View specific business case |
| `/deliver/cases/:id/export` | `BusinessCase` | All | Export to PDF/PPT |

### 3.2 Interactive Tools
*Shareable, embeddable value calculators.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/deliver/calculators` | `InteractiveBusinessCase` | Advanced | ROI calculator builder |
| `/deliver/calculators/:id` | `InteractiveBusinessCase` | Advanced | Shareable calculator link |

### 3.3 API & Integration
*Value embedded into other systems.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/deliver/api` | `Integrations` | Admin | API endpoints & webhooks |
| `/deliver/embeds` | `Integrations` | Admin | Embeddable widgets |

### 3.4 Stakeholder Views
*Role-specific perspectives.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/deliver/views/cfo` | `BusinessCase` | All | CFO-focused dashboard |
| `/deliver/views/executive` | `BusinessCase` | All | Executive summary view |
| `/deliver/views/technical` | `BusinessCase` | All | Technical buyer view |

**Migration from current routes:**
- `/deliver/cases` (unchanged)
- `/deliver/cases/:caseId` (unchanged)
- `/deliver/opportunities` → `/studio/deals` (recontextualized)
- `/deliver/cases/explore` → `/studio/scenarios` AND `/deliver/calculators`

---

## 4. Governance & Observability (Trust Layer)

> CFO-defensible outputs require transparent, auditable systems.

### 4.1 Assumption Traceability
*Evidence lineage for every claim.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/trust/lineage/:entityId` | `DecisionTrace` | Advanced | Data lineage for assumptions |
| `/trust/evidence` | `DecisionTrace` | All | Evidence repository |
| `/trust/provenance` | `DecisionTrace` | Advanced | Full provenance trails |

### 4.2 Agent Reasoning
*Understand how AI reached conclusions.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/trust/reasoning/:workflowId` | `DecisionTrace` | Advanced | Agent reasoning traces |
| `/trust/traces` | `DecisionTrace` | All | Decision trace library |

### 4.3 Audit & Compliance
*Who changed what, when.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/trust/audit/log` | `DecisionTrace` | Admin | Complete audit log |
| `/trust/audit/changes` | `DecisionTrace` | Admin | Change history |
| `/trust/compliance` | `DecisionTrace` | Advanced | Compliance reports |

### 4.4 System Integrity
*Confidence scoring and health.*

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/trust/health` | `HealthMonitor` | Admin | System health dashboard |
| `/trust/integrity` | `DecisionTrace` | Advanced | Confidence scoring |
| `/trust/benchmarks` | `BenchmarkPolicies` | Admin | Benchmark policies |

**Migration from current routes:**
- `/evidence/traces` → `/trust/traces`
- `/evidence/lineage` → `/trust/lineage/:entityId`
- `/evidence/compliance` → `/trust/compliance`
- `/evidence/changelog` → `/trust/audit/changes`
- `/admin/system/health` → `/trust/health`
- `/admin/content/benchmarks` → `/trust/benchmarks`
- `/admin/system/audit` → `/trust/audit/log`

---

## 5. Administration (Control Plane)

> System-level configuration (separated from operational workflows).

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/admin/content/formulas` | `FormulaGovernance` | Admin | Formula governance |
| `/admin/content/versions` | `FormulaGovernance` | Admin | Version management |
| `/admin/content/approvals` | `FormulaGovernance` | Admin | Approval workflows |
| `/admin/data/variables` | `VariableRegistry` | Admin | Variable registry |
| `/admin/data/bindings` | `VariableRegistry` | Admin | Data bindings |
| `/admin/data/quality` | `VariableRegistry` | Admin | Data quality rules |
| `/admin/access/roles` | `PermissionsAdmin` | Admin | Role management |
| `/admin/access/teams` | `PermissionsAdmin` | Admin | Team management |
| `/admin/access/keys` | `PermissionsAdmin` | Admin | API key management |
| `/admin/system/settings` | `PlatformSettings` | Admin | Platform settings |

**Note:** Administration is distinct from Governance. Admin = system config. Governance = operational trust.

---

## Public & Utility Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `LandingPage` | Marketing page (unauthenticated) |
| `/login` | `Login` | Authentication |
| `/login/callback` | `Login` | OIDC callback |
| `/home` | `ValueNarrativeHome` | Personal dashboard (post-login) |
| `*` | `NotFound` | 404 page |

---

## Structural Comparison

### Before (Section-Based)

```
HOME
LIBRARY (packs, models, authoring)
DISCOVER (accounts, jobs, extraction, knowledge, integrations, sources)
MODEL (value-studio 6-stage, formulas, trees)
DELIVER (cases, opportunities, whitespace, agents, calculators)
EVIDENCE (traces, export, lineage, compliance, changelog)
ADMIN (content, data, access, system)
```

### After (Narrative-Based)

```
HOME
CONTEXT ENGINE (ontology, integrations, sources, packs, models, formulas, agents)
VALUE STUDIO (deals, 6-stage build, trees, scenarios)
DELIVERY ORCHESTRATOR (cases, calculators, APIs, stakeholder views)
GOVERNANCE & TRUST (lineage, reasoning, audit, compliance, health)
ADMIN (content, data, access, system)
```

---

## Implementation Notes

### Phase 1: Soft Launch (Redirects)
- Keep old routes active
- Add redirects to new structure
- Update navigation UI

### Phase 2: Hard Cutover
- Remove old routes
- Update bookmarks/documentation

### Key Redirects Required

| Old Route | New Route |
|-----------|-----------|
| `/library/packs` | `/context/packs` |
| `/library/models` | `/context/models` |
| `/discover/knowledge/entities` | `/context/ontology/entities` |
| `/discover/knowledge/ontology` | `/context/ontology` |
| `/discover/knowledge/graph` | `/context/ontology/graph` |
| `/discover/integrations` | `/context/integrations` |
| `/discover/sources` | `/context/sources` |
| `/discover/jobs` | `/context/ingestion/jobs` |
| `/discover/extraction` | `/context/extraction` |
| `/discover/accounts` | `/studio/deals` |
| `/model/value-studio/*` | `/studio/build/*` |
| `/model/value-studio/explorer` | `/studio/trees` |
| `/model/value-studio/formulas` | `/context/formulas` |
| `/deliver/whitespace` | `/studio/deals/:id/whitespace` |
| `/deliver/agents` | `/context/agents` |
| `/deliver/cases/explore` | `/studio/scenarios` |
| `/evidence/traces` | `/trust/traces` |
| `/evidence/lineage` | `/trust/lineage` |
| `/evidence/compliance` | `/trust/compliance` |
| `/evidence/changelog` | `/trust/audit/changes` |
| `/admin/system/health` | `/trust/health` |
| `/admin/content/benchmarks` | `/trust/benchmarks` |

---

## Tier Access Matrix (New Structure)

| Section | Route Pattern | Standard | Advanced | Admin |
|---------|---------------|----------|----------|-------|
| **Context Engine** | `/context/packs` | ✅ | ✅ | ✅ |
| | `/context/models` | ✅ | ✅ | ✅ |
| | `/context/ontology` | ❌ | ✅ | ✅ |
| | `/context/ontology/entities` | ❌ | ✅ | ✅ |
| | `/context/integrations` | ❌ | ❌ | ✅ |
| | `/context/sources` | ❌ | ❌ | ✅ |
| | `/context/ingestion/jobs` | ❌ | ✅ | ✅ |
| | `/context/extraction` | ❌ | ✅ | ✅ |
| | `/context/formulas` | ❌ | ✅ | ✅ |
| | `/context/agents` | ❌ | ✅ | ✅ |
| **Value Studio** | `/studio/deals` | ✅ | ✅ | ✅ |
| | `/studio/deals/:id/*` | ✅ | ✅ | ✅ |
| | `/studio/build/*` | ❌ | ✅ | ✅ |
| | `/studio/trees` | ❌ | ✅ | ✅ |
| | `/studio/scenarios` | ❌ | ✅ | ✅ |
| **Delivery** | `/deliver/cases` | ✅ | ✅ | ✅ |
| | `/deliver/cases/:id` | ✅ | ✅ | ✅ |
| | `/deliver/calculators` | ❌ | ✅ | ✅ |
| | `/deliver/api` | ❌ | ❌ | ✅ |
| **Governance** | `/trust/traces` | ✅ | ✅ | ✅ |
| | `/trust/evidence` | ✅ | ✅ | ✅ |
| | `/trust/lineage/*` | ❌ | ✅ | ✅ |
| | `/trust/reasoning/*` | ❌ | ✅ | ✅ |
| | `/trust/compliance` | ❌ | ✅ | ✅ |
| | `/trust/audit/*` | ❌ | ❌ | ✅ |
| | `/trust/health` | ❌ | ❌ | ✅ |
| | `/trust/benchmarks` | ❌ | ❌ | ✅ |
| **Admin** | `/admin/*` | ❌ | ❌ | ✅ |

---

## Backend API Alignment

This navigation aligns with your architecture:

| Nav Layer | Backend Services |
|-----------|----------------|
| **Context Engine** | Layer 1 (Ingestion) + Layer 2 (Extraction/Ontology) + Layer 3 (Schema) |
| **Value Studio** | Layer 3 (Value Trees, Formulas, Graph) + Layer 4 (Workflows) |
| **Delivery** | Layer 3 (Export) + Layer 4 (Cases, Analysis) + SDUI |
| **Governance** | Layer 4 (Integrity, Audit) + Layer 5 (Ground Truth) |

---

## The Story Your Navigation Tells

When a user logs in, they navigate through a clear narrative:

1. **"What does the system know?"** → Context Engine
2. **"How do I build value?"** → Value Studio  
3. **"How do I deliver impact?"** → Delivery Orchestrator
4. **"Can I trust this?"** → Governance & Observability

This structure prevents the common failure mode of mixing *system configuration* with *user workflows*. The Context Engine is about knowledge, not settings. The Value Studio is about creation, not administration. The separation is clean and intuitive.
