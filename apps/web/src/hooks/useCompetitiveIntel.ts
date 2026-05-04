/**
 * useCompetitiveIntel — Competitive Intelligence hooks (L3 Knowledge Graph)
 *
 * Covers all /v1/competitive endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer3-knowledge/src/api/routes/competitive_intel.py
 * Endpoints: 10
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────

export interface Competitor {
  id: string;
  name: string;
  website?: string;
  description?: string;
  market_position?: string;
  pricing_tier?: string;
  strengths: string[];
  weaknesses: string[];
  products_competed: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateCompetitorRequest {
  name: string;
  website?: string;
  description?: string;
  market_position?: string;
  pricing_tier?: string;
  strengths?: string[];
  weaknesses?: string[];
}

export interface UpdateCompetitorRequest {
  name?: string;
  website?: string;
  description?: string;
  market_position?: string;
  pricing_tier?: string;
  strengths?: string[];
  weaknesses?: string[];
}

export interface CompetitorListFilters {
  search?: string;
  market_position?: string;
  skip?: number;
  limit?: number;
}

export interface CompetitorListResponse {
  competitors: Competitor[];
  total: number;
}

export interface Battlecard {
  id: string;
  competitor_id: string;
  product_id: string;
  key_differentiators: string[];
  objection_handlers: Record<string, string>;
  talk_tracks: string[];
  created_at: string;
  updated_at: string;
}

export interface CreateBattlecardRequest {
  product_id: string;
  key_differentiators?: string[];
  objection_handlers?: Record<string, string>;
  talk_tracks?: string[];
}

export type WinLossOutcome = 'win' | 'loss' | 'no_decision';

export interface WinLossRecord {
  id: string;
  competitor_id: string;
  account_id: string;
  outcome: WinLossOutcome;
  deal_size?: number;
  reason?: string;
  notes?: string;
  recorded_at: string;
}

export interface RecordWinLossRequest {
  competitor_id: string;
  account_id: string;
  outcome: WinLossOutcome;
  deal_size?: number;
  reason?: string;
  notes?: string;
}

export interface WinLossSummary {
  competitor_id: string;
  competitor_name: string;
  wins: number;
  losses: number;
  no_decisions: number;
  win_rate: number;
  avg_deal_size: number;
  top_loss_reasons: string[];
}

export interface LandscapeEntry {
  competitor_id: string;
  competitor_name: string;
  market_position: string;
  win_rate: number;
  overlap_score: number;
  threat_level: string;
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class CompetitiveIntelApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'CompetitiveIntelApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

function buildCompetitorParams(filters: CompetitorListFilters): string {
  const params = new URLSearchParams();
  if (filters.search) params.set('search', filters.search);
  if (filters.market_position) params.set('market_position', filters.market_position);
  if (filters.skip != null) params.set('skip', filters.skip.toString());
  if (filters.limit != null) params.set('limit', filters.limit.toString());
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

async function fetchCompetitors(filters: CompetitorListFilters): Promise<CompetitorListResponse> {
  const response = await apiClient.get('l3', `/v1/competitive/competitors${buildCompetitorParams(filters)}`);
  return response.data as CompetitorListResponse;
}

async function fetchCompetitor(id: string): Promise<Competitor> {
  const response = await apiClient.get('l3', `/v1/competitive/competitors/${id}`);
  return response.data as Competitor;
}

async function fetchBattlecards(competitorId: string): Promise<Battlecard[]> {
  const response = await apiClient.get('l3', `/v1/competitive/competitors/${competitorId}/battlecards`);
  return response.data as Battlecard[];
}

async function fetchWinLossSummary(competitorId?: string): Promise<WinLossSummary[]> {
  const qs = competitorId ? `?competitor_id=${competitorId}` : '';
  const response = await apiClient.get('l3', `/v1/competitive/win-loss/summary${qs}`);
  return response.data as WinLossSummary[];
}

async function fetchLandscape(productId?: string): Promise<LandscapeEntry[]> {
  const qs = productId ? `?product_id=${productId}` : '';
  const response = await apiClient.get('l3', `/v1/competitive/landscape${qs}`);
  return response.data as LandscapeEntry[];
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useCompetitors(filters: CompetitorListFilters = {}) {
  return useQuery<CompetitorListResponse, CompetitiveIntelApiError>({
    queryKey: QK.competitive.list(filters),
    queryFn: () => withApiError(fetchCompetitors(filters), CompetitiveIntelApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useCompetitor(id: string | null) {
  return useQuery<Competitor, CompetitiveIntelApiError>({
    queryKey: QK.competitive.detail(id || ''),
    queryFn: async () => {
      if (!id) throw new CompetitiveIntelApiError('No competitor ID provided');
      return withApiError(fetchCompetitor(id), CompetitiveIntelApiError);
    },
    enabled: !!id,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useBattlecards(competitorId: string | null) {
  return useQuery<Battlecard[], CompetitiveIntelApiError>({
    queryKey: QK.competitive.battlecards(competitorId || ''),
    queryFn: async () => {
      if (!competitorId) throw new CompetitiveIntelApiError('No competitor ID provided');
      return withApiError(fetchBattlecards(competitorId), CompetitiveIntelApiError);
    },
    enabled: !!competitorId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useWinLossSummary(competitorId?: string) {
  return useQuery<WinLossSummary[], CompetitiveIntelApiError>({
    queryKey: QK.competitive.winLoss(competitorId),
    queryFn: () => withApiError(fetchWinLossSummary(competitorId), CompetitiveIntelApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useLandscape(productId?: string) {
  return useQuery<LandscapeEntry[], CompetitiveIntelApiError>({
    queryKey: QK.competitive.landscape(productId),
    queryFn: () => withApiError(fetchLandscape(productId), CompetitiveIntelApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export function useCreateCompetitor() {
  const queryClient = useQueryClient();
  return useMutation<Competitor, CompetitiveIntelApiError, CreateCompetitorRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/competitive/competitors', params);
      return response.data as Competitor;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.competitive.all });
    },
  });
}

export function useUpdateCompetitor() {
  const queryClient = useQueryClient();
  return useMutation<Competitor, CompetitiveIntelApiError, { id: string; data: UpdateCompetitorRequest }>({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put('l3', `/v1/competitive/competitors/${id}`, data);
      return response.data as Competitor;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: QK.competitive.all });
      queryClient.invalidateQueries({ queryKey: QK.competitive.detail(id) });
    },
  });
}

export function useDeleteCompetitor() {
  const queryClient = useQueryClient();
  return useMutation<void, CompetitiveIntelApiError, string>({
    mutationFn: async (id) => {
      await apiClient.delete('l3', `/v1/competitive/competitors/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.competitive.all });
    },
  });
}

export function useCreateBattlecard() {
  const queryClient = useQueryClient();
  return useMutation<Battlecard, CompetitiveIntelApiError, { competitorId: string; data: CreateBattlecardRequest }>({
    mutationFn: async ({ competitorId, data }) => {
      const response = await apiClient.post('l3', `/v1/competitive/competitors/${competitorId}/battlecards`, data);
      return response.data as Battlecard;
    },
    onSuccess: (_data, { competitorId }) => {
      queryClient.invalidateQueries({ queryKey: QK.competitive.battlecards(competitorId) });
      queryClient.invalidateQueries({ queryKey: QK.competitive.all });
    },
  });
}

export function useRecordWinLoss() {
  const queryClient = useQueryClient();
  return useMutation<WinLossRecord, CompetitiveIntelApiError, RecordWinLossRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/competitive/win-loss', params);
      return response.data as WinLossRecord;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.competitive.all });
    },
  });
}
