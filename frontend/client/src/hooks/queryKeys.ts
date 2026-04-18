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
