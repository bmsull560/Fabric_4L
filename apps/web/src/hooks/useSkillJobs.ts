/**
 * useSkillJobs — TanStack Query hooks for Layer 1 Source Intelligence Skills
 *
 * Covers:
 *   Mutations:
 *     useCreateLicensingCompanyIntakeJob  — POST /api/v1/ingestion/jobs/licensing-company-intake
 *     useCreateProspectResearchJob        — POST /api/v1/ingestion/jobs/prospect-research
 *
 *   Queries:
 *     useSourceCorpora                    — GET /api/v1/ingestion/source-corpora
 *     useSourceCorpus                     — GET /api/v1/ingestion/source-corpora/{id}
 *     useAccountIntelligencePackets       — GET /api/v1/ingestion/account-intelligence-packets
 *     useAccountIntelligencePacket        — GET /api/v1/ingestion/account-intelligence-packets/{id}
 *     useJobSkillOutput                   — GET /api/v1/ingestion/jobs/{id}/skill-output
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/api/typedClient';
import { QK } from './queryKeys';
import { STALE_TIME, RETRY_CONFIG } from './useApiShared';

// =============================================================================
// Types
// =============================================================================

export interface CreateLicensingCompanyIntakeRequest {
  target_id: string;
  company_name: string;
  company_id?: string | null;
  priority?: number;
  override_config?: Record<string, unknown> | null;
}

export interface CreateProspectResearchRequest {
  target_id: string;
  account_name: string;
  account_id?: string | null;
  priority?: number;
  override_config?: Record<string, unknown> | null;
}

export interface SkillJobResponse {
  job_id: string;
  status: string;
  job_type: string;
  skill_name: string;
  queue_position: number;
  queue_position_metadata?: Record<string, unknown> | null;
}

export interface SourceCorpusSummary {
  id: string;
  company_name: string;
  company_id: string | null;
  corpus_type: string;
  source_count: number;
  extraction_status: string;
  created_at: string;
}

export interface SourceCorpusDetail extends SourceCorpusSummary {
  tenant_id: string;
  source_groups: Array<{ source_type: string; count: number }>;
  candidate_concepts: string[];
  provenance: Array<Record<string, unknown>>;
  updated_at: string;
}

export interface SourceCorpusListResponse {
  items: SourceCorpusSummary[];
  total: number;
  limit: number;
  next_cursor: string | null;
}

export interface AccountIntelligencePacketSummary {
  id: string;
  account_name: string;
  account_id: string | null;
  packet_type: string;
  observed_signal_count: number;
  high_confidence_signal_count: number;
  created_at: string;
}

export interface AccountIntelligencePacketDetail extends AccountIntelligencePacketSummary {
  tenant_id: string;
  company_profile: Record<string, unknown>;
  observed_signals: Array<Record<string, unknown>>;
  likely_pain_areas: string[];
  likely_stakeholders: string[];
  source_references: Array<Record<string, unknown>>;
  confidence_summary: Record<string, unknown>;
  next_recommended_events: string[];
  updated_at: string;
}

export interface AccountIntelligencePacketListResponse {
  items: AccountIntelligencePacketSummary[];
  total: number;
  limit: number;
  next_cursor: string | null;
}

export interface SkillOutputEnvelope {
  output_contract: 'SourceCorpus' | 'AccountIntelligencePacket';
  data: SourceCorpusDetail | AccountIntelligencePacketDetail;
}

export interface SourceCorpusFilters {
  company_id?: string;
  job_id?: string;
  extraction_status?: string;
  created_after?: string;
  created_before?: string;
  limit?: number;
  cursor?: string;
}

export interface AccountIntelligencePacketFilters {
  account_id?: string;
  job_id?: string;
  created_after?: string;
  created_before?: string;
  limit?: number;
  cursor?: string;
}

// =============================================================================
// Helpers
// =============================================================================

function buildQueryString(params: Record<string, string | number | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== '');
  if (entries.length === 0) return '';
  return '?' + entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join('&');
}

// =============================================================================
// Mutations
// =============================================================================

/**
 * Create a licensing company ontology intake job.
 * Invalidates the source-corpora list on success.
 */
export function useCreateLicensingCompanyIntakeJob() {
  const queryClient = useQueryClient();

  return useMutation<SkillJobResponse, Error, CreateLicensingCompanyIntakeRequest>({
    mutationFn: async (payload) => {
      const resp = await apiPost<SkillJobResponse>(
        'l1',
        '/api/v1/ingestion/jobs/licensing-company-intake',
        payload,
      );
      return resp.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.skillOutputs.corpora() });
      queryClient.invalidateQueries({ queryKey: QK.ingestion.jobs() });
    },
  });
}

