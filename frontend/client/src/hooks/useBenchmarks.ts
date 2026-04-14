import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { withApiError, BenchmarkApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// Benchmark-specific stale time overrides
const BENCHMARK_STALE_TIME = {
  ...STALE_TIME,
  list: 60 * 1000,      // 1 minute for benchmark lists (longer than default)
} as const;

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

// Re-export for backward compatibility
export { BenchmarkApiError } from './useApiShared';

const BENCHMARK_KEYS = {
  all: ['benchmarks'] as const,
  list: (filters: BenchmarkFilters) => [...BENCHMARK_KEYS.all, 'list', filters] as const,
  detail: (id: string) => [...BENCHMARK_KEYS.all, 'detail', id] as const,
};

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
    queryKey: BENCHMARK_KEYS.list(filters),
    queryFn: () => withApiError(fetchBenchmarks(filters), BenchmarkApiError),
    staleTime: BENCHMARK_STALE_TIME.list,
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
    queryKey: BENCHMARK_KEYS.detail(benchmarkId || ''),
    queryFn: async () => {
      if (!benchmarkId) throw new BenchmarkApiError('No benchmark ID provided');
      return withApiError(fetchBenchmark(benchmarkId), BenchmarkApiError);
    },
    enabled: !!benchmarkId,
    staleTime: BENCHMARK_STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}
