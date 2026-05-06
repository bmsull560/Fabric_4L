import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { createLogger } from '@/lib/telemetry';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

export type CRMProvider = 'salesforce' | 'hubspot';
export type SyncStatus = 'synced' | 'pending' | 'failed' | 'stale';

export interface Account {
  id: string;
  name: string;
  domain: string;
  industry?: string;
  stage?: string;
  region?: string;
  segment?: string;
  owner_id?: string;
  owner_name?: string;
  provider: CRMProvider;
  provider_record_id: string;
  sync_status: SyncStatus;
  last_synced_at?: string;
  employees?: number;
  annual_revenue?: number;
  headquarters?: string;
  website?: string;
  opportunities?: Opportunity[];
  created_at: string;
  updated_at: string;
}

export interface Opportunity {
  provider_opportunity_id: string;
  name: string;
  stage: string;
  value?: number;
  probability?: number;
  close_date?: string;
  pipeline?: string;
  last_synced_at?: string;
}

export interface AccountActivity {
  account_id: string;
  interactions: Interaction[];
  total_count: number;
  summary: string;
}

export interface Interaction {
  id: string;
  type: string;
  date: string;
  subject: string;
  duration_minutes?: number;
  notes?: string;
  outcome?: string;
  sender?: string;
}

export interface AccountSyncStatusInfo {
  provider: CRMProvider;
  status: 'idle' | 'running' | 'failed';
  last_sync_at?: string;
  last_successful_sync_at?: string;
  records_synced: number;
  records_updated: number;
  records_failed: number;
  error_message?: string;
}

export interface SyncResult {
  sync_id: string;
  status: 'completed' | 'partial';
  provider?: CRMProvider;
  message: string;
  stats: {
    provider: string;
    synced: number;
    updated: number;
    failed: number;
    errors: string[];
  }[];
}

// Domain-specific error class
export class AccountApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'AccountApiError';
  }
}


const log = createLogger('useAccounts');

