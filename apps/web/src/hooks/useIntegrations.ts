import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiGet, apiPost, apiDelete } from "@/api/typedClient";
import type { l4 } from "@/api/generated";
import { createLogger } from "@/lib/telemetry";
import { QK } from "./queryKeys";
import {
  withApiError,
  BaseApiError,
  STALE_TIME,
  RETRY_CONFIG,
} from "./useApiShared";
import {
  parseConnectionTestResult,
  parseIntegration,
  parseIntegrations,
  parseOAuthAuthorizeResult,
  parseSyncTriggerResult,
  type CRMProvider,
  type ConnectionTestResult,
  type Integration,
  type IntegrationListResponse,
  type OAuthAuthorizeResult,
  type SyncTriggerResult,
} from "@/lib/schemas/integrations";

const log = createLogger("useIntegrations");

export type {
  CRMProvider,
  ConnectionTestResult,
  Integration,
  IntegrationListResponse,
  OAuthAuthorizeResult,
  SyncTriggerResult,
};

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

export interface SalesforceOAuthAuthorizeRequest {
  return_to: string;
}

export class IntegrationApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = "IntegrationApiError";
  }
}

async function fetchIntegrations(): Promise<Integration[]> {
  const response = await apiGet<l4.components["schemas"]["IntegrationListResponse"]>("l4", "/integrations");
  return parseIntegrations(response.data);
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
  const response = await apiGet<l4.components["schemas"]["IntegrationStatusResponse"]>("l4", `/integrations/${provider}`);
  return parseIntegration(response.data);
}

export function useIntegration(provider: CRMProvider | null) {
  return useQuery<Integration, IntegrationApiError>({
    queryKey: QK.integrations.detail(provider || ""),
    queryFn: async () => {
      if (!provider) throw new IntegrationApiError("No provider specified");
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

  return useMutation<
    Integration,
    IntegrationApiError,
    { provider: CRMProvider; data: IntegrationCreateRequest }
  >({
    mutationFn: async ({ provider, data }) => {
      const response = await apiPost<l4.components["schemas"]["IntegrationStatusResponse"]>(
        "l4",
        `/integrations/${provider}`,
        data
      );
      return parseIntegration(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.integrations.all });
    },
    onError: error => {
      log.error("CreateOrUpdate failed", { error: error.message });
    },
  });
}

export function useDeleteIntegration() {
  const queryClient = useQueryClient();

  return useMutation<void, IntegrationApiError, CRMProvider>({
    mutationFn: async provider => {
      await apiDelete<void>("l4", `/integrations/${provider}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.integrations.all });
    },
    onError: error => {
      log.error("Delete failed", { error: error.message });
    },
  });
}

export function useTestIntegration() {
  return useMutation<ConnectionTestResult, IntegrationApiError, CRMProvider>({
    mutationFn: async provider => {
      const response = await apiPost<l4.components["schemas"]["ConnectionTestResponse"]>(
        "l4",
        `/integrations/${provider}/test`,
        {}
      );
      return parseConnectionTestResult(response.data);
    },
    onError: error => {
      log.error("Test failed", { error: error.message });
    },
  });
}

export function useSyncIntegration() {
  const queryClient = useQueryClient();

  return useMutation<SyncTriggerResult, IntegrationApiError, CRMProvider>({
    mutationFn: async provider => {
      const response = await apiPost<l4.components["schemas"]["SyncTriggerResponse"]>(
        "l4",
        `/integrations/${provider}/sync`,
        {}
      );
      return parseSyncTriggerResult(response.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.integrations.all });
    },
    onError: error => {
      log.error("Sync failed", { error: error.message });
    },
  });
}

export function useStartSalesforceOAuth() {
  return useMutation<
    OAuthAuthorizeResult,
    IntegrationApiError,
    SalesforceOAuthAuthorizeRequest
  >({
    mutationFn: async data => {
      const response = await apiPost<unknown>(
        "l4",
        "/integrations/salesforce/oauth/authorize",
        data
      );
      return parseOAuthAuthorizeResult(response.data);
    },
    onError: error => {
      log.error("Salesforce OAuth start failed", { error: error.message });
    },
  });
}
