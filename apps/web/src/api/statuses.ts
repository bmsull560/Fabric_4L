import type { l3 } from '@/api/generated';

export const L3_HEALTH_STATUSES = ['healthy', 'unhealthy', 'degraded'] as const;
export type L3HealthStatus = l3.components['schemas']['DependencyStatus']['status'];

export const L3_ENTITY_STATUSES = ['validated', 'pending', 'draft', 'deprecated'] as const;
export type L3EntityStatus = l3.components['schemas']['Entity']['status'];

export const L3_INGEST_STATUSES = ['success', 'partial', 'failed'] as const;
export type L3IngestStatus = l3.components['schemas']['IngestResponse']['status'];

export const L3_SYNC_STATUSES = ['synced', 'pending', 'failed', 'outdated'] as const;
export type L3SyncStatus = NonNullable<l3.components['schemas']['SyncStatusResponse']['status']>;

export const L3_BENCHMARK_STATUSES = ['active', 'draft', 'deprecated'] as const;
export type L3BenchmarkStatus = l3.components['schemas']['BenchmarkPolicy']['status'];

export const FORMULA_VERSION_STATUSES = [
  'draft',
  'under_review',
  'approved',
  'active',
  'deprecated',
  'retired',
] as const;
export type FormulaVersionStatus = (typeof FORMULA_VERSION_STATUSES)[number];
