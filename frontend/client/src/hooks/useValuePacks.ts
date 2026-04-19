import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG, formatZodError } from './useApiShared';
import {
  ValuePackSchema,
  ValuePackListSchema,
  type ValuePack,
  type PackStatus,
  type PackScope,
} from '@/lib/schemas/valuePack';

// Domain-specific error class
export class ValuePackApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'ValuePackApiError';
  }
}

// Re-export types from schema for backward compatibility
export type { ValuePack, PackStatus, PackScope };


export interface ValuePackFilters {
  industry?: string | 'all';
  status?: PackStatus | 'all';
  scope?: PackScope | 'all';
  category?: string | 'all';
  search?: string;
}

/**
 * Fetch value packs with optional filtering.
 * @param filters - Optional filters for industry, status, scope, category, or search
 * @returns Array of value packs matching the filters
 */
async function fetchValuePacks(filters: ValuePackFilters): Promise<ValuePack[]> {
  const params = new URLSearchParams();
  if (filters.industry && filters.industry !== 'all') params.set('industry', filters.industry);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.scope && filters.scope !== 'all') params.set('scope', filters.scope);
  if (filters.category && filters.category !== 'all') params.set('category', filters.category);
  if (filters.search) params.set('search', filters.search);

  const response = await apiClient.get('l3', `/packs?${params.toString()}`);

  // Runtime validation with Zod
  const parsed = ValuePackListSchema.safeParse(response.data);
  if (!parsed.success) {
    console.error('Value pack list validation failed:', parsed.error);
    throw new ValuePackApiError(formatZodError(parsed.error, 'value pack list response'));
  }
  return parsed.data;
}

/**
 * Hook to fetch a list of value packs with optional filtering.
 * Results are cached for 1 minute (STALE_TIME.stats).
 *
 * @param filters - Optional filters for industry, status, scope, category, or search term
 * @returns React Query result with array of ValuePack objects
 *
 * @example
 * const { data: packs, isLoading } = useValuePacks({ industry: 'SaaS / B2B', status: 'published' });
 */
export function useValuePacks(filters: ValuePackFilters = {}) {
  return useQuery<ValuePack[], ValuePackApiError>({
    queryKey: QK.valuePacks.list(filters),
    queryFn: () => withApiError(fetchValuePacks(filters), ValuePackApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/**
 * Fetch a single value pack by ID.
 * @param packId - The unique identifier of the value pack
 * @returns The value pack details
 * @throws ValuePackApiError if the pack is not found or request fails
 */
async function fetchValuePack(packId: string): Promise<ValuePack> {
  const response = await apiClient.get('l3', `/packs/${packId}`);

  // Runtime validation with Zod
  const parsed = ValuePackSchema.safeParse(response.data);
  if (!parsed.success) {
    console.error('Value pack detail validation failed:', parsed.error);
    throw new ValuePackApiError(formatZodError(parsed.error, 'value pack response'));
  }
  return parsed.data;
}

/**
 * Hook to fetch a single value pack by ID.
 *
 * @param packId - The pack ID to fetch, or null to disable the query
 * @returns Query result with ValuePack data and loading/error states
 */
export function useValuePack(packId: string | null) {
  return useQuery<ValuePack, ValuePackApiError>({
    queryKey: QK.valuePacks.detail(packId || ''),
    queryFn: () => withApiError(fetchValuePack(packId!), ValuePackApiError),
    enabled: !!packId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/** Parameters for applying/deploying a value pack */
export interface ApplyValuePackParams {
  packId: string;
}

export interface ApplyValuePackResponse {
  success: boolean;
  message?: string;
}

/**
 * Hook to apply/deploy a value pack to the current tenant.
 * Invalidates the value packs list query on success.
 *
 * @returns Mutation object with typed data/error/parameter types
 */
export function useApplyValuePack() {
  const queryClient = useQueryClient();

  return useMutation<ApplyValuePackResponse, ValuePackApiError, ApplyValuePackParams>({
    mutationFn: async ({ packId }) => {
      if (!packId) throw new ValuePackApiError('Pack ID is required');
      const response = await apiClient.post('l3', `/packs/${packId}/apply`, {});
      return response.data as ApplyValuePackResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.valuePacks.all });
    },
    onError: (error) => {
      // Log error for monitoring/debugging; UI handles display via error state
      if (process.env.NODE_ENV === 'development') {
        console.error('[useApplyValuePack] Deployment failed:', error.message);
      }
    },
  });
}
