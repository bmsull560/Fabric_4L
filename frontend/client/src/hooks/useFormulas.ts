import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, FormulaApiError, STALE_TIME, RETRY_CONFIG, formatZodError } from './useApiShared';
import {
  FormulaSchema,
  FormulaListSchema,
  ApprovalRequestListSchema,
  FormulaEvaluationResultSchema,
  type Formula,
  type FormulaStatus,
  type ApprovalRequest,
  type FormulaEvaluationResult,
} from '@/lib/schemas/formula';

export type { Formula, FormulaStatus, ApprovalRequest, FormulaEvaluationResult };

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
  
  // Runtime validation with Zod
  const parsed = FormulaListSchema.safeParse(response.data);
  if (!parsed.success) {
    if (process.env.NODE_ENV === 'development') {
      console.error('Formula list validation failed:', parsed.error);
    }
    throw new FormulaApiError(formatZodError(parsed.error, 'formula list response'));
  }
  return parsed.data;
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
  
  // Runtime validation with Zod
  const parsed = FormulaSchema.safeParse(response.data);
  if (!parsed.success) {
    if (process.env.NODE_ENV === 'development') {
      console.error('Formula detail validation failed:', parsed.error);
    }
    throw new FormulaApiError(formatZodError(parsed.error, 'formula response'));
  }
  return parsed.data;
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
  
  // Runtime validation with Zod
  const parsed = ApprovalRequestListSchema.safeParse(response.data);
  if (!parsed.success) {
    if (process.env.NODE_ENV === 'development') {
      console.error('Formula approvals validation failed:', parsed.error);
    }
    throw new FormulaApiError(formatZodError(parsed.error, 'formula approvals response'));
  }
  return parsed.data;
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
      if (process.env.NODE_ENV === 'development') {
        console.error('Formula approval failed:', error.message);
      }
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
      if (process.env.NODE_ENV === 'development') {
        console.error('Formula submission failed:', error.message);
      }
    },
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Formula CRUD Operations
// ─────────────────────────────────────────────────────────────────────────────

export interface CreateFormulaInput {
  name: string;
  description?: string;
  expression: string;
  variables: string[];
  pack_id?: string;
}

/**
 * Hook to create a new formula.
 *
 * @returns Mutation result with execute function and loading/error states
 */
export function useCreateFormula() {
  const queryClient = useQueryClient();

  return useMutation<Formula, FormulaApiError, CreateFormulaInput>({
    mutationFn: async (input) => {
      const response = await apiClient.post('l3', '/formulas', input);
      return response.data as Formula;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.formulas.all });
    },
    onError: (error) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('Formula creation failed:', error.message);
      }
    },
  });
}

export interface UpdateFormulaInput {
  formulaId: string;
  name?: string;
  description?: string;
  expression?: string;
  variables?: string[];
  pack_id?: string;
}

/**
 * Hook to update an existing formula.
 *
 * @returns Mutation result with execute function and loading/error states
 */
export function useUpdateFormula() {
  const queryClient = useQueryClient();

  return useMutation<Formula, FormulaApiError, UpdateFormulaInput>({
    mutationFn: async ({ formulaId, ...updates }) => {
      const response = await apiClient.patch('l3', `/formulas/${formulaId}`, updates);
      return response.data as Formula;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: QK.formulas.all });
      queryClient.invalidateQueries({ queryKey: QK.formulas.detail(variables.formulaId) });
    },
    onError: (error) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('Formula update failed:', error.message);
      }
    },
  });
}

/**
 * Hook to delete/archive a formula.
 *
 * @returns Mutation result with execute function and loading/error states
 */
export function useDeleteFormula() {
  const queryClient = useQueryClient();

  return useMutation<unknown, FormulaApiError, string>({
    mutationFn: async (formulaId) => {
      const response = await apiClient.delete('l3', `/formulas/${formulaId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.formulas.all });
    },
    onError: (error) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('Formula deletion failed:', error.message);
      }
    },
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// Formula Evaluation
// ─────────────────────────────────────────────────────────────────────────────

export interface FormulaEvaluationInput {
  formulaId?: string;
  expression?: string;
  inputs: Array<{ name: string; value: number; unit?: string }>;
  output_unit?: string;
}

/**
 * Hook to evaluate a formula with test inputs.
 *
 * @returns Mutation result with execute function and loading/error states
 */
export function useEvaluateFormula() {
  return useMutation<FormulaEvaluationResult, FormulaApiError, FormulaEvaluationInput>({
    mutationFn: async (input) => {
      const response = await apiClient.post('l3', '/formulas/evaluate', input);
      
      // Runtime validation with Zod
      const parsed = FormulaEvaluationResultSchema.safeParse(response.data);
      if (!parsed.success) {
        if (process.env.NODE_ENV === 'development') {
          console.error('Formula evaluation validation failed:', parsed.error);
        }
        throw new FormulaApiError(formatZodError(parsed.error, 'formula evaluation response'));
      }
      return parsed.data;
    },
    onError: (error) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('Formula evaluation failed:', error.message);
      }
    },
  });
}
