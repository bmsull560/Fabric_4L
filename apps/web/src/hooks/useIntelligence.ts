/**
 * useIntelligence — Intelligence Orchestration hooks (L4 Agents)
 *
 * Covers all /v1/accounts and /v1/intelligence endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer4-agents/src/api/routes/intelligence.py
 * Endpoints: 3
 */
import { useQuery } from '@tanstack/react-query';
import { apiGet } from '@/api/typedClient';
import type { l4 } from '@/api/generated';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';
import { type EnrichmentFinancials } from './useEnrichment';

// ── Types ──────────────────────────────────────────────────────────────────

export interface AccountBriefing {
  account_id: string;
  account_name: string;
  generated_at: string;
  enrichment: {
    last_enriched_at?: string;
    sources_used: string[];
    financials?: EnrichmentFinancials;
    tech_stack?: string[];
  };
  signals: {
    total: number;
    by_category: Record<string, number>;
    recent: Array<{
      id: string;
      text: string;
      category: string;
      detected_at: string;
    }>;
  };
  hypotheses: {
    total: number;
    by_status: Record<string, number>;
    top_hypotheses: Array<{
      id: string;
      text: string;
      confidence: number;
      product_name: string;
    }>;
  };
  competitive: {
    competitors: Array<{
      name: string;
      win_rate: number;
      threat_level: string;
    }>;
  };
  roi: {
    best_case_npv?: number;
    payback_months?: number;
    total_roi_pct?: number;
  };
  evidence: {
    matching_case_studies: number;
    top_matches: Array<{
      id: string;
      title: string;
      relevance_score: number;
    }>;
  };
  narrative: {
    latest_id?: string;
    latest_status?: string;
    generated_at?: string;
  };
}

export interface DealReadiness {
  account_id: string;
  overall_score: number;
  label: string;
  components: {
    enrichment_completeness: number;
    signal_strength: number;
    hypothesis_validation: number;
    competitive_position: number;
    roi_confidence: number;
    evidence_coverage: number;
    narrative_readiness: number;
    stakeholder_mapping: number;
  };
  recommendations: string[];
  generated_at: string;
}

export interface PipelineSummary {
  total_accounts: number;
  accounts_by_readiness: Record<string, number>;
  avg_deal_readiness: number;
  top_accounts: Array<{
    account_id: string;
    account_name: string;
    readiness_score: number;
    label: string;
  }>;
  coverage_metrics: {
    enriched_pct: number;
    with_hypotheses_pct: number;
    with_narratives_pct: number;
    with_roi_pct: number;
  };
  generated_at: string;
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class IntelligenceApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'IntelligenceApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

async function fetchAccountBriefing(accountId: string): Promise<AccountBriefing> {
  const response = await apiGet<AccountBriefing>('l4', `/v1/accounts/${accountId}/briefing`);
  return response.data;
}

async function fetchDealReadiness(accountId: string): Promise<DealReadiness> {
  const response = await apiGet<DealReadiness>('l4', `/v1/accounts/${accountId}/deal-readiness`);
  return response.data;
}

async function fetchPipelineSummary(): Promise<PipelineSummary> {
  const response = await apiGet<PipelineSummary>('l4', '/v1/intelligence/pipeline-summary');
  return response.data;
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useAccountBriefing(accountId: string | null) {
  return useQuery<AccountBriefing, IntelligenceApiError>({
    queryKey: QK.intelligence.briefing(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new IntelligenceApiError('No account ID provided');
      return withApiError(fetchAccountBriefing(accountId), IntelligenceApiError);
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useDealReadiness(accountId: string | null) {
  return useQuery<DealReadiness, IntelligenceApiError>({
    queryKey: QK.intelligence.dealReadiness(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new IntelligenceApiError('No account ID provided');
      return withApiError(fetchDealReadiness(accountId), IntelligenceApiError);
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function usePipelineSummary() {
  return useQuery<PipelineSummary, IntelligenceApiError>({
    queryKey: QK.intelligence.pipeline(),
    queryFn: () => withApiError(fetchPipelineSummary(), IntelligenceApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}
