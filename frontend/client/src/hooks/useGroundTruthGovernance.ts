import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';
import type { components } from '@/api/generated/l5-types';

export class GroundTruthGovernanceApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'GroundTruthGovernanceApiError';
  }
}

export type TruthObjectSummary = components['schemas']['TruthObjectSummary'];
export type ValidationEventResponse = components['schemas']['ValidationEventResponse'];
export type MaturityLadderResponse = components['schemas']['MaturityLadderResponse'];

export interface TruthListFilters {
  status?: string;
  claim_type?: string;
  min_maturity?: number;
  min_confidence?: number;
  is_stale?: boolean;
  applies_to_opportunity?: string;
  limit?: number;
  offset?: number;
}

export interface TruthListResponse {
  items: TruthObjectSummary[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}

export interface FreshnessSummaryResponse {
  stale_count: number;
  fresh_count: number;
  expiring_soon_count: number;
}

export interface StaleTruthsResponse {
  items: TruthObjectSummary[];
  total: number;
  limit?: number;
  offset?: number;
}

function buildTruthListQuery(filters: TruthListFilters = {}): string {
  const params = new URLSearchParams();

  if (filters.status) params.set('status', filters.status);
  if (filters.claim_type) params.set('claim_type', filters.claim_type);
  if (filters.min_maturity != null) params.set('min_maturity', String(filters.min_maturity));
  if (filters.min_confidence != null) params.set('min_confidence', String(filters.min_confidence));
  if (filters.is_stale != null) params.set('is_stale', String(filters.is_stale));
  if (filters.applies_to_opportunity) params.set('applies_to_opportunity', filters.applies_to_opportunity);
  if (filters.limit != null) params.set('limit', String(filters.limit));
  if (filters.offset != null) params.set('offset', String(filters.offset));

  const query = params.toString();
  return query ? `?${query}` : '';
}

async function fetchTruths(filters: TruthListFilters = {}): Promise<TruthListResponse> {
  const response = await apiClient.get('l5', `/truths${buildTruthListQuery(filters)}`);
  return response.data as TruthListResponse;
}

async function fetchTruthAuditTrail(truthId: string): Promise<ValidationEventResponse[]> {
  const response = await apiClient.get('l5', `/truths/${encodeURIComponent(truthId)}/audit`);
  return response.data as ValidationEventResponse[];
}

async function fetchFreshnessSummary(): Promise<FreshnessSummaryResponse> {
  const response = await apiClient.get('l5', '/truths/freshness-summary');
  return response.data as FreshnessSummaryResponse;
}

async function fetchStaleTruths(limit = 50, offset = 0): Promise<StaleTruthsResponse> {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) }).toString();
  const response = await apiClient.get('l5', `/truths/stale?${query}`);
  return response.data as StaleTruthsResponse;
}

async function fetchMaturityLadder(): Promise<MaturityLadderResponse> {
  const response = await apiClient.get('l5', '/maturity-ladder');
  return response.data as MaturityLadderResponse;
}

export function useGroundTruths(filters: TruthListFilters = {}, enabled = true) {
  return useQuery<TruthListResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.list(filters),
    queryFn: () => withApiError(fetchTruths(filters), GroundTruthGovernanceApiError),
    enabled,
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useGroundTruthAuditTrail(truthId: string | null, enabled = true) {
  return useQuery<ValidationEventResponse[], GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.audit(truthId ?? ''),
    queryFn: async () => {
      if (!truthId) throw new GroundTruthGovernanceApiError('No truth ID provided');
      return withApiError(fetchTruthAuditTrail(truthId), GroundTruthGovernanceApiError);
    },
    enabled: enabled && !!truthId,
    staleTime: STALE_TIME.activity,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useGroundTruthFreshnessSummary(enabled = true) {
  return useQuery<FreshnessSummaryResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.freshnessSummary(),
    queryFn: () => withApiError(fetchFreshnessSummary(), GroundTruthGovernanceApiError),
    enabled,
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useGroundTruthStaleTruths(limit = 50, offset = 0, enabled = true) {
  return useQuery<StaleTruthsResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.stale(limit, offset),
    queryFn: () => withApiError(fetchStaleTruths(limit, offset), GroundTruthGovernanceApiError),
    enabled,
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useGroundTruthMaturityLadder(enabled = true) {
  return useQuery<MaturityLadderResponse, GroundTruthGovernanceApiError>({
    queryKey: QK.groundTruth.maturityLadder(),
    queryFn: () => withApiError(fetchMaturityLadder(), GroundTruthGovernanceApiError),
    enabled,
    staleTime: STALE_TIME.reference,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}
