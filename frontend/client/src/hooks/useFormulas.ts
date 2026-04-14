import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, FormulaApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

export type FormulaStatus = 'active' | 'draft' | 'pending' | 'deprecated' | 'archived';

export interface Formula {
  id: string;
  formula_id: string;
  name: string;
  description?: string;
  pack_id?: string;
  pack_name?: string;
  version: string;
  status: FormulaStatus;
  owner?: string;
  updated_at: string;
  created_at: string;
  used_in_count: number;
  governance_score?: number;
  last_reviewed?: string;
  reviewers?: string[];
  expression?: string;
  variables?: string[];
}

export interface ApprovalRequest {
  id: string;
  formula_id: string;
  formula_name: string;
  submitted_by: string;
  submitted_at: string;
  change_summary: string;
  previous_version: string;
  status: 'pending' | 'approved' | 'rejected';
}

/** Parameters for formula approval action */
export interface ApproveFormulaParams {
  formulaId: string;
  action: 'approve' | 'reject' | 'request_changes';
  reason?: string;
}


export interface FormulaFilters {
  status?: FormulaStatus | 'all';
  search?: string;
  pack_id?: string;
}

// Re-export for backward compatibility
export { FormulaApiError } from './useApiShared';

async function fetchFormulas(filters: FormulaFilters): Promise<Formula[]> {
  const params = new URLSearchParams();
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.search) params.set('search', filters.search);
  if (filters.pack_id) params.set('pack_id', filters.pack_id);

  const response = await apiClient.get('l3', `/formulas?${params.toString()}`);
  return response.data as Formula[];
}

/**
 * Hook to fetch a list of formulas with filtering support.
 *
 * @param filters - Optional filters for status, search query, or pack ID
 * @returns Query result with Formula array and loading/error states
 */
export function useFormulas(filters: FormulaFilters = {}) {
  return useQuery<Formula[], FormulaApiError>({
    queryKey: QK.formulas.list(filters),
    queryFn: () => withApiError(fetchFormulas(filters), FormulaApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchFormula(formulaId: string): Promise<Formula> {
  const response = await apiClient.get('l3', `/formulas/${formulaId}`);
  return response.data as Formula;
}

/**
 * Hook to fetch a single formula by ID.
 *
 * @param formulaId - The formula ID to fetch, or null to disable the query
 * @returns Query result with Formula data and loading/error states
 */
export function useFormula(formulaId: string | null) {
  return useQuery<Formula, FormulaApiError>({
    queryKey: QK.formulas.detail(formulaId || ''),
    queryFn: async () => {
      if (!formulaId) throw new FormulaApiError('No formula ID provided');
      return withApiError(fetchFormula(formulaId), FormulaApiError);
    },
    enabled: !!formulaId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchFormulaApprovals(): Promise<ApprovalRequest[]> {
  const response = await apiClient.get('l3', '/formulas/approvals/pending');
  return response.data as ApprovalRequest[];
}

/**
 * Hook to fetch pending formula approval requests.
 *
 * @returns Query result with approval requests array
 */
export function useFormulaApprovals() {
  return useQuery<ApprovalRequest[], FormulaApiError>({
    queryKey: QK.formulas.approvals,
    queryFn: () => withApiError(fetchFormulaApprovals(), FormulaApiError),
    staleTime: STALE_TIME.approvals,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/**
 * Hook to approve, reject, or request changes on a formula.
 *
 * @returns Mutation result with execute function and loading/error states
 */
export function useApproveFormula() {
  const queryClient = useQueryClient();

  return useMutation<unknown, FormulaApiError, ApproveFormulaParams>({
    mutationFn: async ({ formulaId, action, reason }) => {
      const response = await apiClient.post('l3', `/formulas/${formulaId}/approve`, {
        action,
        reason,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.formulas.all });
    },
    onError: (error) => {
      console.error('Formula approval failed:', error.message);
    },
  });
}

/**
 * Hook to submit a formula for approval.
 *
 * @returns Mutation result with execute function and loading/error states
 */
export function useSubmitFormula() {
  const queryClient = useQueryClient();

  return useMutation<unknown, FormulaApiError, string>({
    mutationFn: async (formulaId) => {
      const response = await apiClient.post('l3', `/formulas/${formulaId}/submit`, {});
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.formulas.all });
    },
    onError: (error) => {
      console.error('Formula submission failed:', error.message);
    },
  });
}
