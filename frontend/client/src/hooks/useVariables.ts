import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { withApiError, VariableApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

export type VariableType = 'rate' | 'currency' | 'integer' | 'float' | 'boolean' | 'string';
export type SourceType = 'CRM' | 'Billing' | 'ERP' | 'Manual' | 'Model' | 'API' | 'Database';
export type ValidationStatus = 'validated' | 'pending' | 'failed' | 'deprecated';

export interface Variable {
  id: string;
  variable_id: string;
  name: string;
  display_name: string;
  description?: string;
  type: VariableType;
  unit: string;
  source: SourceType;
  binding: string;
  binding_path?: string;
  default_value?: string;
  valid_range?: { min: number; max: number };
  used_in_count: number;
  validation_status: ValidationStatus;
  validation_message?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
  version: string;
}

export interface SourceBinding {
  id: string;
  name: string;
  source_type: SourceType;
  connection_string?: string;
  status: 'connected' | 'disconnected' | 'error';
  last_sync?: string;
  variables_bound: number;
  error_message?: string;
}

const VARIABLE_KEYS = {
  all: ['variables'] as const,
  list: (filters: VariableFilters) => [...VARIABLE_KEYS.all, 'list', filters] as const,
  detail: (id: string) => [...VARIABLE_KEYS.all, 'detail', id] as const,
  bindings: ['variables', 'bindings'] as const,
  stats: ['variables', 'stats'] as const,
};

export interface VariableFilters {
  type?: VariableType | 'all';
  source?: SourceType | 'all';
  status?: ValidationStatus | 'all';
  search?: string;
}

export interface VariableStats {
  total: number;
  validated: number;
  pending: number;
  failed: number;
  manual_sources: number;
  avg_usage: number;
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
  return response.data as Variable[];
}

export function useVariables(filters: VariableFilters = {}) {
  return useQuery<Variable[], VariableApiError>({
    queryKey: VARIABLE_KEYS.list(filters),
    queryFn: () => withApiError(fetchVariables(filters), VariableApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchVariable(variableId: string): Promise<Variable> {
  const response = await apiClient.get('l3', `/variables/${variableId}`);
  return response.data as Variable;
}

export function useVariable(variableId: string | null) {
  return useQuery<Variable, VariableApiError>({
    queryKey: VARIABLE_KEYS.detail(variableId || ''),
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
  return response.data as VariableStats;
}

export function useVariableStats() {
  return useQuery<VariableStats, VariableApiError>({
    queryKey: VARIABLE_KEYS.stats,
    queryFn: () => withApiError(fetchVariableStats(), VariableApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchSourceBindings(): Promise<SourceBinding[]> {
  const response = await apiClient.get('l3', '/variables/bindings');
  return response.data as SourceBinding[];
}

export function useSourceBindings() {
  return useQuery<SourceBinding[], VariableApiError>({
    queryKey: VARIABLE_KEYS.bindings,
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
      queryClient.invalidateQueries({ queryKey: VARIABLE_KEYS.all });
    },
  });
}
