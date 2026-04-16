import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { STALE_TIME, BusinessCaseApiError } from './useApiShared';
import {
  parseBusinessCaseNarrativeOutput,
  parseBusinessCaseRoiOutput,
  parseWorkflowResult,
  type ApiWorkflowStepDto,
} from '@/types/api';

export interface UseCase {
  name: string;
  persona: string;
  driver: string;
  roi: string;
  payback: string;
  confidence: number;
}

export interface BusinessCaseData {
  id: string;
  company: string;
  totalValue: string;
  useCases: UseCase[];
  avgPayback: string;
  confidence: number;
  executiveSummary: string;
  generatedAt: string;
}

export interface BusinessCaseListItem {
  id: string;
  name: string;
  company: string;
  status: 'draft' | 'active' | 'archived';
  totalValue: string;
  useCaseCount: number;
  confidence: number;
  createdAt: string;
  updatedAt: string;
  owner: string;
}

export interface BusinessCaseFilters {
  status?: 'draft' | 'active' | 'archived' | 'all';
  search?: string;
  company?: string;
}

export interface CreateBusinessCasePayload {
  name: string;
  company: string;
  description?: string;
}

export interface CreateBusinessCaseResponse {
  workflow_id: string;
  name: string;
  status: string;
  created_at: string;
}

/**
 * Get business case from L4 agent workflow results
 * Note: This queries the L4 workflow results for business_case type workflows
 */
export function useBusinessCase(caseId: string | null) {
  return useQuery({
    queryKey: QK.businessCases.detail(caseId || ''),
    queryFn: async () => {
      if (!caseId) throw new Error('No case ID provided');

      // Query L4 for workflow result
      const response = await apiClient.get('l4', `/workflows/${caseId}/result`);
      const result = parseWorkflowResult(response.data);

      // Parse workflow output into business case format
      const output = result.output || {};
      const steps = result.steps || [];

      // Extract data from workflow steps
      const findAgentStep = (agentName: string): ApiWorkflowStepDto | undefined =>
        steps.find((step) => step.agent === agentName);
      const roiResult = parseBusinessCaseRoiOutput(findAgentStep('ROICalculationAgent')?.result?.output);
      const narrativeResult = parseBusinessCaseNarrativeOutput(findAgentStep('NarrativeSynthesisAgent')?.result?.output);

      // Map use cases
      const useCases: UseCase[] = (roiResult.use_cases || []).map((uc) => ({
        name: uc.name || 'Unknown Use Case',
        persona: uc.persona || 'Unknown',
        driver: uc.value_driver || 'Unknown',
        roi: formatCurrency(uc.roi_value ?? 0),
        payback: `${uc.payback_months ?? 12} mo`,
        confidence: Math.round((uc.confidence ?? 0.8) * 100),
      }));

      // Calculate totals
      const totalValue = roiResult.total_value ?? 0;
      const avgPayback = roiResult.avg_payback_months ?? 12;
      const confidence = Math.round((roiResult.confidence ?? 0.85) * 100);

      return {
        id: caseId,
        company: output.company_name || 'Acme Corp',
        totalValue: formatCurrency(totalValue),
        useCases,
        avgPayback: `${avgPayback} months`,
        confidence,
        executiveSummary: narrativeResult.executive_summary || generateSummary(useCases, totalValue),
        generatedAt: result.completed_at || new Date().toISOString(),
      };
    },
    enabled: !!caseId,
    staleTime: STALE_TIME.stats,
  });
}

function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`;
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(1)}K`;
  }
  return `$${value}`;
}

function generateSummary(useCases: UseCase[], totalValue: number): string {
  if (useCases.length === 0) {
    return 'No use cases available for analysis.';
  }

  const topCase = useCases[0];
  return `${topCase.name} presents the most significant opportunity with an estimated ${topCase.roi} in value. Combined with other identified use cases, the total addressable value is estimated at ${formatCurrency(totalValue)} annually with an average payback period of ${useCases.length > 1 ? 'several months' : '6-9 months'}.`;
}

/**
 * Fetch list of business cases with filtering support
 * 
 * @param filters - Optional filters for status, search, company
 * @returns Query result with business case list
 * 
 * @example
 * ```tsx
 * const { data: cases, isLoading } = useBusinessCases({ status: 'active' });
 * ```
 */
export function useBusinessCases(filters: BusinessCaseFilters = {}) {
  return useQuery({
    queryKey: QK.businessCases.list(filters),
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.status && filters.status !== 'all') params.set('status', filters.status);
      if (filters.search) params.set('search', filters.search);
      if (filters.company) params.set('company', filters.company);

      // Query L4 for business case workflows
      const response = await apiClient.get('l4', `/workflows?type=business_case&${params.toString()}`);
      
      // Transform workflow data to BusinessCaseListItem format
      const items = (response.data?.items || []).map((workflow: { 
        workflow_id: string;
        name?: string;
        status?: string;
        company_name?: string;
        total_value?: number;
        use_case_count?: number;
        confidence?: number;
        created_at?: string;
        updated_at?: string;
        owner?: string;
      }) => ({
        id: workflow.workflow_id,
        name: workflow.name || `Case ${workflow.workflow_id}`,
        company: workflow.company_name || 'Unknown Company',
        status: (workflow.status === 'completed' ? 'active' : workflow.status || 'draft') as BusinessCaseListItem['status'],
        totalValue: formatCurrency(workflow.total_value ?? 0),
        useCaseCount: workflow.use_case_count ?? 0,
        confidence: Math.round((workflow.confidence ?? 0.8) * 100),
        createdAt: workflow.created_at || new Date().toISOString(),
        updatedAt: workflow.updated_at || workflow.created_at || new Date().toISOString(),
        owner: workflow.owner || 'System',
      }));

      return items as BusinessCaseListItem[];
    },
    staleTime: STALE_TIME.list,
  });
}

/**
 * Create a new business case
 *
 * @example
 * ```tsx
 * const createCase = useCreateBusinessCase();
 * createCase.mutate({ name: 'Q2 Expansion', company: 'Acme Corp' });
 * ```
 */
export function useCreateBusinessCase() {
  const queryClient = useQueryClient();

  return useMutation<CreateBusinessCaseResponse, BusinessCaseApiError, CreateBusinessCasePayload>({
    mutationFn: async (payload) => {
      const response = await apiClient.post('l4', '/workflows', {
        workflow_type: 'business_case',
        name: payload.name,
        input: {
          company_name: payload.company,
          description: payload.description,
        },
      });
      return response.data as CreateBusinessCaseResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-cases'] });
    },
    onError: (error) => {
      console.error('Failed to create business case:', error.message);
    },
  });
}

/**
 * Archive a business case
 *
 * @example
 * ```tsx
 * const archiveCase = useArchiveBusinessCase();
 * archiveCase.mutate('case-id-123');
 * ```
 */
export function useArchiveBusinessCase() {
  const queryClient = useQueryClient();

  return useMutation<unknown, BusinessCaseApiError, string>({
    mutationFn: async (caseId) => {
      const response = await apiClient.post('l4', `/workflows/${caseId}/archive`, {});
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['business-cases'] });
    },
    onError: (error) => {
      console.error('Failed to archive business case:', error.message);
    },
  });
}
