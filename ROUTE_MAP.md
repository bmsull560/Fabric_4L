# Value Fabric Route Map

**Generated:** April 20, 2026  
**Repository:** Fabric_4L

---

## Table of Contents

1. [Frontend Routes](#frontend-routes)
2. [Layer 1: Ingestion API](#layer-1-ingestion-api)
3. [Layer 2: Extraction API](#layer-2-extraction-api)
4. [Layer 3: Knowledge API](#layer-3-knowledge-api)
5. [Layer 4: Agents API](#layer-4-agents-api)
6. [Tier-Based Access Matrix](#tier-based-access-matrix)

---

## Frontend Routes

### Public Routes (Unauthenticated)

| Route | Component | Description |
|-------|-----------|-------------|
| `/` | `LandingPage` | Marketing/landing page |
| `/login` | `Login` | Authentication page |
| `/login/callback` | `Login` | OIDC callback handler |

### Authenticated Routes (Inside AppShell)

#### HOME Section (All Tiers)

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/home` | `ValueNarrativeHome` | All | Dashboard home page |

#### LIBRARY Section (Content Catalog)

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/library` | → `/library/packs` | All | Redirect to packs |
| `/library/packs` | `ValuePacks` | All | Value packs browser |
| `/library/models` | `MyModels` | All | Model library |
| `/library/authoring` | `PackManagement` | Admin | Pack authoring tools |

#### DISCOVER Section (Research & Data)

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/discover` | → `/discover/accounts` | All | Redirect to accounts |
| `/discover/accounts` | `Accounts` | All | CRM accounts browser |
| `/discover/accounts/:id` | `Accounts` | All | Account detail view |
| `/discover/jobs` | `IngestionJobs` | All | Ingestion job monitor |
| `/discover/extraction` | `ExtractionEngine` | Advanced | Text extraction UI |

**Knowledge Model (Tier 2+)**

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/discover/knowledge` | → `/discover/knowledge/entities` | Advanced | Redirect to entities |
| `/discover/knowledge/entities` | `EntityBrowser` | Advanced | Entity browser |
| `/discover/knowledge/graph` | `GraphExplorer` | Advanced | Graph visualization |
| `/discover/knowledge/ontology` | `OntologyEditor` | Advanced | Ontology editor |

**Admin (Tier 3)**

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/discover/integrations` | `Integrations` | Admin | Integration management |
| `/discover/sources` | `SourceConfiguration` | Admin | Source configuration |

#### MODEL Section (Value Studio - Tier 2+)

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/model` | → `/model/value-studio/explorer` | Advanced | Redirect to explorer |
| `/model/value-studio` | → `/model/value-studio/discovery` | Advanced | Redirect to discovery |

**6-Stage Pipeline**

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/model/value-studio/discovery` | `Stage1Discovery` | Advanced | Stage 1: Discovery |
| `/model/value-studio/mapping` | `Stage2Mapping` | Advanced | Stage 2: Mapping |
| `/model/value-studio/modeling` | `Stage3Modeling` | Advanced | Stage 3: Modeling |
| `/model/value-studio/validation` | `Stage4Validation` | Advanced | Stage 4: Validation |
| `/model/value-studio/narrative` | `Stage5Narrative` | Advanced | Stage 5: Narrative |
| `/model/value-studio/tracking` | `Stage6Tracking` | Advanced | Stage 6: Tracking |
| `/model/value-studio/explorer` | `ValueTreeExplorer` | Advanced | Value tree explorer |
| `/model/value-studio/normalization` | `ValueTreeExplorer` | Advanced | Normalization view |
| `/model/value-studio/formulas` | `FormulaList` | Advanced | Formula list |
| `/model/value-studio/formulas/new` | `FormulaBuilder` | Advanced | Create new formula |
| `/model/value-studio/formulas/:formulaId` | `FormulaBuilder` | Advanced | Edit formula |

#### DELIVER Section (Output & Workflows)

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/deliver` | → `/deliver/cases` | All | Redirect to cases |
| `/deliver/cases` | `BusinessCaseList` | All | Business case list |
| `/deliver/cases/:caseId` | `BusinessCase` | All | Business case detail |
| `/deliver/opportunities` | `OpportunityFinder` | All | Opportunity finder |
| `/deliver/whitespace` | `WhitespaceAnalysis` | Advanced | Whitespace analysis |
| `/deliver/agents` | `AgentWorkflows` | Advanced | Agent workflows |
| `/deliver/cases/explore` | `InteractiveBusinessCase` | Advanced | Interactive case builder |

#### EVIDENCE Section (Audit & Provenance)

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/evidence` | → `/evidence/traces` | All | Redirect to traces |
| `/evidence/traces` | `DecisionTrace` | All | Decision traces |
| `/evidence/export` | `DecisionTrace` | All | Export evidence |
| `/evidence/lineage` | `DecisionTrace` | Advanced | Data lineage |
| `/evidence/compliance` | `DecisionTrace` | Advanced | Compliance view |
| `/evidence/changelog` | `DecisionTrace` | Admin | Change log |

#### GOVERN Section (Admin Control Plane - Tier 3)

| Route | Component | Tier | Description |
|-------|-----------|------|-------------|
| `/admin` | → `/admin/content/formulas` | Admin | Admin home |

**Content Management**

| Route | Component | Description |
|-------|-----------|-------------|
| `/admin/content` | → `/admin/content/formulas` | Redirect to formulas |
| `/admin/content/formulas` | `FormulaGovernance` | Formula governance |
| `/admin/content/versions` | `FormulaGovernance` | Version management |
| `/admin/content/approvals` | `FormulaGovernance` | Approval workflows |
| `/admin/content/benchmarks` | `BenchmarkPolicies` | Benchmark policies |

**Data Management**

| Route | Component | Description |
|-------|-----------|-------------|
| `/admin/data` | → `/admin/data/variables` | Redirect to variables |
| `/admin/data/variables` | `VariableRegistry` | Variable registry |
| `/admin/data/bindings` | `VariableRegistry` | Data bindings |
| `/admin/data/quality` | `VariableRegistry` | Data quality |

**Access Control**

| Route | Component | Description |
|-------|-----------|-------------|
| `/admin/access` | → `/admin/access/roles` | Redirect to roles |
| `/admin/access/roles` | `PermissionsAdmin` | Role management |
| `/admin/access/teams` | `PermissionsAdmin` | Team management |
| `/admin/access/keys` | `PermissionsAdmin` | API keys |

**System**

| Route | Component | Description |
|-------|-----------|-------------|
| `/admin/system` | → `/admin/system/settings` | Redirect to settings |
| `/admin/system/settings` | `PlatformSettings` | Platform settings |
| `/admin/system/audit` | `DecisionTrace` | System audit |
| `/admin/system/health` | `HealthMonitor` | Health monitoring |

### Error Routes

| Route | Component | Description |
|-------|-----------|-------------|
| `*` (catch-all) | `NotFound` | 404 page |

---

## Layer 1: Ingestion API

Base: `/api/v1/ingestion`

### Targets

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ingestion/targets` | List scraping targets |
| POST | `/api/v1/ingestion/targets` | Create target |
| GET | `/api/v1/ingestion/targets/{target_id}` | Get target details |
| PUT | `/api/v1/ingestion/targets/{target_id}` | Update target |
| DELETE | `/api/v1/ingestion/targets/{target_id}` | Archive target |
| POST | `/api/v1/ingestion/targets/{target_id}/validate` | Validate target config |
| POST | `/api/v1/ingestion/targets/{target_id}/execute` | Execute target |
| GET | `/api/v1/ingestion/targets/{target_id}/decisions` | Get crawl decisions |

### Jobs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ingestion/jobs` | List jobs |
| GET | `/api/v1/ingestion/jobs/{job_id}` | Get job details |
| DELETE | `/api/v1/ingestion/jobs/{job_id}` | Cancel job |
| GET | `/api/v1/ingestion/jobs/{job_id}/progress` | Get job progress |
| GET | `/api/v1/ingestion/jobs/{job_id}/results` | Get job results |
| POST | `/api/v1/ingestion/jobs/{job_id}/retry` | Retry job |
| GET | `/api/v1/ingestion/jobs/{job_id}/router-report` | Get router report |

### Content & Domains

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/ingestion/content/raw/{content_id}` | Get raw content |
| GET | `/api/v1/ingestion/domains/{domain}/fallback-stats` | Get fallback stats |

---

## Layer 2: Extraction API

Base: `/v1`

### System

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Metrics endpoint |

### Extraction

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/extract` | Extract entities from text |
| POST | `/v1/extract-and-ingest` | Extract and ingest to L3 |
| GET | `/v1/extract/status/{job_id}` | Get extraction status |
| POST | `/v1/extract/batch` | Batch extraction |
| GET | `/v1/extract/jobs/{job_id}/events` | Stream job events (SSE) |

### Ontology

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/ontology/entities` | List entities |
| GET | `/v1/ontology/relationships/{entity_id}` | Get entity relationships |
| GET | `/v1/ontology/schema` | Get ontology schema |
| POST | `/v1/ontology/schema/validate` | Validate schema |
| POST | `/v1/ontology/schema/publish` | Publish schema version |
| POST | `/v1/ontology/schema/import` | Import schema |
| GET | `/v1/ontology/schema/export` | Export schema |
| GET | `/v1/ontology/schema/types` | List ontology types |
| POST | `/v1/ontology/schema/types` | Create type |
| GET | `/v1/ontology/schema/types/{type_id}` | Get type |
| PUT | `/v1/ontology/schema/types/{type_id}` | Update type |
| DELETE | `/v1/ontology/schema/types/{type_id}` | Delete type |
| POST | `/v1/ontology/schema/types/{type_id}/properties` | Add property |
| PUT | `/v1/ontology/schema/types/{type_id}/properties/{property_id}` | Update property |
| DELETE | `/v1/ontology/schema/types/{type_id}/properties/{property_id}` | Remove property |
| GET | `/v1/ontology/schema/relationships` | List type relationships |
| POST | `/v1/ontology/schema/relationships` | Create relationship |
| DELETE | `/v1/ontology/schema/relationships/{relationship_id}` | Delete relationship |
| GET | `/v1/ontology/schema/versions` | List schema versions |
| GET | `/v1/ontology/schema/versions/{version}` | Get schema version |

### Audit

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/audit/trace/{job_id}` | Get provenance trace |

---

## Layer 3: Knowledge API

Base: `/v1` (and various prefixes)

### System & Health

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/health/detailed` | Detailed health status |

### Graph API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/graph` | Get full graph |
| GET | `/v1/graph/stats` | Graph statistics |
| GET | `/v1/graph/subgraph` | Get subgraph (query or center mode) |

### Entity API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/entities` | List entities (paginated) |
| GET | `/v1/entities/{entity_id}` | Get entity detail |
| POST | `/v1/entities` | Create entity |
| PUT | `/v1/entities/{entity_id}` | Update entity |
| DELETE | `/v1/entities/{entity_id}` | Delete entity |
| GET | `/v1/entities/{entity_id}/context` | Get entity context |
| POST | `/v1/entities/batch` | Batch entity operations |

### Search API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/search` | Semantic search |
| POST | `/v1/search/hybrid` | Hybrid (semantic + keyword) search |
| GET | `/v1/search/suggestions` | Search suggestions |

### Graph RAG

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/graph-rag/query` | Graph RAG query |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/analysis/centrality` | Centrality analysis |
| POST | `/v1/analysis/communities` | Community detection |
| POST | `/v1/analysis/similarity` | Similarity analysis |

### Value Trees & Formulas

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/value-trees/{entity_id}` | Get value tree |
| GET | `/v1/value-trees/{entity_id}/paths` | Get value tree paths |
| GET | `/v1/formulas` | List formulas |
| GET | `/v1/formulas/{formula_id}` | Get formula |
| POST | `/v1/formulas/evaluate` | Evaluate formula |
| GET | `/v1/formulas/variables` | List formula variables |

### Formula Governance

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/formulas/{formula_id}/validate` | Validate formula |
| POST | `/v1/formulas/{formula_id}/submit` | Submit formula for approval |
| GET | `/v1/formulas/{formula_id}/versions` | Get formula versions |

### Benchmarks

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/benchmarks` | List benchmarks |
| GET | `/v1/benchmarks/{benchmark_id}` | Get benchmark |
| GET | `/v1/benchmark-policies` | List benchmark policies |
| PUT | `/v1/benchmark-policies/{policy_id}` | Update policy |

### Value Packs

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/value-packs` | List value packs |
| GET | `/v1/value-packs/{pack_id}` | Get value pack |
| POST | `/v1/value-packs/{pack_id}/apply` | Apply value pack |

### Sync & Export

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/sync/status` | Sync status |
| POST | `/v1/sync/trigger` | Trigger sync |
| POST | `/v1/export/document` | Export document |

### Audit & Provenance

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/audit/provenance/{entity_id}` | Get provenance |
| GET | `/v1/audit/log` | Audit log |

---

## Layer 4: Agents API

Base: `/v1`

### Workflows

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/workflows` | Create workflow |
| GET | `/v1/workflows/{workflow_id}` | Get workflow status |
| DELETE | `/v1/workflows/{workflow_id}` | Cancel workflow |
| GET | `/v1/workflows/{workflow_id}/result` | Get workflow result |
| POST | `/v1/workflows/{workflow_id}/resume` | Resume workflow |
| POST | `/v1/workflows/{workflow_id}/pause` | Pause workflow |
| GET | `/v1/workflows/types` | List workflow types |
| GET | `/v1/workflows/active` | List active workflows |
| GET | `/v1/workflows/{workflow_id}/events` | Workflow events (SSE) |

### Tools

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/tools` | List tools |
| GET | `/v1/tools/{tool_name}` | Get tool schema |
| POST | `/v1/tools/invoke` | Invoke tool |
| POST | `/v1/tools/export-document` | Export document |
| GET | `/v1/tools/categories` | List tool categories |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/analysis/roi` | Quick ROI analysis |
| POST | `/v1/analysis/whitespace` | Whitespace analysis |

### Business Cases

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/cases` | Generate business case |
| GET | `/v1/cases/{case_id}` | Get business case |
| GET | `/v1/cases/{case_id}/export` | Export business case |

### Accounts

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/accounts` | List accounts |
| POST | `/v1/accounts` | Create account |
| GET | `/v1/accounts/{account_id}` | Get account |
| PUT | `/v1/accounts/{account_id}` | Update account |
| DELETE | `/v1/accounts/{account_id}` | Delete account |
| GET | `/v1/accounts/filter-options` | Get filter options |
| POST | `/v1/accounts/{account_id}/sync` | Sync account |
| GET | `/v1/accounts/{account_id}/sync-status` | Get sync status |

### Billing

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/billing/usage` | Get usage |
| GET | `/v1/billing/invoices` | List invoices |
| GET | `/v1/billing/credits` | Get credits |
| POST | `/v1/billing/checkout` | Create checkout |
| GET | `/v1/billing/pricing` | Get pricing |

### Integrations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/integrations` | List integrations |
| POST | `/v1/integrations` | Create integration |
| GET | `/v1/integrations/{integration_id}` | Get integration |
| DELETE | `/v1/integrations/{integration_id}` | Delete integration |
| POST | `/v1/integrations/{integration_id}/test` | Test integration |

### Checkpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/v1/checkpoints/{workflow_id}` | List checkpoints |
| GET | `/v1/checkpoints/{workflow_id}/latest` | Get latest checkpoint |
| POST | `/v1/checkpoints/{workflow_id}/restore` | Restore checkpoint |
| DELETE | `/v1/checkpoints/{workflow_id}` | Delete checkpoints |

### CRM Webhooks

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/webhooks/crm/{provider}` | Receive CRM webhook |
| GET | `/v1/webhooks/crm/{provider}/verify` | Verify webhook |

---

## Tier-Based Access Matrix

| Route | Standard | Advanced | Admin |
|-------|----------|----------|-------|
| `/home` | ✅ | ✅ | ✅ |
| `/library/packs` | ✅ | ✅ | ✅ |
| `/library/models` | ✅ | ✅ | ✅ |
| `/library/authoring` | ❌ | ❌ | ✅ |
| `/discover/accounts` | ✅ | ✅ | ✅ |
| `/discover/jobs` | ✅ | ✅ | ✅ |
| `/discover/extraction` | ❌ | ✅ | ✅ |
| `/discover/knowledge/*` | ❌ | ✅ | ✅ |
| `/discover/integrations` | ❌ | ❌ | ✅ |
| `/discover/sources` | ❌ | ❌ | ✅ |
| `/model/value-studio/*` | ❌ | ✅ | ✅ |
| `/deliver/cases` | ✅ | ✅ | ✅ |
| `/deliver/opportunities` | ✅ | ✅ | ✅ |
| `/deliver/whitespace` | ❌ | ✅ | ✅ |
| `/deliver/agents` | ❌ | ✅ | ✅ |
| `/deliver/cases/explore` | ❌ | ✅ | ✅ |
| `/evidence/traces` | ✅ | ✅ | ✅ |
| `/evidence/export` | ✅ | ✅ | ✅ |
| `/evidence/lineage` | ❌ | ✅ | ✅ |
| `/evidence/compliance` | ❌ | ✅ | ✅ |
| `/evidence/changelog` | ❌ | ❌ | ✅ |
| `/admin/*` | ❌ | ❌ | ✅ |

### Tier Hierarchy

```
Admin > Advanced > Standard
```

- **Standard**: Basic content access, business cases, opportunities
- **Advanced**: + Knowledge model, value studio, agents, lineage
- **Admin**: + Governance, authoring, system configuration

---

## Layer Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (React)                         │
│              Route-based code-splitting                     │
│              Tier-based access control                      │
├─────────────────────────────────────────────────────────────┤
│  Layer 1 (Ingestion) │ Layer 2 (Extraction)                 │
│  - /api/v1/ingestion │ - /v1/extract*                       │
│  - Targets, Jobs     │ - Ontology schema                    │
├─────────────────────────────────────────────────────────────┤
│  Layer 3 (Knowledge)                                        │
│  - /v1/graph*, /v1/entities*                                │
│  - /v1/search*, /v1/value-trees*                          │
│  - /v1/formulas*, /v1/benchmarks*                         │
├─────────────────────────────────────────────────────────────┤
│  Layer 4 (Agents)                                           │
│  - /v1/workflows*, /v1/tools*                             │
│  - /v1/accounts*, /v1/billing*                            │
│  - /v1/analysis*, /v1/cases*                              │
└─────────────────────────────────────────────────────────────┘
```

---

**Legend:**
- ✅ = Accessible
- ❌ = Not accessible (redirects to `/home`)
- → = Redirect
- `:param` = Dynamic route parameter
