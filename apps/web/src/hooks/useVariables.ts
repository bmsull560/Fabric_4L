import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { ZodError } from 'zod';
import { apiClient } from '@/api/client';
import { createLogger } from '@/lib/telemetry';
import { QK } from './queryKeys';
import { withApiError, VariableApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';
import {
  VariableSchema,
  VariableListSchema,
  SourceBindingListSchema,
  VariableStatsSchema,
  type Variable,
  type VariableType,
  type SourceType,
  type ValidationStatus,
  type SourceBinding,
  type VariableStats,
} from '@/lib/schemas/variable';

const log = createLogger('useVariables');

/**
 * Format Zod validation errors into a human-readable string.
 */
function formatZodError(error: ZodError, context: string): string {
  const details = error.issues.map((e: { path: (string | number | symbol)[]; message: string }) => `${String(e.path)}: ${e.message}`).join(', ');
  return `Invalid ${context}: ${details}`;
}

export type { Variable, VariableType, SourceType, ValidationStatus, SourceBinding, VariableStats };

export interface VariableFilters {
  type?: VariableType | 'all';
  source?: SourceType | 'all';
  status?: ValidationStatus | 'all';
  search?: string;
}

// Re-export for backward compatibility
export { VariableApiError } from './useApiShared';

async function fetchVariables(filters: VariableFilters): Promise<Variable[]> {
  const params = new URLSearchParams();
  if (filters.type && filters.type !== 'all') params.set('type', filters.type);
  if (filters.source && filters.source !== 'all') params.set('source', filters.source);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  if (filters.search) params.set('search', filters.search);

  const response = await apiClient.get('l3', `/variables?${params.toString()}`);
  
  // Runtime validation with Zod
  const parsed = VariableListSchema.safeParse(response.data);
  if (!parsed.success) {
    log.error('Variable list validation failed', { error: parsed.error });
    throw new VariableApiError(formatZodError(parsed.error, 'variable list response'));
  }
  return parsed.data;
}

export function useVariables(filters: VariableFilters = {}) {
  return useQuery<Variable[], VariableApiError>({
    queryKey: QK.variables.list(filters),
    queryFn: () => withApiError(fetchVariables(filters), VariableApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchVariable(variableId: string): Promise<Variable> {
  const response = await apiClient.get('l3', `/variables/${variableId}`);
  
  // Runtime validation with Zod
  const parsed = VariableSchema.safeParse(response.data);
  if (!parsed.success) {
    log.error('Variable detail validation failed', { error: parsed.error });
    throw new VariableApiError(formatZodError(parsed.error, 'variable response'));
  }
  return parsed.data;
}

export function useVariable(variableId: string | null) {
  return useQuery<Variable, VariableApiError>({
    queryKey: QK.variables.detail(variableId || ''),
    queryFn: async () => {
      if (!variableId) throw new VariableApiError('No variable ID provided');
      return withApiError(fetchVariable(variableId), VariableApiError);
    },
    enabled: !!variableId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchVariableStats(): Promise<VariableStats> {
  const response = await apiClient.get('l3', '/variables/stats');
  
  // Runtime validation with Zod
  const parsed = VariableStatsSchema.safeParse(response.data);
  if (!parsed.success) {
    log.error('Variable stats validation failed', { error: parsed.error });
    throw new VariableApiError(formatZodError(parsed.error, 'variable stats response'));
  }
  return parsed.data;
}

export function useVariableStats() {
  return useQuery<VariableStats, VariableApiError>({
    queryKey: QK.variables.stats,
    queryFn: () => withApiError(fetchVariableStats(), VariableApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchSourceBindings(): Promise<SourceBinding[]> {
  const response = await apiClient.get('l3', '/variables/bindings');
  
  // Runtime validation with Zod
  const parsed = SourceBindingListSchema.safeParse(response.data);
  if (!parsed.success) {
    log.error('Source binding list validation failed', { error: parsed.error });
    throw new VariableApiError(formatZodError(parsed.error, 'source binding list response'));
  }
  return parsed.data;
}

export function useSourceBindings() {
  return useQuery<SourceBinding[], VariableApiError>({
    queryKey: QK.variables.bindings,
    queryFn: () => withApiError(fetchSourceBindings(), VariableApiError),
    staleTime: STALE_TIME.bindings,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useValidateVariable() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (variableId: string) => {
      if (!variableId) throw new VariableApiError('Variable ID is required');
      const response = await apiClient.post('l3', `/variables/${variableId}/validate`, {});
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.variables.all });
    },
  });
}