export interface AccountFilters {
  provider?: CRMProvider | 'all';
  stage?: string;
  industry?: string;
  region?: string;
  segment?: string;
  owner_id?: string;
  sync_status?: SyncStatus | 'all';
  search?: string;
  page?: number;
  page_size?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface AccountListResponse {
  items: Account[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

export interface FilterOptions {
  industries: string[];
  stages: string[];
  providers: CRMProvider[];
  owners: { id: string; name: string }[];
}

async function fetchAccounts(filters: AccountFilters): Promise<AccountListResponse> {
  const params = new URLSearchParams();
  if (filters.provider && filters.provider !== 'all') params.set('provider', filters.provider);
  if (filters.stage) params.set('stage', filters.stage);
  if (filters.industry) params.set('industry', filters.industry);
  if (filters.region) params.set('region', filters.region);
  if (filters.segment) params.set('segment', filters.segment);
  if (filters.owner_id) params.set('owner_id', filters.owner_id);
  if (filters.sync_status && filters.sync_status !== 'all') params.set('sync_status', filters.sync_status);
  if (filters.search) params.set('q', filters.search);
  if (filters.page) params.set('page', filters.page.toString());
  if (filters.page_size) params.set('page_size', filters.page_size.toString());
  if (filters.sort_by) params.set('sort_by', filters.sort_by);
  if (filters.sort_order) params.set('sort_order', filters.sort_order);

  const response = await apiClient.get('l4', `/accounts?${params.toString()}`);
  // Backend returns { items, total, page, page_size, has_more }
  // Map to frontend contract for backward compatibility
  const data = response.data as {
    items?: Account[];
    accounts?: Account[];
    total: number;
    page: number;
    page_size: number;
    has_more?: boolean;
  };
  return {
    items: data.items ?? data.accounts ?? [],
    total: data.total,
    page: data.page,
    page_size: data.page_size,
    has_more: data.has_more ?? false,
  };
}

export function useAccounts(filters: AccountFilters = {}) {
  return useQuery<AccountListResponse, AccountApiError>({
    queryKey: QK.accounts.list(filters),
    queryFn: () => withApiError(fetchAccounts(filters), AccountApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchAccount(accountId: string): Promise<Account> {
  const response = await apiClient.get('l4', `/accounts/${accountId}`);
  return response.data as Account;
}

export function useAccount(accountId: string | null) {
  return useQuery<Account, AccountApiError>({
    queryKey: QK.accounts.detail(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new AccountApiError('No account ID provided');
      return withApiError(fetchAccount(accountId), AccountApiError);
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchAccountActivity(accountId: string, sinceDays: number = 90): Promise<AccountActivity> {
  const response = await apiClient.get('l4', `/accounts/${accountId}/activity?since_days=${sinceDays}`);
  return response.data as AccountActivity;
}

export function useAccountActivity(accountId: string | null, sinceDays?: number) {
  return useQuery<AccountActivity, AccountApiError>({
    queryKey: QK.accounts.activity(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new AccountApiError('No account ID provided');
      return withApiError(fetchAccountActivity(accountId, sinceDays), AccountApiError);
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.activity,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchSyncStatus(): Promise<AccountSyncStatusInfo[]> {
  const response = await apiClient.get('l4', '/accounts/sync-status');
  return response.data as AccountSyncStatusInfo[];
}

export function useAccountSyncStatus() {
  return useQuery<AccountSyncStatusInfo[], AccountApiError>({
    queryKey: QK.accounts.syncStatus,
    queryFn: () => withApiError(fetchSyncStatus(), AccountApiError),
    staleTime: STALE_TIME.poll,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

async function fetchFilterOptions(): Promise<FilterOptions> {
  const response = await apiClient.get('l4', '/accounts/filters');
  return response.data as FilterOptions;
}

export function useAccountFilterOptions() {
  return useQuery<FilterOptions, AccountApiError>({
    queryKey: QK.accounts.filters,
    queryFn: () => withApiError(fetchFilterOptions(), AccountApiError),
    staleTime: STALE_TIME.activity,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export interface CreateAccountParams {
  name: string;
  domain?: string;
  industry?: string;
  stage?: string;
  region?: string;
  employees?: number;
  annual_revenue?: number;
  headquarters?: string;
  website?: string;
  enrichment_input?: string;
}

export interface CreateAccountResponse {
  account: Account;
  workflow_id?: string;
}

export interface SyncAccountsParams {
  provider?: CRMProvider;
  account_ids?: string[];
  force_refresh?: boolean;
}

export function useCreateAccount() {
  const queryClient = useQueryClient();

  return useMutation<CreateAccountResponse, AccountApiError, CreateAccountParams>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l4', '/accounts', {
        name: params.name,
        domain: params.domain,
        industry: params.industry,
        stage: params.stage || 'prospect',
        region: params.region,
        employees: params.employees,
        annual_revenue: params.annual_revenue,
        headquarters: params.headquarters,
        website: params.website,
        enrichment_input: params.enrichment_input,
      });
      return response.data as CreateAccountResponse;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.accounts.list({}) });
    },
    onError: (error) => {
      log.error('CreateAccount failed', { error: error.message });
    },
  });
}

export function useSyncAccounts() {
  const queryClient = useQueryClient();

  return useMutation<SyncResult, AccountApiError, SyncAccountsParams>({
    mutationFn: async (params = {}) => {
      const response = await apiClient.post('l4', '/accounts/sync', {
        provider: params.provider,
        account_ids: params.account_ids,
        force_refresh: params.force_refresh || false,
      });
      return response.data as SyncResult;
    },
    onSuccess: () => {
      // Invalidate all account queries to refresh data
      queryClient.invalidateQueries({ queryKey: QK.accounts.list({}) });
    },
    onError: (error) => {
      log.error('SyncAccounts failed', { error: error.message });
    },
  });
}

export function useRefreshAccount() {
  const queryClient = useQueryClient();

  return useMutation<Account, AccountApiError, string>({
    mutationFn: async (accountId: string) => {
      if (!accountId || accountId.trim() === '') {
        throw new AccountApiError('Account ID is required');
      }
      const response = await apiClient.post('l4', `/accounts/${accountId}/refresh`, {});
      return response.data as Account;
    },
    onSuccess: (data) => {
      // Invalidate to get fresh data from server
      queryClient.invalidateQueries({ queryKey: QK.accounts.detail(data.id) });
      queryClient.invalidateQueries({ queryKey: QK.accounts.list({}) });
    },
    onError: (error, accountId) => {
      log.error('RefreshAccount failed', { accountId, error: error.message });
    },
  });
}