/**
 * Create a prospect research job.
 * Invalidates the account-intelligence-packets list on success.
 */
export function useCreateProspectResearchJob() {
  const queryClient = useQueryClient();

  return useMutation<SkillJobResponse, Error, CreateProspectResearchRequest>({
    mutationFn: async (payload) => {
      const resp = await apiPost<SkillJobResponse>(
        'l1',
        '/api/v1/ingestion/jobs/prospect-research',
        payload,
      );
      return resp.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.skillOutputs.packets() });
      queryClient.invalidateQueries({ queryKey: QK.ingestion.jobs() });
    },
  });
}

// =============================================================================
// Queries — SourceCorpus
// =============================================================================

/**
 * List SourceCorpus records for the authenticated tenant.
 * Summary-only — provenance arrays are not included.
 */
export function useSourceCorpora(filters?: SourceCorpusFilters) {
  const qs = buildQueryString({
    company_id: filters?.company_id,
    job_id: filters?.job_id,
    extraction_status: filters?.extraction_status,
    created_after: filters?.created_after,
    created_before: filters?.created_before,
    limit: filters?.limit,
    cursor: filters?.cursor,
  });

  return useQuery<SourceCorpusListResponse, Error>({
    queryKey: QK.skillOutputs.corpora(filters),
    queryFn: async () => {
      const resp = await apiGet<SourceCorpusListResponse>(
        'l1',
        `/api/v1/ingestion/source-corpora${qs}`,
      );
      return resp.data;
    },
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/**
 * Get a single SourceCorpus by ID including full provenance.
 * Only fetches when corpusId is non-null.
 */
export function useSourceCorpus(corpusId: string | null) {
  return useQuery<SourceCorpusDetail, Error>({
    queryKey: QK.skillOutputs.corpus(corpusId ?? ''),
    queryFn: async () => {
      const resp = await apiGet<SourceCorpusDetail>(
        'l1',
        `/api/v1/ingestion/source-corpora/${corpusId}`,
      );
      return resp.data;
    },
    enabled: !!corpusId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// =============================================================================
// Queries — AccountIntelligencePacket
// =============================================================================

/**
 * List AccountIntelligencePacket records for the authenticated tenant.
 * Summary-only — source_references arrays are not included.
 */
export function useAccountIntelligencePackets(filters?: AccountIntelligencePacketFilters) {
  const qs = buildQueryString({
    account_id: filters?.account_id,
    job_id: filters?.job_id,
    created_after: filters?.created_after,
    created_before: filters?.created_before,
    limit: filters?.limit,
    cursor: filters?.cursor,
  });

  return useQuery<AccountIntelligencePacketListResponse, Error>({
    queryKey: QK.skillOutputs.packets(filters),
    queryFn: async () => {
      const resp = await apiGet<AccountIntelligencePacketListResponse>(
        'l1',
        `/api/v1/ingestion/account-intelligence-packets${qs}`,
      );
      return resp.data;
    },
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/**
 * Get a single AccountIntelligencePacket by ID including full source references.
 * Only fetches when packetId is non-null.
 */
export function useAccountIntelligencePacket(packetId: string | null) {
  return useQuery<AccountIntelligencePacketDetail, Error>({
    queryKey: QK.skillOutputs.packet(packetId ?? ''),
    queryFn: async () => {
      const resp = await apiGet<AccountIntelligencePacketDetail>(
        'l1',
        `/api/v1/ingestion/account-intelligence-packets/${packetId}`,
      );
      return resp.data;
    },
    enabled: !!packetId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// =============================================================================
// Queries — Skill output by job
// =============================================================================

/**
 * Get the skill-specific output for a completed job.
 * Returns an envelope with output_contract and the full data object.
 * Only fetches when jobId is non-null.
 */
export function useJobSkillOutput(jobId: string | null) {
  return useQuery<SkillOutputEnvelope, Error>({
    queryKey: QK.skillOutputs.jobOutput(jobId ?? ''),
    queryFn: async () => {
      const resp = await apiGet<SkillOutputEnvelope>(
        'l1',
        `/api/v1/ingestion/jobs/${jobId}/skill-output`,
      );
      return resp.data;
    },
    enabled: !!jobId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}
