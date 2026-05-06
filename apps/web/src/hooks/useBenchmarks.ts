import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BenchmarkApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';
import { createFeatureLogger } from '@/lib/telemetry';
import type { BenchmarkDataset } from '@/api/types';

const log = createFeatureLogger('useBenchmarks');


export type ConfidenceLevel = 'High' | 'Medium' | 'Low';
export type BenchmarkStatus = 'active' | 'draft' | 'deprecated';

export interface Benchmark {
  id: string;
  benchmark_id: string;
  name: string;
  industry: string;
  vertical?: string;
  value_range: string;
  confidence: ConfidenceLevel;
  source: string;
  source_url?: string;
  year: number;
  status: BenchmarkStatus;
  tags: string[];
  last_verified?: string;
  usage_count: number;
  description?: string;
}

/**
 * L6 dataset shape mapped into legacy benchmark UI fields.
 * Keep this hook L6-only; L3 ROI assumptions live in useROICalculator.
 */
export type L6BenchmarkDataset = BenchmarkDataset;

// Re-export for backward compatibility
export { BenchmarkApiError } from './useApiShared';



export interface BenchmarkPolicy {
  id: string;
  policy_id: string;
  name: string;
  description?: string;
  rules: Array<{
    metric: string;
    threshold: number;
    operator: 'gt' | 'lt' | 'eq' | 'gte' | 'lte';
  }>;
  status: 'active' | 'draft' | 'archived';
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface BenchmarkFilters {
  industry?: string;
  status?: BenchmarkStatus | 'all';
  confidence?: ConfidenceLevel | 'all';
  search?: string;
}

async function fetchBenchmarks(filters: BenchmarkFilters): Promise<Benchmark[]> {
  const params = new URLSearchParams();
  if (filters.industry) params.set('industry', filters.industry);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.confidence && filters.confidence !== 'all') params.set('confidence', filters.confidence);
  if (filters.search) params.set('search', filters.search);

  const response = await apiClient.get('l6', `/datasets?${params.toString()}`);
  return response.data as Benchmark[];
}

/**
 * Hook to fetch a list of benchmarks with filtering support.
 *
 * @param filters - Optional filters for industry, status, confidence level, or search query
 * @returns Query result with Benchmark array and loading/error states
 */
export function useBenchmarks(filters: BenchmarkFilters = {}) {
  return useQuery<Benchmark[], BenchmarkApiError>({
    queryKey: QK.benchmarks.list(filters),
    queryFn: () => withApiError(fetchBenchmarks(filters), BenchmarkApiError),
    staleTime: STALE_TIME.stats,      // 1 minute for benchmark lists
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchBenchmark(benchmarkId: string): Promise<Benchmark> {
  const response = await apiClient.get('l6', `/datasets/${benchmarkId}`);
  return response.data as Benchmark;
}

/**
 * Hook to fetch a single benchmark by ID.
 *
 * @param benchmarkId - The benchmark ID to fetch, or null to disable the query
 * @returns Query result with Benchmark data and loading/error states
 */
export function useBenchmark(benchmarkId: string | null) {
  return useQuery<Benchmark, BenchmarkApiError>({
    queryKey: QK.benchmarks.detail(benchmarkId || ''),
    queryFn: async () => {
      if (!benchmarkId) throw new BenchmarkApiError('No benchmark ID provided');
      return withApiError(fetchBenchmark(benchmarkId), BenchmarkApiError);
    },
    enabled: !!benchmarkId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchBenchmarkPolicies(): Promise<BenchmarkPolicy[]> {
  const response = await apiClient.get('l3', '/benchmarks/policies');
  return response.data as BenchmarkPolicy[];
}

/**
 * Hook to fetch benchmark policy configuration.
 *
 * @returns Query result with policy array and loading/error states
 */
export function useBenchmarkPolicies() {
  return useQuery<BenchmarkPolicy[], BenchmarkApiError>({
    queryKey: QK.benchmarks.policies,
    queryFn: () => withApiError(fetchBenchmarkPolicies(), BenchmarkApiError),
    staleTime: STALE_TIME.policies,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/** Parameters for updating a benchmark policy */
export interface UpdateBenchmarkPolicyParams extends Partial<BenchmarkPolicy> {
  id: string;
}

/**
 * Hook to update a benchmark policy.
 *
 * @returns Mutation result with execute function and loading/error states
 */
export function useUpdateBenchmarkPolicy() {
  const queryClient = useQueryClient();

  return useMutation<BenchmarkPolicy, BenchmarkApiError, UpdateBenchmarkPolicyParams>({
    mutationFn: async (policy) => {
      if (!policy.id) throw new BenchmarkApiError('Policy ID is required');
      const response = await apiClient.put('l3', `/benchmarks/policies/${policy.id}`, policy);
      return response.data as BenchmarkPolicy;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.benchmarks.policies });
    },
    onError: (error) => {
      log.error('Benchmark policy update failed', { errorCode: error.message });
    },
  });
}
