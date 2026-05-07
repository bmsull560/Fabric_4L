/**
 * useNarratives — Narrative Builder hooks (L4 Agents)
 *
 * Covers all /v1/narratives endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer4-agents/src/api/routes/narratives.py
 * Endpoints: 5
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/api/typedClient';
import type { l4 } from '@/api/generated';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────

export type NarrativeTone = 'executive' | 'technical' | 'financial' | 'consultative';
export type NarrativeAudience = 'c_suite' | 'vp_director' | 'technical_buyer' | 'champion' | 'evaluation_committee';
export type NarrativeStatus = 'draft' | 'review' | 'approved' | 'delivered';

export interface NarrativeSection {
  section_type: string;
  title: string;
  summary: string;
  detail: Record<string, unknown>;
  data_source: string;
  caller_supplied: boolean;
  verified: boolean;
}

export interface Narrative {
  id: string;
  account_id: string;
  title: string;
  tone: NarrativeTone;
  audience: NarrativeAudience;
  status: NarrativeStatus;
  sections: NarrativeSection[];
  created_at: string;
  updated_at: string;
}

export interface GenerateNarrativeRequest {
  account_id: string;
  tone?: NarrativeTone;
  audience?: NarrativeAudience;
  sections?: string[];
  title?: string;
}

export interface NarrativeListFilters {
  account_id?: string;
  status?: NarrativeStatus;
  skip?: number;
  limit?: number;
}

export interface NarrativeListResponse {
  narratives: Narrative[];
  total: number;
}

export interface UpdateNarrativeStatusRequest {
  status: NarrativeStatus;
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class NarrativeApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'NarrativeApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

function buildNarrativeParams(filters: NarrativeListFilters): string {
  const params = new URLSearchParams();
  if (filters.account_id) params.set('account_id', filters.account_id);
  if (filters.status) params.set('status', filters.status);
  if (filters.skip != null) params.set('skip', filters.skip.toString());
  if (filters.limit != null) params.set('limit', filters.limit.toString());
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

async function fetchNarratives(filters: NarrativeListFilters): Promise<NarrativeListResponse> {
  const response = await apiGet<NarrativeListResponse>('l4', `/v1/narratives${buildNarrativeParams(filters)}`);
  return response.data;
}

async function fetchNarrative(id: string): Promise<Narrative> {
  const response = await apiGet<Narrative>('l4', `/v1/narratives/${id}`);
  return response.data;
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useNarratives(filters: NarrativeListFilters = {}) {
  return useQuery<NarrativeListResponse, NarrativeApiError>({
    queryKey: QK.narratives.list(filters),
    queryFn: () => withApiError(fetchNarratives(filters), NarrativeApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useNarrative(id: string | null) {
  return useQuery<Narrative, NarrativeApiError>({
    queryKey: QK.narratives.detail(id || ''),
    queryFn: async () => {
      if (!id) throw new NarrativeApiError('No narrative ID provided');
      return withApiError(fetchNarrative(id), NarrativeApiError);
    },
    enabled: !!id,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export function useGenerateNarrative() {
  const queryClient = useQueryClient();
  return useMutation<Narrative, NarrativeApiError, GenerateNarrativeRequest>({
    mutationFn: async (params) => {
      const response = await apiPost<Narrative>('l4', '/v1/narratives/generate', params);
      return response.data;
    },
    onSuccess: (_data, { account_id }) => {
      queryClient.invalidateQueries({ queryKey: QK.narratives.all });
      queryClient.invalidateQueries({ queryKey: QK.intelligence.briefing(account_id) });
    },
  });
}

export function useUpdateNarrativeStatus() {
  const queryClient = useQueryClient();
  return useMutation<
    Narrative,
    NarrativeApiError,
    { narrativeId: string; data: UpdateNarrativeStatusRequest }
  >({
    mutationFn: async ({ narrativeId, data }) => {
      const response = await apiPatch<Narrative>('l4', `/v1/narratives/${narrativeId}/status`, data);
      return response.data;
    },
    onSuccess: (_data, { narrativeId }) => {
      queryClient.invalidateQueries({ queryKey: QK.narratives.all });
      queryClient.invalidateQueries({ queryKey: QK.narratives.detail(narrativeId) });
    },
  });
}

export function useDeleteNarrative() {
  const queryClient = useQueryClient();
  return useMutation<void, NarrativeApiError, string>({
    mutationFn: async (narrativeId) => {
      await apiDelete<void>('l4', `/v1/narratives/${narrativeId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.narratives.all });
    },
  });
}
