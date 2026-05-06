/**
 * useROICalculator — ROI Calculator hooks (L3 Knowledge Graph)
 *
 * Covers all /v1/roi endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer3-knowledge/src/api/routes/roi_calculator.py
 * Endpoints: 7
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────

export interface ROICalculationRequest {
  deal_size: number;
  implementation_cost: number;
  annual_benefit: number;
  time_horizon_years?: number;
  discount_rate?: number;
  ramp_months?: number;
  product_id?: string;
  account_id?: string;
}

export interface ROICalculationResult {
  id: string;
  npv: number;
  irr: number;
  payback_months: number;
  total_roi_pct: number;
  annual_projections: AnnualProjection[];
  scenarios: Record<string, ScenarioResult>;
  created_at: string;
}

export interface AnnualProjection {
  year: number;
  cost: number;
  benefit: number;
  cumulative_net: number;
  discounted_benefit: number;
}

export interface ScenarioResult {
  npv: number;
  irr: number;
  payback_months: number;
  total_roi_pct: number;
  multiplier: number;
}

export interface ROICompareRequest {
  calculations: ROICalculationRequest[];
  labels?: string[];
}

export interface ROICompareResult {
  comparisons: Array<{
    label: string;
    result: ROICalculationResult;
  }>;
  best_npv_index: number;
  best_roi_index: number;
}

export interface ROITemplate {
  id: string;
  name: string;
  description?: string;
  defaults: Partial<ROICalculationRequest>;
  industry?: string;
  created_at: string;
}

export interface CreateROITemplateRequest {
  name: string;
  description?: string;
  defaults: Partial<ROICalculationRequest>;
  industry?: string;
}

export interface ROICalculationListFilters {
  product_id?: string;
  account_id?: string;
  skip?: number;
  limit?: number;
}

export interface ROICalculationListResponse {
  calculations: ROICalculationResult[];
  total: number;
}

export interface IndustryBenchmark {
  industry: string;
  avg_roi_pct: number;
  avg_payback_months: number;
  avg_npv: number;
  sample_size: number;
}

export interface Benchmark {
  id: string;
  name: string;
  industry: string;
  metric: string;
  value: number;
  unit: string;
  source?: string;
  created_at: string;
  updated_at: string;
}

export interface BenchmarkListResponse {
  benchmarks: Benchmark[];
  total: number;
}

export interface ROICalculationAgentRequest {
  deal_size: number;
  implementation_cost: number;
  annual_benefit: number;
  time_horizon_years?: number;
  discount_rate?: number;
  ramp_months?: number;
  product_id?: string;
  account_id?: string;
  scenario_count?: number;
}

export interface ROICalculationAgentResult extends ROICalculationResult {
  scenarios: Record<string, ScenarioResult>;
  confidence_score?: number;
  recommended_actions?: string[];
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class ROIApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'ROIApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

function buildCalcParams(filters: ROICalculationListFilters): string {
  const params = new URLSearchParams();
  if (filters.product_id) params.set('product_id', filters.product_id);
  if (filters.account_id) params.set('account_id', filters.account_id);
  if (filters.skip != null) params.set('skip', filters.skip.toString());
  if (filters.limit != null) params.set('limit', filters.limit.toString());
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

async function fetchTemplates(): Promise<ROITemplate[]> {
  const response = await apiClient.get('l3', '/v1/roi/templates');
  return response.data as ROITemplate[];
}

async function fetchCalculations(filters: ROICalculationListFilters): Promise<ROICalculationListResponse> {
  const response = await apiClient.get('l3', `/v1/roi/calculations${buildCalcParams(filters)}`);
  return response.data as ROICalculationListResponse;
}

async function fetchCalculation(calcId: string): Promise<ROICalculationResult> {
  const response = await apiClient.get('l3', `/v1/roi/calculations/${calcId}`);
  return response.data as ROICalculationResult;
}

async function fetchBenchmarks(industry: string): Promise<IndustryBenchmark> {
  const response = await apiClient.get('l3', `/v1/roi/benchmarks/${encodeURIComponent(industry)}`);
  return response.data as IndustryBenchmark;
}

async function fetchBenchmarksList(): Promise<BenchmarkListResponse> {
  const response = await apiClient.get('l3', '/v1/roi/benchmarks');
  return response.data as BenchmarkListResponse;
}

async function fetchBenchmarkDetail(benchmarkId: string): Promise<Benchmark> {
  const response = await apiClient.get('l3', `/v1/roi/benchmarks/${encodeURIComponent(benchmarkId)}`);
  return response.data as Benchmark;
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useROITemplates() {
  return useQuery<ROITemplate[], ROIApiError>({
    queryKey: QK.roi.templates(),
    queryFn: () => withApiError(fetchTemplates(), ROIApiError),
    staleTime: STALE_TIME.reference,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useROICalculations(filters: ROICalculationListFilters = {}) {
  return useQuery<ROICalculationListResponse, ROIApiError>({
    queryKey: QK.roi.list(filters),
    queryFn: () => withApiError(fetchCalculations(filters), ROIApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useROICalculation(calcId: string | null) {
  return useQuery<ROICalculationResult, ROIApiError>({
    queryKey: QK.roi.detail(calcId || ''),
    queryFn: async () => {
      if (!calcId) throw new ROIApiError('No calculation ID provided');
      return withApiError(fetchCalculation(calcId), ROIApiError);
    },
    enabled: !!calcId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useIndustryBenchmarks(industry: string | null) {
  return useQuery<IndustryBenchmark, ROIApiError>({
    queryKey: QK.roi.benchmarks(industry || ''),
    queryFn: async () => {
      if (!industry) throw new ROIApiError('No industry provided');
      return withApiError(fetchBenchmarks(industry), ROIApiError);
    },
    enabled: !!industry,
    staleTime: STALE_TIME.reference,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useBenchmarksList() {
  return useQuery<BenchmarkListResponse, ROIApiError>({
    queryKey: QK.roi.benchmarksList(),
    queryFn: () => withApiError(fetchBenchmarksList(), ROIApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useBenchmarkDetail(benchmarkId: string | null) {
  return useQuery<Benchmark, ROIApiError>({
    queryKey: QK.roi.benchmarkDetail(benchmarkId || ''),
    queryFn: async () => {
      if (!benchmarkId) throw new ROIApiError('No benchmark ID provided');
      return withApiError(fetchBenchmarkDetail(benchmarkId), ROIApiError);
    },
    enabled: !!benchmarkId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export function useCalculateROI() {
  const queryClient = useQueryClient();
  return useMutation<ROICalculationResult, ROIApiError, ROICalculationRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/roi/calculate', params);
      return response.data as ROICalculationResult;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.roi.all });
    },
  });
}

export function useCompareROI() {
  return useMutation<ROICompareResult, ROIApiError, ROICompareRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/roi/compare', params);
      return response.data as ROICompareResult;
    },
  });
}

export function useCreateROITemplate() {
  const queryClient = useQueryClient();
  return useMutation<ROITemplate, ROIApiError, CreateROITemplateRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/roi/templates', params);
      return response.data as ROITemplate;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.roi.templates() });
    },
  });
}

export function useROICalculationAgent() {
  const queryClient = useQueryClient();
  return useMutation<ROICalculationAgentResult, ROIApiError, ROICalculationAgentRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/agents/roi-calculation', params);
      return response.data as ROICalculationAgentResult;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.roi.agentCalculation() });
      queryClient.invalidateQueries({ queryKey: QK.roi.all });
    },
  });
}
