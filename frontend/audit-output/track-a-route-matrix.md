# Track A: Route Integrity Matrix

## Executive Summary

**Total Routes Analyzed:** 154

### Data Source Distribution

| Color | Status | Count | Percentage |
|-------|--------|-------|------------|
| **GREEN** | Live backend integration | 16 | 10.4% |
| **YELLOW** | Generic endpoint passthrough | 0 | 0.0% |
| **RED** | Hardcoded mock/orphaned | 51 | 33.1% |
| **REDIRECT** | Legacy redirects | 70 | 45.5% |
| **UNKNOWN** | Unknown/unevaluated | 17 | 11.0% |

### Facade Problem: 81.0%

**68** of **84** authenticated routes are non-functional facades (render hardcoded data, mocks, or have no backend integration).

## Route Detail by Category

### GREEN: Live Backend Integration

| Route | Component | Hook | Backend Endpoint |
|-------|-----------|------|------------------|
| `/accounts` | Accounts | useAccounts | GET l4 |
| `/accounts/:id` | Accounts | useAccounts | GET l4 |
| `/context/extraction` | ExtractionEngine | useExtraction | POST l2 |
| `/context/formulas` | FormulaList | useFormulas | DELETE l3 |
| `/context/integrations` | Integrations | useIntegrations | GET l4 |
| `/context/models` | MyModels | useModels | DELETE l3 |
| `/context/ontology/entities` | EntityBrowser | useEntities | GET /v1/entities?search_text={query |
| `/context/ontology/graph` | GraphExplorer | useGraphQuery | POST l3 |
| `/context/packs` | ValuePacks | useValuePacks | POST l3 |
| `/deliverables/api` | Integrations | useIntegrations | GET l4 |
| `/governance/benchmarks` | BenchmarkPolicies | useBenchmarks | GET l6 |
| `/governance/health` | HealthMonitor | useSystemHealth | GET l4 |
| `/settings/data/bindings` | VariableRegistry | useVariables | POST l3 |
| `/settings/data/quality` | VariableRegistry | useVariables | POST l3 |
| `/settings/data/variables` | VariableRegistry | useVariables | POST l3 |
| `/settings/system/settings` | PlatformSettings | usePlatformSettings | GET l4 |

### RED: Hardcoded/Mock/Orphaned

| Route | Component | Hook | Backend Endpoint |
|-------|-----------|------|------------------|
| `* (catch-all)` | NotFound | UNKNOWN | N/A |
| `/command-center` | CommandCenter | UNKNOWN | N/A |
| `/context/ontology/entities/:entityId` | EntityDetail | UNKNOWN | N/A |
| `/context/sources` | SourceConfiguration | useSources | DELETE l1 |
| `/deliverables/calculators` | InteractiveBusinessCase | UNKNOWN | N/A |
| `/home` | ValueNarrativeHome | UNKNOWN | N/A |
| `/intelligence` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/:accountId` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/drivers` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/evidence` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/signals` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/stakeholders` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/drivers` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/evidence` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/signals` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/stakeholders` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio/discovery` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio/explorer` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio/mapping` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio/modeling` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio/narrative` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio/tracking` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/model/value-studio/validation` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/settings/access/keys` | PermissionsAdmin | UNKNOWN | N/A |
| `/settings/access/roles` | PermissionsAdmin | UNKNOWN | N/A |
| `/settings/access/teams` | PermissionsAdmin | UNKNOWN | N/A |
| `/settings/content/approvals` | FormulaGovernance | UNKNOWN | N/A |
| `/settings/content/formulas` | FormulaGovernance | UNKNOWN | N/A |
| `/settings/content/versions` | FormulaGovernance | UNKNOWN | N/A |
| ... | *21 more routes* | | |

### UNKNOWN: Unevaluated/Incomplete

| Route | Component | Hook | Backend Endpoint |
|-------|-----------|------|------------------|
| `/context/agents` | AgentWorkflows | useWorkflows | N/A |
| `/context/formulas/:formulaId` | FormulaBuilder | useFormula | N/A |
| `/context/formulas/new` | FormulaBuilder | useFormula | N/A |
| `/context/ingestion/jobs` | IngestionJobs | useIngestion | N/A |
| `/context/ontology` | OntologyEditor | useOntology | N/A |
| `/deliverables/cases` | BusinessCaseList | useBusinessCases | N/A |
| `/deliverables/cases/:caseId` | BusinessCase | useBusinessCases | N/A |
| `/deliverables/views/cfo` | BusinessCase | useBusinessCases | N/A |
| `/deliverables/views/executive` | BusinessCase | useBusinessCases | N/A |
| `/deliverables/views/technical` | BusinessCase | useBusinessCases | N/A |
| `/governance/audit/changes` | DecisionTrace | useProvenance | N/A |
| `/governance/audit/log` | DecisionTrace | useProvenance | N/A |
| `/governance/compliance` | DecisionTrace | useProvenance | N/A |
| `/governance/evidence` | DecisionTrace | useProvenance | N/A |
| `/governance/integrity` | DecisionTrace | useProvenance | N/A |
| `/governance/provenance` | DecisionTrace | useProvenance | N/A |
| `/governance/traces` | DecisionTrace | useProvenance | N/A |
