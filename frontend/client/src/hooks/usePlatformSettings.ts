/**
 * Platform Settings React Query Hooks
 * 
 * Server state management for tenant/platform configuration:
 * - usePlatformSettings: Fetch tenant settings
 * - useUpdatePlatformSettings: Update tenant configuration
 * 
 * All hooks handle loading, error, and caching automatically.
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Error Class ─────────────────────────────────────────────────────────────

export class PlatformSettingsApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'PlatformSettingsApiError';
  }
}

// ── Types ───────────────────────────────────────────────────────────────────

export interface TenantSettings {
  tenant_id: string;
  tenant_name: string;
  features: {
    advanced_analytics: boolean;
    custom_integrations: boolean;
    ai_assistant: boolean;
    audit_trail: boolean;
  };
  limits: {
    max_users: number;
    max_api_calls_per_day: number;
    storage_gb: number;
  };
  notifications: {
    email_alerts: boolean;
    slack_webhook?: string;
    webhook_url?: string;
  };
  security: {
    require_2fa: boolean;
    session_timeout_minutes: number;
    ip_allowlist: string[];
  };
  branding?: {
    logo_url?: string;
    primary_color?: string;
    favicon_url?: string;
  };
  updated_at: string;
  updated_by?: string;
}

export interface UpdateSettingsPayload {
  tenant_name?: string;
  features?: Partial<TenantSettings['features']>;
  notifications?: Partial<TenantSettings['notifications']>;
  security?: Partial<TenantSettings['security']>;
  branding?: Partial<TenantSettings['branding']>;
}

// ── Fetch Functions ─────────────────────────────────────────────────────────

async function fetchPlatformSettings(): Promise<TenantSettings> {
  const response = await apiClient.get('l4', '/tenant/settings');
  return response.data as TenantSettings;
}

async function updatePlatformSettings(payload: UpdateSettingsPayload): Promise<TenantSettings> {
  const response = await apiClient.patch('l4', '/tenant/settings', payload);
  return response.data as TenantSettings;
}

// ── Hooks ───────────────────────────────────────────────────────────────────

/**
 * Fetch tenant platform settings
 * 
 * @returns Query result with tenant settings and loading/error states
 * 
 * @example
 * ```tsx
 * const { data: settings, isLoading } = usePlatformSettings();
 * ```
 */
export function usePlatformSettings() {
  return useQuery<TenantSettings, PlatformSettingsApiError>({
    queryKey: QK.platform.settings,
    queryFn: () => withApiError(fetchPlatformSettings(), PlatformSettingsApiError),
    staleTime: STALE_TIME.reference,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/**
 * Update tenant platform settings
 * 
 * @returns Mutation result with update function
 * 
 * @example
 * ```tsx
 * const updateSettings = useUpdatePlatformSettings();
 * updateSettings.mutate({ 
 *   features: { advanced_analytics: true } 
 * });
 * ```
 */
export function useUpdatePlatformSettings() {
  const queryClient = useQueryClient();

  return useMutation<TenantSettings, PlatformSettingsApiError, UpdateSettingsPayload>({
    mutationFn: (payload) => withApiError(updatePlatformSettings(payload), PlatformSettingsApiError),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.platform.settings });
    },
  });
}

// ── Query Key Extension ─────────────────────────────────────────────────────

// Add to QK in queryKeys.ts:
// platform: {
//   settings: ['platform', 'settings'] as const,
// },
