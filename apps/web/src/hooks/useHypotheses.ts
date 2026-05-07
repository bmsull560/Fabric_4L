/**
 * useHypotheses — Value Hypothesis hooks (L4 Agents)
 *
 * Covers all /v1/hypotheses endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer4-agents/src/api/routes/value_hypotheses.py
 * Endpoints: 7
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────

export type HypothesisStatus = 'draft' | 'validated' | 'rejected' | 'converted';

export interface ValueHypothesis {
  id: string;
  account_id: string;
  product_id: string;
  signal_id: string;
  capability_id?: string;
  hypothesis_text: string;
  capability_name?: string;
  value_path_category?: string;
  confidence: number;
  status: HypothesisStatus;
  evidence_ids: string[];
  feedback?: string;
  created_at: string;
  updated_at: string;
}

export interface GenerateHypothesesRequest {
  account_id: string;
  product_ids?: string[];
  max_hypotheses?: number;
  min_confidence?: number;
}

export interface GenerateHypothesesResponse {
  hypotheses: ValueHypothesis[];
  signals_analyzed: number;
  products_matched: number;
}

export interface AccountHypothesesFilters {
  status?: HypothesisStatus;
  value_path_category?: 'revenue_uplift' | 'cost_savings' | 'risk_reduction' | 'blended';
  product_id?: string;
  min_confidence?: number;
  skip?: number;
  limit?: number;
}

export interface AccountHypothesesResponse {
  hypotheses: ValueHypothesis[];
  total: number;
}

export interface ValidateHypothesisRequest {
  new_status: HypothesisStatus;
  feedback?: string;
  evidence_ids?: string[];
  confidence_adjustment?: number;
}

export interface RankHypothesesRequest {
  hypothesis_ids: string[];
  strategy?: 'impact' | 'confidence' | 'balanced' | 'evidence' | 'recency';
}

export interface RankedHypothesis extends ValueHypothesis {
  rank: number;
  composite_score: number;
}

export interface PromoteSignalRequest {
  account_id: string;
  signal_id: string;
  value_path_category?: 'revenue_uplift' | 'cost_savings' | 'risk_reduction' | 'blended';
  product_id?: string;
  product_name?: string;
  capability_id?: string;
  capability_name?: string;
}

export interface PromoteSignalResponse {
  status: string;
  hypothesis_id: string;
  signal_id: string;
  account_id: string;
  value_path_category: string | null;
}

export interface HypothesisStats {
  total: number;
  by_status: Record<HypothesisStatus, number>;
  avg_confidence: number;
  conversion_rate: number;
}

export interface ConvertHypothesisToTreeResponse {
  hypothesis_id: string;
  account_id: string;
  tenant_id: string;
  evidence_ids: string[];
  value_model_id?: string | null;
  tree_id?: string | null;
  status: HypothesisStatus;
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class HypothesisApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'HypothesisApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

function buildHypothesisParams(filters: AccountHypothesesFilters): string {
  const params = new URLSearchParams();
  if (filters.status) params.set('status', filters.status);
  if (filters.value_path_category) params.set('value_path_category', filters.value_path_category);
  if (filters.product_id) params.set('product_id', filters.product_id);
  if (filters.min_confidence != null) params.set('min_confidence', filters.min_confidence.toString());
  if (filters.skip != null) params.set('skip', filters.skip.toString());
  if (filters.limit != null) params.set('limit', filters.limit.toString());
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

async function fetchHypothesis(id: string): Promise<ValueHypothesis> {
  const response = await apiClient.get('l4', `/v1/hypotheses/${id}`);
  return response.data as ValueHypothesis;
}

async function fetchAccountHypotheses(
  accountId: string,
  filters: AccountHypothesesFilters,
): Promise<AccountHypothesesResponse> {
  const response = await apiClient.get(
    'l4',
    `/v1/hypotheses/account/${accountId}${buildHypothesisParams(filters)}`,
  );
  return response.data as AccountHypothesesResponse;
}

async function fetchHypothesisStats(): Promise<HypothesisStats> {
  const response = await apiClient.get('l4', '/v1/hypotheses/summary/stats');
  return response.data as HypothesisStats;
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useHypothesis(id: string | null) {
  return useQuery<ValueHypothesis, HypothesisApiError>({
    queryKey: QK.hypotheses.detail(id || ''),
    queryFn: async () => {
      if (!id) throw new HypothesisApiError('No hypothesis ID provided');
      return withApiError(fetchHypothesis(id), HypothesisApiError);
    },
    enabled: !!id,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useAccountHypotheses(accountId: string | null, filters: AccountHypothesesFilters = {}) {
  return useQuery<AccountHypothesesResponse, HypothesisApiError>({
    queryKey: QK.hypotheses.byAccount(accountId || '', filters),
    queryFn: async () => {
      if (!accountId) throw new HypothesisApiError('No account ID provided');
      return withApiError(fetchAccountHypotheses(accountId, filters), HypothesisApiError);
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useHypothesisStats() {
  return useQuery<HypothesisStats, HypothesisApiError>({
    queryKey: QK.hypotheses.stats(),
    queryFn: () => withApiError(fetchHypothesisStats(), HypothesisApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export function useGenerateHypotheses() {
  const queryClient = useQueryClient();
  return useMutation<GenerateHypothesesResponse, HypothesisApiError, GenerateHypothesesRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l4', '/v1/hypotheses/generate', params);
      return response.data as GenerateHypothesesResponse;
    },
    onSuccess: (_data, { account_id }) => {
      queryClient.invalidateQueries({ queryKey: QK.hypotheses.all });
      queryClient.invalidateQueries({ queryKey: QK.intelligence.briefing(account_id) });
    },
  });
}

export function useValidateHypothesis() {
  const queryClient = useQueryClient();
  return useMutation<
    ValueHypothesis,
    HypothesisApiError,
    { hypothesisId: string; data: ValidateHypothesisRequest }
  >({
    mutationFn: async ({ hypothesisId, data }) => {
      const response = await apiClient.post('l4', `/v1/hypotheses/${hypothesisId}/validate`, data);
      return response.data as ValueHypothesis;
    },
    onSuccess: (_data, { hypothesisId }) => {
      queryClient.invalidateQueries({ queryKey: QK.hypotheses.all });
      queryClient.invalidateQueries({ queryKey: QK.hypotheses.detail(hypothesisId) });
    },
  });
}

export function useDeleteHypothesis() {
  const queryClient = useQueryClient();
  return useMutation<void, HypothesisApiError, string>({
    mutationFn: async (hypothesisId) => {
      await apiClient.delete('l4', `/v1/hypotheses/${hypothesisId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.hypotheses.all });
    },
  });
}

export function useConvertHypothesisToTree() {
  const queryClient = useQueryClient();
  return useMutation<
    ConvertHypothesisToTreeResponse,
    HypothesisApiError,
    { hypothesisId: string }
  >({
    mutationFn: async ({ hypothesisId }) => {
      const response = await apiClient.post('l4', `/v1/hypotheses/${hypothesisId}/convert`, {});
      return response.data as ConvertHypothesisToTreeResponse;
    },
    onSuccess: (_data, { hypothesisId }) => {
      queryClient.invalidateQueries({ queryKey: QK.hypotheses.all });
      queryClient.invalidateQueries({ queryKey: QK.hypotheses.detail(hypothesisId) });
      queryClient.invalidateQueries({ queryKey: QK.accounts.all });
      queryClient.invalidateQueries({ queryKey: QK.valueTrees.all });
    },
  });
}

export function useRankHypotheses() {
  return useMutation<RankedHypothesis[], HypothesisApiError, RankHypothesesRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l4', '/v1/hypotheses/rank', params);
      return response.data as RankedHypothesis[];
    },
  });
}

export function usePromoteSignal() {
  const queryClient = useQueryClient();
  return useMutation<PromoteSignalResponse, HypothesisApiError, PromoteSignalRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l4', '/v1/hypotheses/from-signal', params);
      return response.data as PromoteSignalResponse;
    },
    onSuccess: (_data, { account_id }) => {
      queryClient.invalidateQueries({ queryKey: QK.hypotheses.all });
      queryClient.invalidateQueries({ queryKey: QK.intelligence.briefing(account_id) });
    },
  });
}
