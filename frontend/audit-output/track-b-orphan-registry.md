# Track B: API Archaeology — Orphan Endpoint Registry

## Executive Summary

**Total Backend Endpoints:** 244
**Connected (have frontend hooks):** 8
**Orphan (no frontend surface):** 236
**Orphan Rate:** 96.7%

## Orphan Rate by Layer

| Layer | Total | Connected | Orphan | Orphan Rate |
|-------|-------|-----------|--------|-------------|
| layer1-ingestion     |    26 |         0 |     26 |      100.0% |
| layer2-extraction    |    29 |         7 |     22 |       75.9% |
| layer3-knowledge     |    89 |         1 |     88 |       98.9% |
| layer4-agents        |    84 |         0 |     84 |      100.0% |
| layer5-ground-truth  |    13 |         0 |     13 |      100.0% |
| signals              |     3 |         0 |      3 |      100.0% |

## Top Orphaned Domain Entities (by Tag)

| Domain/Tag | Orphan Endpoints | Potential Frontend Surface |
|------------|------------------|---------------------------|
| Accounts             |               16 | Accounts.tsx, CRM integration pages |
| ontology             |               14 | OntologyEditor.tsx, EntityBrowser.tsx |
| ground-truth         |               13 | DecisionTrace.tsx, Governance pages |
| state-inspector      |               12 | HealthMonitor.tsx |
| health               |               12 | HealthMonitor.tsx |
| ValuePacks           |                9 | ValuePacks.tsx |
| workflows            |                9 | AgentWorkflows.tsx |
| checkpoints          |                8 | AgentWorkflows.tsx |
| Model Registry       |                7 | MyModels.tsx |
| Integrations         |                6 | Integrations.tsx |
| Formulas             |                5 | FormulaBuilder.tsx, FormulaList.tsx |
| Models               |                5 | MyModels.tsx |
| tools                |                5 | Unknown |
| analysis             |                5 | Unknown |
| Tenants              |                5 | PlatformSettings.tsx (admin) |
| Users                |                5 | PermissionsAdmin.tsx |
| Feature Flags        |                5 | PlatformSettings.tsx |
| extraction           |                4 | ExtractionEngine.tsx |
| system               |                3 | PlatformSettings.tsx |
| Graph                |                3 | GraphExplorer.tsx |
| CRM Webhooks         |                3 | Unknown |
| API Keys             |                3 | PermissionsAdmin.tsx |
| OIDC SSO             |                3 | Unknown |
| audit                |                2 | Unknown |
| Value Trees          |                2 | ValueTreeExplorer.tsx |

## Critical Orphan Endpoints (High-Value, No Surface)

These endpoints should power existing pages but have no frontend implementation:

### Accounts

| Method | Path | Summary |
|--------|------|---------|
| GET    | `/v1/accounts                                      ` | List Accounts |
| GET    | `/v1/accounts                                      ` | List Accounts |
| GET    | `/v1/accounts/filters                              ` | Get Filter Options |
| GET    | `/v1/accounts/filters                              ` | Get Filter Options |
| POST   | `/v1/accounts/search                               ` | Search Accounts |
| POST   | `/v1/accounts/search                               ` | Search Accounts |
| POST   | `/v1/accounts/sync                                 ` | Sync Accounts |
| POST   | `/v1/accounts/sync                                 ` | Sync Accounts |
| GET    | `/v1/accounts/sync-status                          ` | Get Sync Status All |
| GET    | `/v1/accounts/sync-status                          ` | Get Sync Status All |
| ... | *6 more endpoints* | |

### ontology

| Method | Path | Summary |
|--------|------|---------|
| GET    | `/v1/ontology/entities                             ` | List Entities |
| GET    | `/v1/ontology/relationships/{entity_id}            ` | Get Relationships |
| GET    | `/v1/ontology/schema/export                        ` | Export Ontology Schema |
| GET    | `/v1/ontology/schema/relationships                 ` | List Type Relationships |
| DELETE | `/v1/ontology/schema/relationships/{relationship_id...` | Delete Type Relationship |
| GET    | `/v1/ontology/schema/types                         ` | List Ontology Types |
| GET    | `/v1/ontology/schema/types/{type_id}               ` | Get Ontology Type |
| PUT    | `/v1/ontology/schema/types/{type_id}               ` | Update Ontology Type |
| DELETE | `/v1/ontology/schema/types/{type_id}               ` | Delete Ontology Type |
| POST   | `/v1/ontology/schema/types/{type_id}/properties    ` | Add Type Property |
| ... | *4 more endpoints* | |

