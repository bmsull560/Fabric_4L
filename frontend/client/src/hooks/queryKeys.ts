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
import type { BenchmarkFilters } from './useBenchmarks';
import type { FormulaFilters } from './useFormulas';
import type { ValuePackFilters } from './useValuePacks';
import type { ModelFilters } from './useModels';
import type { VariableFilters } from './useVariables';
import type { GraphQueryRequest, EntityTraversalRequest } from './useGraphQuery';
import type { AuditLogFilter } from './useProvenance';
import type { SourceFilters } from './useSources';
import type { ProductListFilters } from './useProducts';
import type { CaseStudyListFilters } from './useEvidence';
import type { CompetitorListFilters } from './useCompetitiveIntel';
import type { ROICalculationListFilters } from './useROICalculator';
import type { AccountHypothesesFilters } from './useHypotheses';
import type { NarrativeListFilters } from './useNarratives';

// ── Registry ─────────────────────────────────────────────────────────────────
export const QK = {
  // Layer 1 — Ingestion
  ingestion: {
    all:    ['ingestion'] as const,
    jobs:   () => ['ingestion', 'jobs'] as const,
    recent: () => ['ingestion', 'recent'] as const,
    stats:  () => ['ingestion', 'stats'] as const,
    list:   (filters: unknown) => ['ingestion', 'list', stableKey(filters)] as const,
    detail: (id: string) => ['ingestion', 'detail', id] as const,
    logs:   (id: string) => ['ingestion', 'logs', id] as const,
  },

  // Layer 1 — Sources (Data Source Configuration)
  sources: {
    all:    ['sources'] as const,
    list:   (filters: SourceFilters) => ['sources', 'list', stableKey(filters)] as const,
    detail: (id: string) => ['sources', 'detail', id] as const,
    stats:  ['sources', 'stats'] as const,
  },

  // Layer 2 — Extraction
  extraction: {
    all:     ['extraction'] as const,
    job:     (id: string) => ['extraction', 'job', id] as const,
    results: (id: string) => ['extraction', 'results', id] as const,
  },

  // Layer 3 — Knowledge graph
  graph: {
    all:       ['graph'] as const,
    query:     (params: GraphQueryRequest) =>
                 ['graph', 'query', stableKey(params)] as const,
    context:   (entityId: string, hops?: number) =>
                 ['graph', 'context', entityId, hops] as const,
    traversal: (params: EntityTraversalRequest) =>
                 ['graph', 'traversal', stableKey(params)] as const,
    subgraph:  (query?: string, centerEntityId?: string, depth?: number, limit?: number) =>
                 ['graph', 'subgraph', query ?? '', centerEntityId ?? '', depth ?? 2, limit ?? 100] as const,
  },

  entities: {
    all:    ['entities'] as const,
    list:   () => ['entities', 'list'] as const,
    search: (query: string) => ['entities', 'search', query] as const,
    detail: (id: string) => ['entities', 'detail', id] as const,
  },

  formulas: {
    all:       ['formulas'] as const,
    list:      (filters: FormulaFilters) => ['formulas', 'list', filters] as const,
    detail:    (id: string) => ['formulas', 'detail', id] as const,
    approvals: ['formulas', 'approvals'] as const,
  },

  benchmarks: {
    all:      ['benchmarks'] as const,
    list:     (filters: BenchmarkFilters) => ['benchmarks', 'list', filters] as const,
    detail:   (id: string) => ['benchmarks', 'detail', id] as const,
    policies: ['benchmarks', 'policies'] as const,
  },

  variables: {
    all:      ['variables'] as const,
    list:     (filters: VariableFilters) => ['variables', 'list', filters] as const,
    detail:   (id: string) => ['variables', 'detail', id] as const,
    bindings: ['variables', 'bindings'] as const,
    stats:    ['variables', 'stats'] as const,
  },

  valuePacks: {
    all:    ['value-packs'] as const,
    list:   (filters: ValuePackFilters) => ['value-packs', 'list', filters] as const,
    detail: (id: string) => ['value-packs', 'detail', id] as const,
    stats:  ['value-packs', 'stats'] as const,
  },

  models: {
    all:     ['models'] as const,
    list:    (filters: ModelFilters) => ['models', 'list', stableKey(filters)] as const,
    detail:  (id: string) => ['models', 'detail', id] as const,
    folders: () => ['models', 'folders'] as const,
  },

  valueTrees: {
    all:    ['value-trees'] as const,
    tree:   (entityId: string, direction: string, maxDepth: number) => 
              ['value-trees', 'tree', entityId, direction, maxDepth] as const,
    paths:  (entityId: string, direction: string, maxDepth: number) =>
              ['value-trees', 'paths', entityId, direction, maxDepth] as const,
  },

  provenance: {
    all:   ['provenance'] as const,
    trail: (entityId: string) => ['provenance', 'trail', entityId] as const,
    audit: (filters: AuditLogFilter) => ['provenance', 'audit', filters] as const,
  },

  // Layer 4 — Agents / Governance
  workflows: {
    all:     ['workflows'] as const,
    active:  () => ['workflows', 'active'] as const,
    history: () => ['workflows', 'history'] as const,
    detail:  (id: string) => ['workflows', 'detail', id] as const,
  },

  businessCases: {
    all:    ['business-cases'] as const,
    list:   (filters: { status?: string; search?: string; company?: string }) => 
              ['business-cases', 'list', stableKey(filters)] as const,
    detail: (id: string) => ['business-cases', 'detail', id] as const,
  },

  documents: {
    all:          ['documents'] as const,
    export:       (id: string) => ['documents', 'export', id] as const,
    businessCase: (id: string) => ['documents', 'businessCase', id] as const,
  },

  governance: {
    tenants: ['governance', 'tenants'] as const,
    users:   (tenantId?: string) => ['governance', 'users', tenantId] as const,
    apiKeys: (tenantId?: string) => ['governance', 'api-keys', tenantId] as const,
  },

  accounts: {
    all:        ['accounts'] as const,
    list:       (filters: unknown) => ['accounts', 'list', filters] as const,
    detail:     (id: string) => ['accounts', 'detail', id] as const,
    activity:   (id: string) => ['accounts', 'activity', id] as const,
    syncStatus: ['accounts', 'sync-status'] as const,
    filters:    ['accounts', 'filters'] as const,
  },

  integrations: {
    all:    ['integrations'] as const,
    list:   ['integrations', 'list'] as const,
    detail: (provider: string) => ['integrations', 'detail', provider] as const,
  },

  // Narrative generation
  narrative: {
    all:        ['narrative'] as const,
    industries: () => ['narrative', 'industries'] as const,
  },

  // Platform/Admin Settings
  platform: {
    all:      ['platform'] as const,
    settings: ['platform', 'settings'] as const,
    health:   ['platform', 'health'] as const,
  },

  // Ontology Schema Management
  ontology: {
    all:    ['ontology'] as const,
    schema: () => ['ontology', 'schema'] as const,
    type:   (id: string) => ['ontology', 'type', id] as const,
  },

  // ── Data Intelligence Layer (DIL) ─────────────────────────────────────────

  // L3 — Product Portfolio
  products: {
    all:             ['products'] as const,
    list:            (filters: ProductListFilters) => ['products', 'list', stableKey(filters)] as const,
    detail:          (id: string) => ['products', 'detail', id] as const,
    signalMatching:  (accountId?: string) => ['products', 'signal-matching', accountId ?? ''] as const,
    summary:         () => ['products', 'summary'] as const,
    coverage:        () => ['products', 'coverage'] as const,
  },

  // L3 — Evidence Library
  evidence: {
    all:           ['evidence'] as const,
    list:          (filters: CaseStudyListFilters) => ['evidence', 'list', stableKey(filters)] as const,
    detail:        (id: string) => ['evidence', 'detail', id] as const,
    industryStats: () => ['evidence', 'stats', 'industry'] as const,
    productStats:  () => ['evidence', 'stats', 'product'] as const,
  },

  // L3 — Competitive Intelligence
  competitive: {
    all:          ['competitive'] as const,
    list:         (filters: CompetitorListFilters) => ['competitive', 'list', stableKey(filters)] as const,
    detail:       (id: string) => ['competitive', 'detail', id] as const,
    battlecards:  (competitorId: string) => ['competitive', 'battlecards', competitorId] as const,
    winLoss:      (competitorId?: string) => ['competitive', 'win-loss', competitorId ?? ''] as const,
    landscape:    (productId?: string) => ['competitive', 'landscape', productId ?? ''] as const,
  },

  // L3 — ROI Calculator
  roi: {
    all:        ['roi'] as const,
    list:       (filters: ROICalculationListFilters) => ['roi', 'list', stableKey(filters)] as const,
    detail:     (id: string) => ['roi', 'detail', id] as const,
    templates:  () => ['roi', 'templates'] as const,
    benchmarks: (industry: string) => ['roi', 'benchmarks', industry] as const,
  },

  // L4 — Account Enrichment
  enrichment: {
    all:    ['enrichment'] as const,
    status: () => ['enrichment', 'status'] as const,
    detail: (accountId: string) => ['enrichment', 'detail', accountId] as const,
  },

  // L4 — Value Hypotheses
  hypotheses: {
    all:       ['hypotheses'] as const,
    detail:    (id: string) => ['hypotheses', 'detail', id] as const,
    byAccount: (accountId: string, filters?: AccountHypothesesFilters) =>
                 ['hypotheses', 'account', accountId, stableKey(filters ?? {})] as const,
    stats:     () => ['hypotheses', 'stats'] as const,
  },

  // L4 — Narratives
  narratives: {
    all:    ['narratives'] as const,
    list:   (filters: NarrativeListFilters) => ['narratives', 'list', stableKey(filters)] as const,
    detail: (id: string) => ['narratives', 'detail', id] as const,
  },



  // L5 — Ground Truth Governance
  groundTruth: {
    all:              ['ground-truth'] as const,
    list:             (filters: unknown) => ['ground-truth', 'list', stableKey(filters)] as const,
    audit:            (truthId: string) => ['ground-truth', 'audit', truthId] as const,
    freshnessSummary: () => ['ground-truth', 'freshness-summary'] as const,
    stale:            (limit: number, offset: number) => ['ground-truth', 'stale', limit, offset] as const,
    maturityLadder:   () => ['ground-truth', 'maturity-ladder'] as const,
  },
  // L4 — Intelligence Orchestration
  intelligence: {
    all:           ['intelligence'] as const,
    briefing:      (accountId: string) => ['intelligence', 'briefing', accountId] as const,
    dealReadiness: (accountId: string) => ['intelligence', 'deal-readiness', accountId] as const,
    pipeline:      () => ['intelligence', 'pipeline'] as const,
  },
} as const;

// ── Helpers ───────────────────────────────────────────────────────────────────
/**
 * Produces a stable string key from an arbitrary object so that React Query
 * can use it as a cache key without reference equality issues.
 */
function stableKey(obj: unknown): string {
  if (obj == null || typeof obj !== 'object') return String(obj);
  return JSON.stringify(obj, Object.keys(obj).sort());
}
