import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Error Class ─────────────────────────────────────────────────────────────

export class GovernanceApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'GovernanceApiError';
  }
}

// ── Types ───────────────────────────────────────────────────────────────────

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  status: 'active' | 'suspended' | 'deleted';
  plan?: string;
  created_at: string;
  updated_at?: string;
}

export interface User {
  id: string;
  email: string;
  display_name?: string;
  role: 'super_admin' | 'tenant_admin' | 'member' | 'viewer';
  status: 'active' | 'invited' | 'deactivated';
  tenant_id: string;
  created_at: string;
  last_login_at?: string;
}

export interface ApiKey {
  id: string;
  name: string;
  prefix: string;
  tenant_id: string;
  is_enabled: boolean;
  created_at: string;
  expires_at?: string;
  last_used_at?: string;
}

// ── Query Keys ──────────────────────────────────────────────────────────────

const GOVERNANCE_KEYS = {
  tenants: ['governance', 'tenants'] as const,
  users: (tenantId?: string) => ['governance', 'users', tenantId] as const,
  apiKeys: (tenantId?: string) => ['governance', 'api-keys', tenantId] as const,
};

// ── Fetch Functions ─────────────────────────────────────────────────────────

async function fetchTenants(): Promise<Tenant[]> {
  const response = await apiClient.get('l4', '/tenants');
  return response.data as Tenant[];
}

async function fetchUsers(): Promise<User[]> {
  const response = await apiClient.get('l4', '/users');
  return response.data as User[];
}

async function fetchApiKeys(): Promise<ApiKey[]> {
  const response = await apiClient.get('l4', '/api-keys');
  return response.data as ApiKey[];
}

// ── Hooks ───────────────────────────────────────────────────────────────────

export function useTenants() {
  return useQuery<Tenant[], GovernanceApiError>({
    queryKey: GOVERNANCE_KEYS.tenants,
    queryFn: () => withApiError(fetchTenants(), GovernanceApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useUsers() {
  return useQuery<User[], GovernanceApiError>({
    queryKey: GOVERNANCE_KEYS.users(),
    queryFn: () => withApiError(fetchUsers(), GovernanceApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useApiKeys() {
  return useQuery<ApiKey[], GovernanceApiError>({
    queryKey: GOVERNANCE_KEYS.apiKeys(),
    queryFn: () => withApiError(fetchApiKeys(), GovernanceApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useInviteUser() {
  const queryClient = useQueryClient();

  return useMutation<User, GovernanceApiError, { email: string; role: string }>({
    mutationFn: async (payload) => {
      const response = await apiClient.post('l4', '/users/invite', payload);
      return response.data as User;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GOVERNANCE_KEYS.users() });
    },
  });
}

export function useRevokeApiKey() {
  const queryClient = useQueryClient();

  return useMutation<void, GovernanceApiError, string>({
    mutationFn: async (keyId) => {
      await apiClient.delete('l4', `/api-keys/${keyId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: GOVERNANCE_KEYS.apiKeys() });
    },
  });
}