### workflows

| Method | Path | Summary |
|--------|------|---------|
| POST   | `/v1/workflows                                     ` | Create Workflow |
| GET    | `/v1/workflows/active                              ` | List Active Workflows |
| GET    | `/v1/workflows/types                               ` | List Available Workflows |
| GET    | `/v1/workflows/{workflow_id}                       ` | Get Workflow Status |
| DELETE | `/v1/workflows/{workflow_id}                       ` | Cancel Workflow |
| GET    | `/v1/workflows/{workflow_id}/events                ` | Get Workflow Events |
| POST   | `/v1/workflows/{workflow_id}/pause                 ` | Pause Workflow |
| GET    | `/v1/workflows/{workflow_id}/result                ` | Get Workflow Result |
| POST   | `/v1/workflows/{workflow_id}/resume                ` | Resume Workflow |

### ValuePacks

| Method | Path | Summary |
|--------|------|---------|
| GET    | `/v1/valuepacks                                    ` | List ValuePacks |
| POST   | `/v1/valuepacks                                    ` | Create ValuePack |
| POST   | `/v1/valuepacks/compare                            ` | Compare ValuePacks |
| GET    | `/v1/valuepacks/composable-templates               ` | Get Composable Templates |
| GET    | `/v1/valuepacks/ontology-map                       ` | Get Ontology Map |
| GET    | `/v1/valuepacks/{industry_id}                      ` | Get ValuePack |
| PUT    | `/v1/valuepacks/{industry_id}                      ` | Update ValuePack |
| DELETE | `/v1/valuepacks/{industry_id}                      ` | Delete ValuePack |
| POST   | `/v1/valuepacks/{industry_id}/seed                 ` | Seed ValuePack Data |

### Formulas

| Method | Path | Summary |
|--------|------|---------|
| GET    | `/v1/formulas                                      ` | List Registered Formulas |
| POST   | `/v1/formulas/evaluate                             ` | Evaluate Formula |
| POST   | `/v1/formulas/scenario                             ` | Calculate What-If Scenario |
| GET    | `/v1/formulas/variables                            ` | Get Variables Registry |
| GET    | `/v1/formulas/{formula_id}                         ` | Get Formula Details |

### Graph

| Method | Path | Summary |
|--------|------|---------|
| GET    | `/entities/{entity_id}/subgraph                    ` | Get Entity Subgraph |
| GET    | `/graph                                            ` | Get Full Graph |
| GET    | `/v1/graph/subgraph                                ` | Get Query-Based Subgraph |

### Value Trees

| Method | Path | Summary |
|--------|------|---------|
| GET    | `/v1/value-trees/{entity_id}                       ` | Get Value Tree |
| GET    | `/v1/value-trees/{entity_id}/paths                 ` | Get Value Tree Paths |


## Recommendations

### Priority 1: Core Functionality
1. **Accounts/CRM Integration** - 16 orphan endpoints for account management
2. **Workflow Checkpoints** - 8 orphan endpoints for agent checkpoint/resume
3. **Health Monitoring** - 12 orphan endpoints for system health

### Priority 2: Knowledge Layer
1. **Ontology Management** - 14 orphan endpoints for ontology CRUD
2. **Graph Context** - Entity context endpoints for GraphExplorer
3. **Value Trees** - Path traversal endpoints for ValueTreeExplorer

### Priority 3: Platform
1. **Tenant Management** - 5 orphan endpoints for multi-tenant admin
2. **User/Permission** - 5+ orphan endpoints for access control
3. **Ground Truth** - 13 orphan endpoints for evaluation/evidence