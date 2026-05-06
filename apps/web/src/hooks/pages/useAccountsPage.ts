/**
 * useAccountsPage — Tier-3 Page Orchestration Hook
 *
 * Orchestrates all account-related hooks and state for the Accounts page.
 * Provides a stable boundary between atomic data hooks, mutations, and UI state.
 *
 * @example
 * ```ts
 * const {
 *   accounts,
 *   selectedAccount,
 *   filters,
 *   pagination,
 *   actions,
 *   status,
 * } = useAccountsPage();
 * ```
 */

import { useState, useCallback, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import {
  useAccounts,
  useAccount,
  useAccountFilterOptions,
  useAccountSyncStatus,
  useSyncAccounts,
  useRefreshAccount,
  type Account,
  type CRMProvider,
  type SyncStatus,
  type AccountSyncStatusInfo,
} from "@/hooks";
import type { AccountFilters as ApiAccountFilters, FilterOptions as ApiFilterOptions } from "@/hooks/useAccounts";
import { usePaginatedList } from "@/hooks";
import { useAccountContextStore } from "@/stores/accountContextStore";

interface PageAccountFilters {
  search?: string;
  region?: string;
  segment?: string;
  sync_status?: SyncStatus | 'all';
  industry?: string;
}

// Page hook return type
export interface UseAccountsPageReturn {
  // Data
  accounts: Account[];
  selectedAccount: Account | null;
  filterOptions: ApiFilterOptions | undefined;
  syncStatus: AccountSyncStatusInfo[] | undefined;

  // State
  filters: PageAccountFilters;
  pagination: ReturnType<typeof usePaginatedList>;

  // Actions
  actions: {
    handleFilterChange: (newFilters: Partial<PageAccountFilters>) => void;
    handleSelectAccount: (accountId: string) => void;
    handleSyncAccounts: () => void;
    handleRefreshAccount: (accountId: string) => void;
    handleSearch: (query: string) => void;
  };

  // Status
  status: {
    isLoading: boolean;
    error: Error | null;
    isSyncing: boolean;
    isRefreshing: boolean;
  };
}

export function useAccountsPage(): UseAccountsPageReturn {
  const [searchParams, setSearchParams] = useSearchParams();
  const { selectedAccountId, setSelectedAccountId } = useAccountContextStore();

  // Local filter state
  const [filters, setFilters] = useState<PageAccountFilters>({});

  // Pagination state with URL sync
  const pagination = usePaginatedList({
    initialPage: searchParams.get('page') ? Math.max(1, parseInt(searchParams.get('page')!, 10) || 1) : 1,
    initialPageSize: 20,
    mode: 'server',
  });

  // Sync pagination state to URL
  const handlePageChange = useCallback((page: number) => {
    pagination.setPage(page);
    const params = new URLSearchParams(searchParams);
    if (page > 1) {
      params.set('page', String(page));
    } else {
      params.delete('page');
    }
    setSearchParams(params, { replace: true });
  }, [pagination, searchParams, setSearchParams]);

  // Override pagination methods to sync URL
  const paginationWithUrlSync = useMemo(() => ({
    ...pagination,
    setPage: handlePageChange,
  }), [pagination, handlePageChange]);

  // Atomic data hooks
  const { data: accountsData, isLoading, error } = useAccounts({
    page: pagination.page,
    page_size: pagination.limit,
    search: filters.search,
    region: filters.region,
    segment: filters.segment,
    sync_status: filters.sync_status,
    industry: filters.industry,
  });

  const { data: selectedAccount } = useAccount(selectedAccountId);
  const { data: filterOptions } = useAccountFilterOptions();
  const { data: syncStatus } = useAccountSyncStatus();

  // Mutation hooks
  const syncMutation = useSyncAccounts();
  const refreshMutation = useRefreshAccount();

  // Derived state
  const handleFilterChange = useCallback((newFilters: Partial<PageAccountFilters>) => {
    setFilters((prev: PageAccountFilters) => ({ ...prev, ...newFilters }));
    paginationWithUrlSync.setPage(1); // Reset to page 1 when filters change
  }, [paginationWithUrlSync]);

  const handleSelectAccount = useCallback((accountId: string) => {
    setSelectedAccountId(accountId === selectedAccountId ? null : accountId);
  }, [selectedAccountId, setSelectedAccountId]);

  const handleSyncAccounts = useCallback(() => {
    syncMutation.mutate({});
  }, [syncMutation]);

  const handleRefreshAccount = useCallback((accountId: string) => {
    refreshMutation.mutate(accountId);
  }, [refreshMutation]);

  const handleSearch = useCallback((query: string) => {
    handleFilterChange({ search: query });
  }, [handleFilterChange]);

  return {
    accounts: accountsData?.items ?? [],
    selectedAccount: selectedAccount ?? null,
    filterOptions,
    syncStatus,
    filters,
    pagination: paginationWithUrlSync,
    actions: {
      handleFilterChange,
      handleSelectAccount,
      handleSyncAccounts,
      handleRefreshAccount,
      handleSearch,
    },
    status: {
      isLoading,
      error: error ?? null,
      isSyncing: syncMutation.isPending,
      isRefreshing: refreshMutation.isPending,
    },
  };
}
