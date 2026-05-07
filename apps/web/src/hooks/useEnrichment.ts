/**
 * useEnrichment — Account Enrichment hooks (L4 Agents)
 *
 * Covers all /v1/enrichment endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer4-agents/src/api/routes/enrichment.py
 * Endpoints: 4
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/api/typedClient';
import type { l4 } from '@/api/generated';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────

export interface EnrichmentResult {
  account_id: string;
  sources_used: string[];
  fields_updated: string[];
  enriched_at: string;
  financials?: EnrichmentFinancials;
  tech_stack?: string[];
  executives?: EnrichmentExecutive[];
  news_items?: EnrichmentNewsItem[];
}

export interface EnrichmentFinancials {
  revenue?: number;
  growth_rate?: number;
  employees?: number;
  market_cap?: number;
  fiscal_year?: string;
}

export interface EnrichmentExecutive {
  name: string;
  title: string;
  linkedin_url?: string;
}

export interface EnrichmentNewsItem {
  headline: string;
  source: string;
  url: string;
  published_at: string;
  sentiment?: string;
}

export interface EnrichAccountRequest {
  force?: boolean;
  sources?: string[];
}

export interface BatchEnrichRequest {
  account_ids: string[];
  force?: boolean;
  sources?: string[];
}

export interface BatchEnrichResponse {
  results: Array<{
    account_id: string;
    status: 'success' | 'failed' | 'skipped';
    message?: string;
  }>;
  total_enriched: number;
  total_failed: number;
  total_skipped: number;
}

export interface EnrichmentCoverageStats {
  total_accounts: number;
  enriched_accounts: number;
  stale_accounts: number;
  never_enriched: number;
  coverage_pct: number;
  avg_sources_per_account: number;
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class EnrichmentApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'EnrichmentApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

async function fetchEnrichmentStatus(): Promise<EnrichmentCoverageStats> {
  const response = await apiGet<EnrichmentCoverageStats>('l4', '/v1/enrichment/status');
  return response.data;
}

async function fetchEnrichmentDetails(accountId: string): Promise<EnrichmentResult> {
  const response = await apiGet<EnrichmentResult>('l4', `/v1/enrichment/${accountId}`);
  return response.data;
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useEnrichmentStatus() {
  return useQuery<EnrichmentCoverageStats, EnrichmentApiError>({
    queryKey: QK.enrichment.status(),
    queryFn: () => withApiError(fetchEnrichmentStatus(), EnrichmentApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useEnrichmentDetails(accountId: string | null) {
  return useQuery<EnrichmentResult, EnrichmentApiError>({
    queryKey: QK.enrichment.detail(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new EnrichmentApiError('No account ID provided');
      return withApiError(fetchEnrichmentDetails(accountId), EnrichmentApiError);
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export function useEnrichAccount() {
  const queryClient = useQueryClient();
  return useMutation<EnrichmentResult, EnrichmentApiError, { accountId: string; params?: EnrichAccountRequest }>({
    mutationFn: async ({ accountId, params }) => {
      const response = await apiPost<EnrichmentResult>('l4', `/v1/enrichment/${accountId}`, params ?? {});
      return response.data;
    },
    onSuccess: (_data, { accountId }) => {
      queryClient.invalidateQueries({ queryKey: QK.enrichment.all });
      queryClient.invalidateQueries({ queryKey: QK.enrichment.detail(accountId) });
      // Also invalidate account detail since enrichment updates account fields
      queryClient.invalidateQueries({ queryKey: QK.accounts.detail(accountId) });
    },
  });
}

export function useBatchEnrich() {
  const queryClient = useQueryClient();
  return useMutation<BatchEnrichResponse, EnrichmentApiError, BatchEnrichRequest>({
    mutationFn: async (params) => {
      const response = await apiPost<BatchEnrichResponse>('l4', '/v1/enrichment/batch', params);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.enrichment.all });
      queryClient.invalidateQueries({ queryKey: QK.accounts.all });
    },
  });
}
