import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { createWrapper, createMockResponse } from '../test-utils';
import { QK } from './queryKeys';
import {
  useAccounts,
  useAccount,
  useAccountSyncStatus,
  useSyncAccounts,
  useRefreshAccount,
  useAccountFilterOptions,
  type Account,
  type CRMProvider,
  type AccountListResponse,
  type AccountSyncStatusInfo,
  type SyncResult,
  type FilterOptions,
} from './useAccounts';

// Mock the apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Sample data
const sampleAccount: Account = {
  id: 'acc-001',
  name: 'Acme Corp',
  domain: 'acme.com',
  provider: 'salesforce' as CRMProvider,
  provider_record_id: '001ABC',
  sync_status: 'synced',
  industry: 'Technology',
  stage: 'customer',
  owner_id: 'usr-001',
  owner_name: 'John Doe',
  employees: 500,
  annual_revenue: 50000000,
  headquarters: 'San Francisco, CA',
  website: 'https://acme.com',
  last_synced_at: '2024-01-15T10:00:00Z',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T10:00:00Z',
};

const sampleAccountsResponse: AccountListResponse = {
  items: [sampleAccount],
  total: 1,
  page: 1,
  page_size: 20,
  has_more: false,
};

const sampleSyncStatus: AccountSyncStatusInfo[] = [
  {
    provider: 'salesforce' as CRMProvider,
    status: 'idle',
    last_sync_at: '2024-01-15T10:00:00Z',
    last_successful_sync_at: '2024-01-15T10:00:00Z',
    records_synced: 100,
    records_updated: 5,
    records_failed: 0,
  },
  {
    provider: 'hubspot' as CRMProvider,
    status: 'idle',
    last_sync_at: '2024-01-15T09:30:00Z',
    last_successful_sync_at: '2024-01-15T09:30:00Z',
    records_synced: 50,
    records_updated: 2,
    records_failed: 0,
  },
];

const sampleSyncResult: SyncResult = {
  sync_id: 'sync-20240115120000',
  status: 'completed',
  provider: 'salesforce' as CRMProvider,
  message: 'Synced 100 accounts, 0 failed',
  stats: [
    {
      provider: 'salesforce',
      synced: 0,
      updated: 100,
      failed: 0,
      errors: [],
    },
  ],
};

const sampleFilterOptions: FilterOptions = {
  industries: ['Technology', 'Healthcare', 'Finance'],
  stages: ['prospect', 'qualified', 'opportunity', 'customer'],
  providers: ['salesforce', 'hubspot'] as CRMProvider[],
  owners: [
    { id: 'usr-001', name: 'John Doe' },
    { id: 'usr-002', name: 'Jane Smith' },
  ],
};

