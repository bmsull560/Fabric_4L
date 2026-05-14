/**
 * queryKeys.ts — Centralized React Query key registry
 *
 * All query key factories live here. This prevents:
 *   1. Cache key collisions between hooks (e.g., two hooks using ['list'] at root)
 *   2. Stale invalidation bugs from typos in ad-hoc key strings
 *   3. Duplicate key definitions scattered across 14 hook files
 *
 * Usage:
 *   import { QK } from '@/hooks/queryKeys';
 *   queryKey: QK.formulas.list(filters)
 *   queryClient.invalidateQueries({ queryKey: QK.formulas.all })
 */

// ── Filter type imports (kept minimal to avoid circular deps) ─────────────────
import type { BenchmarkFilters } from "./useBenchmarks";
import type { FormulaFilters } from "./useFormulas";
import type { ValuePackFilters } from "./useValuePacks";
import type { ModelFilters } from "./useModels";
import type { VariableFilters } from "./useVariables";
import type {
  GraphQueryRequest,
  EntityTraversalRequest,
} from "./useGraphQuery";
import type { AuditLogFilter } from "./useProvenance";
import type { SourceFilters } from "./useSources";
import type { TargetFilters } from "./useTargets";
import type { ProductListFilters } from "./useProducts";
import type { CaseStudyListFilters } from "./useEvidence";
import type { CompetitorListFilters } from "./useCompetitiveIntel";
import type { ROICalculationListFilters } from "./useROICalculator";
import type { AccountHypothesesFilters } from "./useHypotheses";
import type { NarrativeListFilters } from "./useNarratives";
import type { LeverConfigRequest } from "./useCalculators";



/**
 * Observability tags used by query keys/hooks to correlate cache entries to
 * backend layer ownership in traces and debug tooling.
 */
export const QUERY_LAYER_TAGS = {
  layer1: "layer:1-ingestion",
  layer2: "layer:2-extraction",
  layer3: "layer:3-knowledge",
  layer4: "layer:4-agents",
  layer5: "layer:5-ground-truth",
  layer6: "layer:6-benchmarks",
  crossLayer: "layer:x-cross",
} as const;

