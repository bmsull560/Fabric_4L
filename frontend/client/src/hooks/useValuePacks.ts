import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

export type PackStatus = 'active' | 'draft' | 'archived' | 'published';
export type PackScope = 'global' | 'tenant';

// Domain-specific error class
export class ValuePackApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'ValuePackApiError';
  }
}

export interface ValuePack {
  id: string;
  pack_id: string;
  name: string;
  industry: string;
  description?: string;
  driver_count: number;
  formula_count: number;
  benchmark_count: number;
  workflow_count: number;
  status: PackStatus;
  scope: PackScope;
  updated_at: string;
  created_at?: string;
  version?: string;
  owner?: string;
}

// ValuePack-specific stale time overrides
const VALUE_PACK_STALE_TIME = {
  ...STALE_TIME,
  list: 60 * 1000,      // 1 minute for pack lists
  detail: 5 * 60 * 1000, // 5 minutes for single pack
} as const;

const VALUE_PACK_KEYS = {
  all: ['value-packs'] as const,
  list: (filters: ValuePackFilters) => [...VALUE_PACK_KEYS.all, 'list', filters] as const,
  detail: (id: string) => [...VALUE_PACK_KEYS.all, 'detail', id] as const,
  stats: ['value-packs', 'stats'] as const,
};

export interface ValuePackFilters {
  industry?: string | 'all';
  status?: PackStatus | 'all';
  scope?: PackScope | 'all';
  search?: string;
}

async function fetchValuePacks(filters: ValuePackFilters): Promise<ValuePack[]> {
  const params = new URLSearchParams();
  if (filters.industry && filters.industry !== 'all') params.set('industry', filters.industry);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.scope && filters.scope !== 'all') params.set('scope', filters.scope);
  if (filters.search) params.set('search', filters.search);

  const response = await apiClient.get('l3', `/packs?${params.toString()}`);
  return response.data as ValuePack[];
}

export function useValuePacks(filters: ValuePackFilters = {}) {
  return useQuery<ValuePack[], ValuePackApiError>({
    queryKey: VALUE_PACK_KEYS.list(filters),
    queryFn: () => withApiError(fetchValuePacks(filters), ValuePackApiError),
    staleTime: VALUE_PACK_STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchValuePack(packId: string): Promise<ValuePack> {
  const response = await apiClient.get('l3', `/packs/${packId}`);
  return response.data as ValuePack;
}

export function useValuePack(packId: string | null) {
  return useQuery<ValuePack, ValuePackApiError>({
    queryKey: VALUE_PACK_KEYS.detail(packId || ''),
    queryFn: () => withApiError(fetchValuePack(packId!), ValuePackApiError),
    enabled: !!packId,
    staleTime: VALUE_PACK_STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useApplyValuePack() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (packId: string) => {
      if (!packId) throw new ValuePackApiError('Pack ID is required');
      const response = await apiClient.post('l3', `/packs/${packId}/apply`, {});
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: VALUE_PACK_KEYS.all });
    },
  });
}
