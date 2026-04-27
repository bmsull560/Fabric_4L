/**
 * useEvidence — Evidence Library hooks (L3 Knowledge Graph)
 *
 * Covers all /v1/evidence endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer3-knowledge/src/api/routes/evidence.py
 * Endpoints: 9
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────

export interface CaseStudy {
  id: string;
  title: string;
  customer_name: string;
  industry: string;
  product_ids: string[];
  challenge: string;
  solution: string;
  outcome: string;
  metrics_before: Record<string, number>;
  metrics_after: Record<string, number>;
  improvement_pct: Record<string, number>;
  tags: string[];
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface CreateCaseStudyRequest {
  title: string;
  customer_name: string;
  industry: string;
  product_ids?: string[];
  challenge: string;
  solution: string;
  outcome: string;
  metrics_before?: Record<string, number>;
  metrics_after?: Record<string, number>;
  tags?: string[];
  published?: boolean;
}

export interface UpdateCaseStudyRequest {
  title?: string;
  customer_name?: string;
  industry?: string;
  product_ids?: string[];
  challenge?: string;
  solution?: string;
  outcome?: string;
  metrics_before?: Record<string, number>;
  metrics_after?: Record<string, number>;
  tags?: string[];
  published?: boolean;
}

export interface CaseStudyListFilters {
  industry?: string;
  product_id?: string;
  search?: string;
  published?: boolean;
  skip?: number;
  limit?: number;
}

export interface CaseStudyListResponse {
  case_studies: CaseStudy[];
  total: number;
}

export interface IndustryStats {
  industry: string;
  count: number;
}

export interface ProductStats {
  product_id: string;
  product_name: string;
  count: number;
}

export interface EvidenceSearchRequest {
  query: string;
  industry?: string;
  product_id?: string;
  limit?: number;
}

export interface EvidenceSearchResult {
  case_study_id: string;
  title: string;
  relevance_score: number;
  snippet: string;
}

export interface BulkImportRequest {
  case_studies: CreateCaseStudyRequest[];
}

export interface BulkImportResponse {
  created: number;
  errors: string[];
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class EvidenceApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'EvidenceApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

function buildEvidenceParams(filters: CaseStudyListFilters): string {
  const params = new URLSearchParams();
  if (filters.industry) params.set('industry', filters.industry);
  if (filters.product_id) params.set('product_id', filters.product_id);
  if (filters.search) params.set('search', filters.search);
  if (filters.published != null) params.set('published', String(filters.published));
  if (filters.skip != null) params.set('skip', filters.skip.toString());
  if (filters.limit != null) params.set('limit', filters.limit.toString());
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

async function fetchCaseStudies(filters: CaseStudyListFilters): Promise<CaseStudyListResponse> {
  const response = await apiClient.get('l3', `/v1/evidence/case-studies${buildEvidenceParams(filters)}`);
  return response.data as CaseStudyListResponse;
}

async function fetchCaseStudy(id: string): Promise<CaseStudy> {
  const response = await apiClient.get('l3', `/v1/evidence/case-studies/${id}`);
  return response.data as CaseStudy;
}

async function fetchIndustryStats(): Promise<IndustryStats[]> {
  const response = await apiClient.get('l3', '/v1/evidence/stats/by-industry');
  return response.data as IndustryStats[];
}

async function fetchProductStats(): Promise<ProductStats[]> {
  const response = await apiClient.get('l3', '/v1/evidence/stats/by-product');
  return response.data as ProductStats[];
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useCaseStudies(filters: CaseStudyListFilters = {}) {
  return useQuery<CaseStudyListResponse, EvidenceApiError>({
    queryKey: QK.evidence.list(filters),
    queryFn: () => withApiError(fetchCaseStudies(filters), EvidenceApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useCaseStudy(id: string | null) {
  return useQuery<CaseStudy, EvidenceApiError>({
    queryKey: QK.evidence.detail(id || ''),
    queryFn: async () => {
      if (!id) throw new EvidenceApiError('No case study ID provided');
      return withApiError(fetchCaseStudy(id), EvidenceApiError);
    },
    enabled: !!id,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useEvidenceIndustryStats() {
  return useQuery<IndustryStats[], EvidenceApiError>({
    queryKey: QK.evidence.industryStats(),
    queryFn: () => withApiError(fetchIndustryStats(), EvidenceApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useEvidenceProductStats() {
  return useQuery<ProductStats[], EvidenceApiError>({
    queryKey: QK.evidence.productStats(),
    queryFn: () => withApiError(fetchProductStats(), EvidenceApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export function useCreateCaseStudy() {
  const queryClient = useQueryClient();
  return useMutation<CaseStudy, EvidenceApiError, CreateCaseStudyRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/evidence/case-studies', params);
      return response.data as CaseStudy;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
    },
  });
}

export function useUpdateCaseStudy() {
  const queryClient = useQueryClient();
  return useMutation<CaseStudy, EvidenceApiError, { id: string; data: UpdateCaseStudyRequest }>({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put('l3', `/v1/evidence/case-studies/${id}`, data);
      return response.data as CaseStudy;
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
      queryClient.invalidateQueries({ queryKey: QK.evidence.detail(id) });
    },
  });
}

export function useDeleteCaseStudy() {
  const queryClient = useQueryClient();
  return useMutation<void, EvidenceApiError, string>({
    mutationFn: async (id) => {
      await apiClient.delete('l3', `/v1/evidence/case-studies/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
    },
  });
}

export function useBulkImportCaseStudies() {
  const queryClient = useQueryClient();
  return useMutation<BulkImportResponse, EvidenceApiError, BulkImportRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/evidence/case-studies/bulk-import', params);
      return response.data as BulkImportResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
    },
  });
}

export function useEvidenceSearch() {
  return useMutation<EvidenceSearchResult[], EvidenceApiError, EvidenceSearchRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/evidence/search', params);
      return response.data as EvidenceSearchResult[];
    },
  });
}