// ── Registry ─────────────────────────────────────────────────────────────────
export const QK = {
  // Layer 1 — Ingestion
  ingestion: {
    layerTag: QUERY_LAYER_TAGS.layer1,
    all: ["ingestion"] as const,
    jobs: () => ["ingestion", "jobs"] as const,
    recent: () => ["ingestion", "recent"] as const,
    stats: () => ["ingestion", "stats"] as const,
    list: (filters: unknown) =>
      ["ingestion", "list", stableKey(filters)] as const,
    detail: (id: string) => ["ingestion", "detail", id] as const,
    logs: (id: string) => ["ingestion", "logs", id] as const,
  },

  // Layer 1 — Targets (Scraping Target Configuration)
  targets: {
    layerTag: QUERY_LAYER_TAGS.layer1,
    all: ["targets"] as const,
    list: (filters: TargetFilters) =>
      ["targets", "list", stableKey(filters)] as const,
    detail: (id: string) => ["targets", "detail", id] as const,
    stats: ["targets", "stats"] as const,
    jobs: (targetId: string) => ["targets", "jobs", targetId] as const,
  },

  // Layer 1 — Sources (Data Source Configuration)
  sources: {
    layerTag: QUERY_LAYER_TAGS.layer1,
    all: ["sources"] as const,
    list: (filters: SourceFilters) =>
      ["sources", "list", stableKey(filters)] as const,
    detail: (id: string) => ["sources", "detail", id] as const,
    stats: ["sources", "stats"] as const,
  },

  // Layer 2 — Extraction
  extraction: {
    layerTag: QUERY_LAYER_TAGS.layer2,
    all: ["extraction"] as const,
    job: (id: string) => ["extraction", "job", id] as const,
    results: (id: string) => ["extraction", "results", id] as const,
  },

  // Layer 3 — Knowledge graph
  graph: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["graph"] as const,
    query: (params: GraphQueryRequest) =>
      ["graph", "query", stableKey(params)] as const,
    context: (entityId: string, hops?: number) =>
      ["graph", "context", entityId, hops] as const,
    traversal: (params: EntityTraversalRequest) =>
      ["graph", "traversal", stableKey(params)] as const,
    subgraph: (
      query?: string,
      centerEntityId?: string,
      depth?: number,
      limit?: number
    ) =>
      [
        "graph",
        "subgraph",
        query ?? "",
        centerEntityId ?? "",
        depth ?? 2,
        limit ?? 100,
      ] as const,
  },

  entities: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["entities"] as const,
    list: () => ["entities", "list"] as const,
    search: (query: string) => ["entities", "search", query] as const,
    detail: (id: string) => ["entities", "detail", id] as const,
  },

  formulas: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["formulas"] as const,
    list: (filters: FormulaFilters) => ["formulas", "list", filters] as const,
    detail: (id: string) => ["formulas", "detail", id] as const,
    approvals: ["formulas", "approvals"] as const,
  },

  benchmarks: {
    layerTag: QUERY_LAYER_TAGS.layer6,
    all: ["benchmarks"] as const,
    list: (filters: BenchmarkFilters) =>
      ["benchmarks", "datasets", stableKey(filters)] as const,
    detail: (id: string) => ["benchmarks", "detail", id] as const,
    compare: () => ["benchmarks", "compare"] as const,
    industries: () => ["benchmarks", "industries"] as const,
    policies: ["benchmarks", "policies"] as const,
  },

  variables: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["variables"] as const,
    list: (filters: VariableFilters) => ["variables", "list", filters] as const,
    detail: (id: string) => ["variables", "detail", id] as const,
    bindings: ["variables", "bindings"] as const,
    stats: ["variables", "stats"] as const,
  },

  valuePacks: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["value-packs"] as const,
    list: (filters: ValuePackFilters) =>
      ["value-packs", "list", filters] as const,
    detail: (id: string) => ["value-packs", "detail", id] as const,
    stats: ["value-packs", "stats"] as const,
  },

  models: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["models"] as const,
    list: (filters: ModelFilters) =>
      ["models", "list", stableKey(filters)] as const,
    detail: (id: string) => ["models", "detail", id] as const,
    folders: () => ["models", "folders"] as const,
  },

  valueTrees: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["value-trees"] as const,
    tree: (entityId: string, direction: string, maxDepth: number) =>
      ["value-trees", "tree", entityId, direction, maxDepth] as const,
    paths: (entityId: string, direction: string, maxDepth: number) =>
      ["value-trees", "paths", entityId, direction, maxDepth] as const,
  },

  provenance: {
    layerTag: QUERY_LAYER_TAGS.layer5,
    all: ["provenance"] as const,
    trail: (entityId: string) => ["provenance", "trail", entityId] as const,
    audit: (filters: AuditLogFilter) =>
      ["provenance", "audit", filters] as const,
  },

  // Layer 4 — Agents / Governance
  workflows: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["workflows"] as const,
    active: () => ["workflows", "active"] as const,
    history: () => ["workflows", "history"] as const,
    detail: (id: string) => ["workflows", "detail", id] as const,
  },

  businessCases: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["business-cases"] as const,
    list: (filters: { status?: string; search?: string; company?: string }) =>
      ["business-cases", "list", stableKey(filters)] as const,
    detail: (id: string) => ["business-cases", "detail", id] as const,
  },

  documents: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["documents"] as const,
    export: (id: string) => ["documents", "export", id] as const,
    businessCase: (id: string) => ["documents", "businessCase", id] as const,
  },

  governance: {
    layerTag: QUERY_LAYER_TAGS.layer5,
    all: ["governance"] as const,
    tenants: ["governance", "tenants"] as const,
    users: (tenantId?: string) => ["governance", "users", tenantId] as const,
    apiKeys: (tenantId?: string) =>
      ["governance", "api-keys", tenantId] as const,
    review: (reviewId: string) => ["governance", "review", reviewId] as const,
    reviewQueue: (filters: { status?: string; subject_type?: string }) =>
      ["governance", "review-queue", stableKey(filters)] as const,
    reviewComments: (reviewId: string) =>
      ["governance", "review-comments", reviewId] as const,
    audit: (reviewId: string) => ["governance", "audit", reviewId] as const,
    auditExport: (jobId: string) => ["governance", "audit-export", jobId] as const,
    lineage: (correlationId: string) =>
      ["governance", "lineage", correlationId] as const,
  },

  workspace: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["workspace"] as const,
    caseId: (accountId: string | null) => ["workspace", "case-id", accountId] as const,
    tab: (caseId: string | null, tabKey: string) =>
      ["workspace", "tab", caseId, tabKey] as const,
    accountTab: (accountId: string, tabKey: string) =>
      ["workspace", accountId, tabKey] as const,
  },

  versions: {
    layerTag: QUERY_LAYER_TAGS.layer5,
    all: ["versions"] as const,
    list: (accountId: string) => ["versions", "list", accountId] as const,
    detail: (versionId: string) => ["versions", "detail", versionId] as const,
    compare: (versionId: string, compareToVersionId: string) =>
      ["versions", "compare", versionId, compareToVersionId] as const,
  },

  accounts: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["accounts"] as const,
    list: (filters: unknown) => ["accounts", "list", filters] as const,
    detail: (id: string) => ["accounts", "detail", id] as const,
    activity: (id: string) => ["accounts", "activity", id] as const,
    syncStatus: ["accounts", "sync-status"] as const,
    filters: ["accounts", "filters"] as const,
  },

  tasks: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["tasks"] as const,
    list: (filters: { accountId?: string; status?: string }) =>
      ["tasks", "list", stableKey(filters)] as const,
  },

  comments: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["comments"] as const,
    list: (filters: { subjectType?: string; subjectId?: string; accountId?: string }) =>
      ["comments", "list", stableKey(filters)] as const,
  },

  notifications: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["notifications"] as const,
    list: (filters: { read?: boolean; accountId?: string }) =>
      ["notifications", "list", stableKey(filters)] as const,
  },

  integrations: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["integrations"] as const,
    list: ["integrations", "list"] as const,
    detail: (provider: string) => ["integrations", "detail", provider] as const,
  },

  // Narrative generation
  narrative: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["narrative"] as const,
    industries: () => ["narrative", "industries"] as const,
  },

  // Platform/Admin Settings
  platform: {
    layerTag: QUERY_LAYER_TAGS.crossLayer,
    all: ["platform"] as const,
    settings: ["platform", "settings"] as const,
    health: ["platform", "health"] as const,
  },

  // Ontology Schema Management
  ontology: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["ontology"] as const,
    schema: () => ["ontology", "schema"] as const,
    type: (id: string) => ["ontology", "type", id] as const,
  },

  // ── Data Intelligence Layer (DIL) ─────────────────────────────────────────

  // L3 — Product Portfolio
  products: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["products"] as const,
    list: (filters: ProductListFilters) =>
      ["products", "list", stableKey(filters)] as const,
    detail: (id: string) => ["products", "detail", id] as const,
    signalMatching: (accountId?: string) =>
      ["products", "signal-matching", accountId ?? ""] as const,
    summary: () => ["products", "summary"] as const,
    coverage: () => ["products", "coverage"] as const,
  },

  // L3 — Evidence Library
  evidence: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["evidence"] as const,
    list: (filters: CaseStudyListFilters) =>
      ["evidence", "list", stableKey(filters)] as const,
    detail: (id: string) => ["evidence", "detail", id] as const,
    industryStats: () => ["evidence", "stats", "industry"] as const,
    productStats: () => ["evidence", "stats", "product"] as const,
  },

  // L3 — Competitive Intelligence
  competitive: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["competitive"] as const,
    list: (filters: CompetitorListFilters) =>
      ["competitive", "list", stableKey(filters)] as const,
    detail: (id: string) => ["competitive", "detail", id] as const,
    battlecards: (competitorId: string) =>
      ["competitive", "battlecards", competitorId] as const,
    battlecard: (competitorId: string, productId: string) =>
      ["competitive", "battlecard", competitorId, productId] as const,
    winLoss: (competitorId?: string) =>
      ["competitive", "win-loss", competitorId ?? ""] as const,
    landscape: (productId?: string) =>
      ["competitive", "landscape", productId ?? ""] as const,
  },

  // L3 — ROI Calculator
  roi: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["roi"] as const,
    list: (filters: ROICalculationListFilters) =>
      ["roi", "list", stableKey(filters)] as const,
    detail: (id: string) => ["roi", "detail", id] as const,
    templates: () => ["roi", "templates"] as const,
    /**
     * L3 ROI benchmark assumptions (separate from L6 benchmark datasets).
     */
    assumptionsByIndustry: (industry: string) => ["roi", "assumptions", industry] as const,
    assumptionsList: () => ["roi", "assumptions-list"] as const,
    assumptionDetail: (id: string) => ["roi", "assumption", id] as const,
    agentCalculation: () => ["roi", "agent-calculation"] as const,
    scenarioVersions: (scope: { tenantId?: string | null; accountId?: string | null; caseId?: string | null; modelId?: string | null }) =>
      ["roi", "scenario-versions", stableKey(scope)] as const,
  },

  // L3 — Value Calculators (Workflow)
  calculators: {
    layerTag: QUERY_LAYER_TAGS.layer3,
    all: ["calculators"] as const,
    levers: (filters: unknown) =>
      ["calculators", "levers", stableKey(filters)] as const,
    detail: (id: string) => ["calculators", "detail", id] as const,
  },

  // L4 — Account Enrichment
  enrichment: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["enrichment"] as const,
    status: () => ["enrichment", "status"] as const,
    detail: (accountId: string) => ["enrichment", "detail", accountId] as const,
  },

  // L4 — Value Hypotheses
  hypotheses: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["hypotheses"] as const,
    detail: (id: string) => ["hypotheses", "detail", id] as const,
    byAccount: (accountId: string, filters?: AccountHypothesesFilters) =>
      ["hypotheses", "account", accountId, stableKey(filters ?? {})] as const,
    stats: () => ["hypotheses", "stats"] as const,
  },

  
  intelligenceDecisions: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["intelligence-decisions"] as const,
    signalReview: (scope: { tenantId?: string; accountId?: string; caseId?: string; signalId?: string }) =>
      ["intelligence-decisions", "signal-review", stableKey(scope)] as const,
    evidenceDecision: (scope: { tenantId?: string; accountId?: string; caseId?: string; evidenceId?: string }) =>
      ["intelligence-decisions", "evidence", stableKey(scope)] as const,
  },
