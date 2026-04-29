# Track A: Route Integrity Matrix

## Executive Summary

**Total Routes Analyzed:** 203

### Data Source Distribution

| Color | Status | Count | Percentage |
|-------|--------|-------|------------|
| **GREEN** | Live backend integration | 16 | 7.9% |
| **YELLOW** | Generic endpoint passthrough | 0 | 0.0% |
| **RED** | Hardcoded mock/orphaned | 75 | 36.9% |
| **REDIRECT** | Legacy redirects | 101 | 49.8% |
| **UNKNOWN** | Unknown/unevaluated | 11 | 5.4% |

### Facade Problem: 84.3%

**86** of **102** authenticated routes are non-functional facades (render hardcoded data, mocks, or have no backend integration).

## Route Detail by Category

### GREEN: Live Backend Integration

| Route | Component | Hook | Backend Endpoint |
|-------|-----------|------|------------------|
| `/accounts` | Accounts | useAccounts | GET l4 |
| `/accounts/:id` | Accounts | useAccounts | GET l4 |
| `/context/extraction` | ExtractionEngine | useExtraction | POST /v1/extract |
| `/context/formulas` | FormulaList | useFormulas | GET l3 |
| `/context/integrations` | Integrations | useIntegrations | GET l4 |
| `/context/models` | MyModels | useModels | GET l3 |
| `/context/ontology/entities` | EntityBrowser | useEntities | GET l3 |
| `/context/ontology/graph` | GraphExplorer | useGraphQuery | GET l3 |
| `/context/packs` | ValuePacks | useValuePacks | GET l3 |
| `/deliverables/api` | Integrations | useIntegrations | GET l4 |
| `/governance/benchmarks` | BenchmarkPolicies | useBenchmarks | GET l3 |
| `/governance/health` | HealthMonitor | useSystemHealth | GET l4 |
| `/settings/data/bindings` | VariableRegistry | useVariables | GET l3 |
| `/settings/data/quality` | VariableRegistry | useVariables | GET l3 |
| `/settings/data/variables` | VariableRegistry | useVariables | GET l3 |
| `/settings/system/settings` | PlatformSettings | usePlatformSettings | GET l4 |

### RED: Hardcoded/Mock/Orphaned

| Route | Component | Hook | Backend Endpoint |
|-------|-----------|------|------------------|
| `/command-center` | CommandCenter | UNKNOWN | N/A |
| `/context/ontology/entities/:entityId` | EntityDetail | UNKNOWN | N/A |
| `/context/sources` | SourceConfiguration | useSources | DELETE l1 |
| `/deliverables/calculators` | InteractiveBusinessCase | UNKNOWN | N/A |
| `/deliverables/views/cfo` | CFOView | UNKNOWN | N/A |
| `/deliverables/views/executive` | ExecutiveView | UNKNOWN | N/A |
| `/deliverables/views/technical` | TechnicalView | UNKNOWN | N/A |
| `/dev/integration` | Suspense | UNKNOWN | N/A |
| `/governance/audit/changes` | GovernanceChangeHistory | UNKNOWN | N/A |
| `/governance/audit/log` | GovernanceAuditLog | UNKNOWN | N/A |
| `/governance/compliance` | GovernanceCompliance | UNKNOWN | N/A |
| `/governance/evidence` | GovernanceEvidence | UNKNOWN | N/A |
| `/home` | ValueNarrativeHome | UNKNOWN | N/A |
| `/intelligence` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/:accountId` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/competitive` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/drivers` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/enrichment` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/evidence` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/evidence-lib...` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/hypotheses` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/roi` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/signals` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/:accountId/stakeholders` | AccountContextSync | UNKNOWN | N/A |
| `/intelligence/competitive` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/drivers` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/enrichment` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/evidence` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/evidence-library` | WorkspaceContextRedirect | UNKNOWN | N/A |
| `/intelligence/hypotheses` | WorkspaceContextRedirect | UNKNOWN | N/A |
| ... | *45 more routes* | | |

### UNKNOWN: Unevaluated/Incomplete

| Route | Component | Hook | Backend Endpoint |
|-------|-----------|------|------------------|
| `/context/agents` | AgentWorkflows | useWorkflows | N/A |
| `/context/formulas/:formulaId` | FormulaBuilder | useFormula | N/A |
| `/context/formulas/new` | FormulaBuilder | useFormula | N/A |
| `/context/ingestion/jobs` | IngestionJobs | useIngestion | N/A |
| `/context/ontology` | OntologyEditor | useOntology | N/A |
| `/context/value-trees/explorer` | ValueTreeExplorer | useValueTrees | N/A |
| `/deliverables/cases` | BusinessCaseList | useBusinessCases | N/A |
| `/deliverables/cases/:caseId` | BusinessCase | useBusinessCases | N/A |
| `/governance/integrity` | DecisionTrace | useProvenance | N/A |
| `/governance/provenance` | DecisionTrace | useProvenance | N/A |
| `/governance/traces` | DecisionTrace | useProvenance | N/A |
