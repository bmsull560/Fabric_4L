import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { createLogger } from '@/lib/telemetry';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

const log = createLogger('useIntegrations');

export type CRMProvider = 'salesforce' | 'hubspot';

export interface Integration {
  id: string;
  tenant_id: string;
  provider: CRMProvider;
  enabled: boolean;
  instance_url: string | null;
  sync_interval_minutes: number;
  sync_batch_size: number;
  last_sync_at: string | null;
  last_successful_sync_at: string | null;
  records_synced: number;
  records_updated: number;
  records_failed: number;
  status: 'idle' | 'running' | 'failed' | 'pending' | 'degraded';
  last_error_message: string | null;
  has_refresh_token: boolean;
  created_at: string;
  updated_at: string;
}

export interface IntegrationConfig {
  provider: CRMProvider;
  enabled: boolean;
  instance_url?: string;
  sync_interval_minutes: number;
  sync_batch_size: number;
}

export interface IntegrationCreateRequest {
  enabled: boolean;
  api_key: string;
  api_secret?: string;
  instance_url?: string;
  sync_interval_minutes: number;
  sync_batch_size: number;
  salesforce_org_id?: string;
}

export interface ConnectionTestResult {
  success: boolean;
  message: string;
  details?: Record<string, unknown>;
  error_code?: string;
}

export interface SyncTriggerResult {
  sync_id: string;
  status: string;
  provider: string;
}

export interface IntegrationListResponse {
  integrations: Integration[];
}

export class IntegrationApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'IntegrationApiError';
  }
}

async function fetchIntegrations(): Promise<Integration[]> {
  const response = await apiClient.get('l4', '/integrations');
  const data = response.data as IntegrationListResponse;
  return data.integrations;
}

export function useIntegrations() {
  return useQuery<Integration[], IntegrationApiError>({
    queryKey: QK.integrations.list,
    queryFn: () => withApiError(fetchIntegrations(), IntegrationApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchIntegration(provider: CRMProvider): Promise<Integration> {
  const response = await apiClient.get('l4', `/integrations/${provider}`);
  return response.data as Integration;
}

export function useIntegration(provider: CRMProvider | null) {
  return useQuery<Integration, IntegrationApiError>({
    queryKey: QK.integrations.detail(provider || ''),
    queryFn: async () => {
      if (!provider) throw new IntegrationApiError('No provider specified');
      return withApiError(fetchIntegration(provider), IntegrationApiError);
    },
    enabled: !!provider,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useCreateOrUpdateIntegration() {
  const queryClient = useQueryClient();

  return useMutation<Integration, IntegrationApiError, { provider: CRMProvider; data: IntegrationCreateRequest }>({
    mutationFn: async ({ provider, data }) => {
      const response = await apiClient.post('l4', `/integrations/${provider}`, data);
      return response.data as Integration;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.integrations.all });
    },
    onError: (error) => {
      log.error('CreateOrUpdate failed', { error: error.message });
    },
  });
}

export function useDeleteIntegration() {
  const queryClient = useQueryClient();

  return useMutation<void, IntegrationApiError, CRMProvider>({
    mutationFn: async (provider) => {
      await apiClient.delete('l4', `/integrations/${provider}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.integrations.all });
    },
    onError: (error) => {
      log.error('Delete failed', { error: error.message });
    },
  });
}

export function useTestIntegration() {
  return useMutation<ConnectionTestResult, IntegrationApiError, CRMProvider>({
    mutationFn: async (provider) => {
      const response = await apiClient.post('l4', `/integrations/${provider}/test`, {});
      return response.data as ConnectionTestResult;
    },
    onError: (error) => {
      log.error('Test failed', { error: error.message });
    },
  });
}

export function useSyncIntegration() {
  const queryClient = useQueryClient();

  return useMutation<SyncTriggerResult, IntegrationApiError, CRMProvider>({
    mutationFn: async (provider) => {
      const response = await apiClient.post('l4', `/integrations/${provider}/sync`, {});
      return response.data as SyncTriggerResult;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.integrations.all });
    },
    onError: (error) => {
      log.error('Sync failed', { error: error.message });
    },
  });
}
