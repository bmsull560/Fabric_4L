export const L3_HEALTH_STATUSES = ['healthy', 'unhealthy', 'degraded'] as const;
export type L3HealthStatus = (typeof L3_HEALTH_STATUSES)[number];

export const L3_ENTITY_STATUSES = ['validated', 'pending', 'draft', 'deprecated'] as const;
export type L3EntityStatus = (typeof L3_ENTITY_STATUSES)[number];

export const L3_INGEST_STATUSES = ['success', 'partial', 'failed'] as const;
export type L3IngestStatus = (typeof L3_INGEST_STATUSES)[number];

export const L3_SYNC_STATUSES = ['synced', 'pending', 'failed', 'outdated'] as const;
export type L3SyncStatus = (typeof L3_SYNC_STATUSES)[number];

export const L3_BENCHMARK_STATUSES = ['active', 'draft', 'deprecated'] as const;
export type L3BenchmarkStatus = (typeof L3_BENCHMARK_STATUSES)[number];

export const FORMULA_VERSION_STATUSES = [
  'draft',
  'under_review',
  'approved',
  'active',
  'deprecated',
  'retired',
] as const;
export type FormulaVersionStatus = (typeof FORMULA_VERSION_STATUSES)[number];
