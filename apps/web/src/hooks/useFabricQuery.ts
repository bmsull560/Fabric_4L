/**
 * useFabricQuery — Tier 2 Domain Query Hook Wrapper
 *
 * Contract: Hook Architecture Contract §2.2
 * Enforces standardized cache policy, retry logic, and error wrapping
 * for all domain-level list/detail queries.
 *
 * All new domain hooks MUST use this instead of raw `useQuery`.
 */
import { useQuery, type UseQueryOptions } from '@tanstack/react-query';
import { STALE_TIME, RETRY_CONFIG, withApiError, BaseApiError, type ApiErrorClass } from './useApiShared';

export interface FabricQueryOptions<TData, TError extends BaseApiError>
  extends Omit<UseQueryOptions<TData, TError>, 'queryFn' | 'queryKey'> {
  /** Query key from the QK registry */
  queryKey: readonly unknown[];
  /** Async fetcher — must NOT catch errors (wrapper handles that) */
  queryFn: () => Promise<TData>;
  /** Domain-specific error class extending BaseApiError */
  errorClass: ApiErrorClass;
  /** Optional staleTime override (defaults to STALE_TIME.list) */
  staleTime?: number;
  /** Optional retry override (defaults to RETRY_CONFIG.maxRetries) */
  retry?: number | false;
  /** Optional retryDelay override */
  retryDelay?: (attemptIndex: number) => number;
}

/**
 * Standardized query hook wrapper.
 *
 * @example
 * ```ts
 * export function useExtractionResults(jobId: string | null) {
 *   return useFabricQuery({
 *     queryKey: QK.extraction.results(jobId || ''),
 *     queryFn: () => fetchExtractionResults(jobId!),
 *     errorClass: BaseApiError,
 *     staleTime: STALE_TIME.poll,
 *     enabled: !!jobId,
 *   });
 * }
 * ```
 */
export function useFabricQuery<TData, TError extends BaseApiError>(
  options: FabricQueryOptions<TData, TError>
) {
  const { queryKey, queryFn, errorClass, staleTime, retry, retryDelay, ...rest } = options;

  return useQuery<TData, TError>({
    ...rest,
    queryKey: [...queryKey],
    queryFn: async () => withApiError(queryFn(), errorClass),
    staleTime: staleTime ?? STALE_TIME.list,
    retry: retry ?? RETRY_CONFIG.maxRetries,
    retryDelay: retryDelay ?? RETRY_CONFIG.retryDelay,
  });
}