describe('useAccounts', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('useAccounts hook', () => {
    it('should fetch accounts list successfully', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse(sampleAccountsResponse)
      );

      const { result } = renderHook(() => useAccounts({ page: 1, page_size: 20 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith('l4', '/accounts?page=1&page_size=20');
      expect(result.current.data).toEqual(sampleAccountsResponse);
    });

    it('should apply filters correctly', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse({ ...sampleAccountsResponse, total: 0, accounts: [] })
      );

      renderHook(
        () =>
          useAccounts({
            provider: 'salesforce',
            stage: 'customer',
            industry: 'Technology',
            owner_id: 'usr-001',
            sync_status: 'synced',
            search: 'acme',
            page: 1,
            page_size: 10,
            sort_by: 'name',
            sort_order: 'asc',
          }),
        { wrapper: createWrapper() }
      );

      await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

      const callUrl = (apiClient.get as Mock).mock.calls[0][1];
      expect(callUrl).toContain('provider=salesforce');
      expect(callUrl).toContain('stage=customer');
      expect(callUrl).toContain('industry=Technology');
      expect(callUrl).toContain('owner_id=usr-001');
      expect(callUrl).toContain('sync_status=synced');
      expect(callUrl).toContain('q=acme');
      expect(callUrl).toContain('page=1');
      expect(callUrl).toContain('page_size=10');
      expect(callUrl).toContain('sort_by=name');
      expect(callUrl).toContain('sort_order=asc');
    });

    it('should handle empty response', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(
        createMockResponse({ accounts: [], total: 0, page: 1, page_size: 20 })
      );

      const { result } = renderHook(() => useAccounts({}), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.items).toHaveLength(0);
      expect(result.current.data?.total).toBe(0);
    });

    it('should handle API error', async () => {
      (apiClient.get as Mock).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useAccounts({}), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error).toBeDefined();
      expect(result.current.error?.name).toBe('AccountApiError');
    });
  });

  describe('useAccount hook', () => {
    it('should fetch single account successfully', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse(sampleAccount));

      const { result } = renderHook(() => useAccount('acc-001'), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith('l4', '/accounts/acc-001');
      expect(result.current.data?.id).toBe('acc-001');
      expect(result.current.data?.name).toBe('Acme Corp');
    });

    it('should not fetch when accountId is null', () => {
      renderHook(() => useAccount(null), {
        wrapper: createWrapper(),
      });

      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it('should be disabled when accountId is empty string', async () => {
      const { result } = renderHook(() => useAccount(''), {
        wrapper: createWrapper(),
      });

      // Hook should be disabled (no fetch, no loading, no error)
      expect(result.current.isLoading).toBe(false);
      expect(result.current.isFetching).toBe(false);
      expect(result.current.isError).toBe(false);
      expect(result.current.data).toBeUndefined();
      // No API call should be made
      expect(apiClient.get).not.toHaveBeenCalled();
    });
  });

  describe('useAccountSyncStatus hook', () => {
    it('should fetch sync status for all providers', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse(sampleSyncStatus));

      const { result } = renderHook(() => useAccountSyncStatus(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith('l4', '/accounts/sync-status');
      expect(result.current.data).toHaveLength(2);
      expect(result.current.data?.[0].provider).toBe('salesforce');
      expect(result.current.data?.[1].provider).toBe('hubspot');
    });
  });

  describe('useSyncAccounts mutation', () => {
    it('should trigger sync for specific provider', async () => {
      (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(sampleSyncResult));
      (apiClient.get as Mock).mockResolvedValue(createMockResponse(sampleAccountsResponse));

      const { result } = renderHook(() => useSyncAccounts(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ provider: 'salesforce', force_refresh: false });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.post).toHaveBeenCalledWith('l4', '/accounts/sync', {
        provider: 'salesforce',
        account_ids: undefined,
        force_refresh: false,
      });
    });

    it('should trigger sync for specific account IDs', async () => {
      (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(sampleSyncResult));

      const { result } = renderHook(() => useSyncAccounts(), {
        wrapper: createWrapper(),
      });

      result.current.mutate({ account_ids: ['acc-001', 'acc-002'] });

      await waitFor(() => expect(apiClient.post).toHaveBeenCalled());

      expect(apiClient.post).toHaveBeenCalledWith('l4', '/accounts/sync', {
        provider: undefined,
        account_ids: ['acc-001', 'acc-002'],
        force_refresh: false,
      });
    });

    it('should invalidate queries on success', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      }

      (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(sampleSyncResult));

      const { result } = renderHook(() => useSyncAccounts(), {
        wrapper: Wrapper,
      });

      result.current.mutate({});

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['accounts'] });
    });
  });

  describe('useRefreshAccount mutation', () => {
    it('should refresh single account', async () => {
      (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(sampleAccount));

      const { result } = renderHook(() => useRefreshAccount(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('acc-001');

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.post).toHaveBeenCalledWith('l4', '/accounts/acc-001/refresh', {});
      expect(result.current.data?.id).toBe('acc-001');
    });

    it('should reject empty account ID', async () => {
      const { result } = renderHook(() => useRefreshAccount(), {
        wrapper: createWrapper(),
      });

      result.current.mutate('');

      await waitFor(() => expect(result.current.isError).toBe(true));

      expect(result.current.error?.message).toBe('Account ID is required');
    });

    it('should invalidate queries on success', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      }

      (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(sampleAccount));

      const { result } = renderHook(() => useRefreshAccount(), {
        wrapper: Wrapper,
      });

      result.current.mutate('acc-001');

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: QK.accounts.detail('acc-001') });
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: QK.accounts.list({}) });
    });

    it('does not perform optimistic updates (removed for correctness)', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });
      const cancelSpy = vi.spyOn(queryClient, 'cancelQueries');
      const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      }

      // Pre-populate cache with existing account
      const initialAccount = { ...sampleAccount, sync_status: 'synced' as const };
      queryClient.setQueryData(QK.accounts.detail('acc-001'), initialAccount);

      (apiClient.post as Mock).mockImplementation(() =>
        new Promise((resolve) => setTimeout(() => resolve(createMockResponse(sampleAccount)), 100))
      );

      const { result } = renderHook(() => useRefreshAccount(), {
        wrapper: Wrapper,
      });

      result.current.mutate('acc-001');

      // Verify no optimistic update was performed (no cancelQueries or setQueryData calls)
      expect(cancelSpy).not.toHaveBeenCalled();
      expect(setQueryDataSpy).not.toHaveBeenCalled();

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });

    it('handles refresh error without rollback (no optimistic update to rollback)', async () => {
      const queryClient = new QueryClient({
        defaultOptions: { queries: { retry: false } },
      });

      // Pre-populate cache with existing account
      const initialAccount = { ...sampleAccount, sync_status: 'synced' as const };
      queryClient.setQueryData(QK.accounts.detail('acc-001'), initialAccount);

      function Wrapper({ children }: { children: React.ReactNode }) {
        return (
          <QueryClientProvider client={queryClient}>
            {children}
          </QueryClientProvider>
        );
      }

      (apiClient.post as Mock).mockRejectedValueOnce(new Error('Network error'));

      const { result } = renderHook(() => useRefreshAccount(), {
        wrapper: Wrapper,
      });

      await expect(result.current.mutateAsync('acc-001')).rejects.toThrow();

      await waitFor(() => expect(result.current.isError).toBe(true));

      // Verify cache remains unchanged (since no optimistic update was made)
      const finalAccount = queryClient.getQueryData(QK.accounts.detail('acc-001'));
      expect(finalAccount).toEqual(initialAccount);
    });
  });

  describe('useAccountFilterOptions hook', () => {
    it('should fetch filter options', async () => {
      (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse(sampleFilterOptions));

      const { result } = renderHook(() => useAccountFilterOptions(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(apiClient.get).toHaveBeenCalledWith('l4', '/accounts/filters');
      expect(result.current.data?.industries).toContain('Technology');
      expect(result.current.data?.stages).toContain('customer');
      expect(result.current.data?.providers).toHaveLength(2);
    });
  });
});
