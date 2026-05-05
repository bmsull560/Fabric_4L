/**
 * useEvidence — Evidence Library hooks (L3 Knowledge Graph)
 *
 * Covers all /v1/evidence endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer3-knowledge/src/api/routes/evidence.py
 * Endpoints: 9
 */
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import { QK } from "./queryKeys";
import {
  withApiError,
  BaseApiError,
  STALE_TIME,
  RETRY_CONFIG,
} from "./useApiShared";
import {
  parseBulkImportResponse,
  parseCaseStudy,
  parseCaseStudyListResponse,
  parseCaseStudyMutationResponse,
  parseDeleteCaseStudyResponse,
  parseEvidenceSearchResponse,
  parseEvidenceStatsResponse,
  type BulkImportResponse,
  type CaseStudy,
  type CaseStudyListResponse,
  type CaseStudyMutationResponse,
  type DeleteCaseStudyResponse,
  type EvidenceSearchResponse,
  type EvidenceSearchResult,
  type IndustryStats,
  type ProductStats,
} from "@/lib/schemas/evidence";

// ── Types ──────────────────────────────────────────────────────────────────

export type {
  BulkImportResponse,
  CaseStudy,
  CaseStudyListResponse,
  CaseStudyMutationResponse,
  DeleteCaseStudyResponse,
  EvidenceSearchResponse,
  EvidenceSearchResult,
  IndustryStats,
  ProductStats,
} from "@/lib/schemas/evidence";

export interface CaseStudyOutcomeInput {
  metric: string;
  before_value?: string | null;
  after_value?: string | null;
  improvement_pct?: number | null;
  time_to_achieve_days?: number | null;
}

export interface CreateCaseStudyRequest {
  title: string;
  content: string;
  industry: string;
  summary?: string | null;
  company_name?: string | null;
  company_size?: string | null;
  products_used?: string[] | null;
  pain_signals_addressed?: string[] | null;
  outcomes?: CaseStudyOutcomeInput[] | null;
  time_to_value_days?: number | null;
  deal_size_usd?: number | null;
  published_date?: string | null;
  tags?: string[] | null;
}

export interface UpdateCaseStudyRequest {
  title?: string;
  content?: string;
  summary?: string | null;
  industry?: string;
  company_name?: string | null;
  company_size?: string | null;
  products_used?: string[] | null;
  pain_signals_addressed?: string[] | null;
  outcomes?: CaseStudyOutcomeInput[] | null;
  time_to_value_days?: number | null;
  deal_size_usd?: number | null;
  tags?: string[] | null;
}

export interface CaseStudyListFilters {
  industry?: string;
  company_size?: string;
  product?: string;
  product_id?: string;
  tag?: string;
  min_deal_size?: number;
  search?: string;
  published?: boolean;
  skip?: number;
  limit?: number;
  offset?: number;
}

export interface EvidenceSearchRequest {
  query: string;
  evidence_types?: string[] | null;
  limit?: number;
  industry?: string;
  product_id?: string;
}

export interface BulkImportRequest {
  case_studies: CreateCaseStudyRequest[];
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class EvidenceApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = "EvidenceApiError";
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

function buildEvidenceParams(filters: CaseStudyListFilters): string {
  const params = new URLSearchParams();
  if (filters.industry) params.set("industry", filters.industry);
  if (filters.company_size) params.set("company_size", filters.company_size);
  if (filters.product ?? filters.product_id) {
    params.set("product", filters.product ?? filters.product_id ?? "");
  }
  if (filters.tag) params.set("tag", filters.tag);
  if (filters.min_deal_size != null) {
    params.set("min_deal_size", filters.min_deal_size.toString());
  }
  if (filters.limit != null) params.set("limit", filters.limit.toString());
  const offset = filters.offset ?? filters.skip;
  if (offset != null) params.set("offset", offset.toString());
  const qs = params.toString();
  return qs ? `?${qs}` : "";
}

async function fetchCaseStudies(
  filters: CaseStudyListFilters
): Promise<CaseStudyListResponse> {
  const response = await apiClient.get(
    "l3",
    `/v1/evidence/case-studies${buildEvidenceParams(filters)}`
  );
  return parseCaseStudyListResponse(response.data);
}

async function fetchCaseStudy(id: string): Promise<CaseStudy> {
  const response = await apiClient.get("l3", `/v1/evidence/case-studies/${id}`);
  return parseCaseStudy(response.data);
}

async function fetchIndustryStats(): Promise<IndustryStats> {
  const response = await apiClient.get("l3", "/v1/evidence/stats/by-industry");
  return parseEvidenceStatsResponse(response.data);
}

async function fetchProductStats(): Promise<ProductStats> {
  const response = await apiClient.get("l3", "/v1/evidence/stats/by-product");
  return parseEvidenceStatsResponse(response.data);
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
    queryKey: QK.evidence.detail(id || ""),
    queryFn: async () => {
      if (!id) throw new EvidenceApiError("No case study ID provided");
      return withApiError(fetchCaseStudy(id), EvidenceApiError);
    },
    enabled: !!id,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useEvidenceIndustryStats() {
  return useQuery<IndustryStats, EvidenceApiError>({
    queryKey: QK.evidence.industryStats(),
    queryFn: () => withApiError(fetchIndustryStats(), EvidenceApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useEvidenceProductStats() {
  return useQuery<ProductStats, EvidenceApiError>({
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
  return useMutation<
    CaseStudyMutationResponse,
    EvidenceApiError,
    CreateCaseStudyRequest
  >({
    mutationFn: async params => {
      const response = await apiClient.post(
        "l3",
        "/v1/evidence/case-studies",
        params
      );
      return parseCaseStudyMutationResponse(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
    },
  });
}

export function useUpdateCaseStudy() {
  const queryClient = useQueryClient();
  return useMutation<
    CaseStudyMutationResponse,
    EvidenceApiError,
    { id: string; data: UpdateCaseStudyRequest }
  >({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(
        "l3",
        `/v1/evidence/case-studies/${id}`,
        data
      );
      return parseCaseStudyMutationResponse(response.data);
    },
    onSuccess: (_data, { id }) => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
      queryClient.invalidateQueries({ queryKey: QK.evidence.detail(id) });
    },
  });
}

export function useDeleteCaseStudy() {
  const queryClient = useQueryClient();
  return useMutation<DeleteCaseStudyResponse, EvidenceApiError, string>({
    mutationFn: async id => {
      const response = await apiClient.delete(
        "l3",
        `/v1/evidence/case-studies/${id}`
      );
      return parseDeleteCaseStudyResponse(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
    },
  });
}

export function useBulkImportCaseStudies() {
  const queryClient = useQueryClient();
  return useMutation<BulkImportResponse, EvidenceApiError, BulkImportRequest>({
    mutationFn: async params => {
      const response = await apiClient.post(
        "l3",
        "/v1/evidence/case-studies/bulk-import",
        params
      );
      return parseBulkImportResponse(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.evidence.all });
    },
  });
}

export function useEvidenceSearch() {
  return useMutation<
    EvidenceSearchResponse,
    EvidenceApiError,
    EvidenceSearchRequest
  >({
    mutationFn: async params => {
      const response = await apiClient.post("l3", "/v1/evidence/search", {
        query: params.query,
        evidence_types: params.evidence_types,
        limit: params.limit,
      });
      return parseEvidenceSearchResponse(response.data);
    },
  });
}
