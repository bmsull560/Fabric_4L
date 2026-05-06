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

import { useState, useMemo, useCallback } from "react";
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
import { usePaginatedList } from "@/hooks";
import { useAccountContextStore } from "@/stores/accountContextStore";

// Filter types
interface AccountFilters {
  search?: string;
  region?: string;
  segment?: string;
  sync_status?: string;
  industry?: string;
}

interface FilterOptions {
  regions?: { value: string; label: string }[];
  segments?: { value: string; label: string }[];
  industries?: { value: string; label: string }[];
}

// Page hook return type
export interface UseAccountsPageReturn {
  // Data
  accounts: Account[];
  selectedAccount: Account | null;
  filterOptions: FilterOptions | undefined;
  syncStatus: AccountSyncStatusInfo | undefined;
  
  // State
  filters: AccountFilters;
  pagination: ReturnType<typeof usePaginatedList>;
  
  // Actions
  actions: {
    handleFilterChange: (newFilters: Partial<AccountFilters>) => void;
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
  const [searchParams] = useSearchParams();
  const { selectedAccountId, setSelectedAccountId } = useAccountContextStore();

  // Local filter state
  const [filters, setFilters] = useState<AccountFilters>({});

  // Pagination state
  const pagination = usePaginatedList({
    initialPage: searchParams.get('page') ? Math.max(1, parseInt(searchParams.get('page')!, 10)) : 1,
    initialPageSize: 20,
    mode: 'server',
  });

  // Atomic data hooks
  const { data: accounts, isLoading, error } = useAccounts({
    limit: pagination.limit,
    offset: pagination.offset,
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
  const handleFilterChange = useCallback((newFilters: Partial<AccountFilters>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
    pagination.setPage(1); // Reset to page 1 when filters change
  }, [pagination]);

  const handleSelectAccount = useCallback((accountId: string) => {
    setSelectedAccountId(accountId === selectedAccountId ? null : accountId);
  }, [selectedAccountId, setSelectedAccountId]);

  const handleSyncAccounts = useCallback(() => {
    syncMutation.mutate();
  }, [syncMutation]);

  const handleRefreshAccount = useCallback((accountId: string) => {
    refreshMutation.mutate(accountId);
  }, [refreshMutation]);

  const handleSearch = useCallback((query: string) => {
    handleFilterChange({ search: query });
  }, [handleFilterChange]);

  return {
    accounts: accounts ?? [],
    selectedAccount: selectedAccount ?? null,
    filterOptions,
    syncStatus,
    filters,
    pagination,
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