// L4 — Narratives
  narratives: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["narratives"] as const,
    list: (filters: NarrativeListFilters) =>
      ["narratives", "list", stableKey(filters)] as const,
    detail: (id: string) => ["narratives", "detail", id] as const,
  },

  // L5 — Ground Truth Governance
  groundTruth: {
    layerTag: QUERY_LAYER_TAGS.layer5,
    all: ["ground-truth"] as const,
    list: (filters: unknown) =>
      ["ground-truth", "list", stableKey(filters)] as const,
    truths: (filters: unknown) =>
      ["ground-truth", "truths", stableKey(filters)] as const,
    audit: (truthId: string) => ["ground-truth", "audit", truthId] as const,
    truthAudit: (truthId: string | null) => ["ground-truth", "truth-audit", truthId] as const,
    freshnessSummary: () => ["ground-truth", "freshness-summary"] as const,
    stale: (filters: unknown) =>
      ["ground-truth", "stale", stableKey(filters)] as const,
    maturityLadder: () => ["ground-truth", "maturity-ladder"] as const,
  },

  // L4 — Intelligence Orchestration
  intelligence: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["intelligence"] as const,
    briefing: (accountId: string) =>
      ["intelligence", "briefing", accountId] as const,
    dealReadiness: (accountId: string) =>
      ["intelligence", "deal-readiness", accountId] as const,
    pipeline: () => ["intelligence", "pipeline"] as const,
  },

  // Gates & Reviews
  gates: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["gates"] as const,
    account: (accountId: string) => ["gates", "account", accountId] as const,
  },

  reviews: {
    layerTag: QUERY_LAYER_TAGS.layer4,
    all: ["reviews"] as const,
    list: (accountId: string) => ["reviews", "list", accountId] as const,
    detail: (reviewId: string) => ["reviews", "detail", reviewId] as const,
  },
} as const;

// ── Helpers ───────────────────────────────────────────────────────────────────
/**
 * Produces a stable string key from an arbitrary object so that React Query
 * can use it as a cache key without reference equality issues.
 */
function stableKey(obj: unknown): string {
  if (obj == null || typeof obj !== "object") return String(obj);
  return JSON.stringify(obj, Object.keys(obj).sort());
}
