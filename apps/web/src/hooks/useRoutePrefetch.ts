/**
 * useRoutePrefetch - Prefetch lazy-loaded routes and data on hover/focus
 * 
 * This hook provides a debounced prefetch mechanism for high-traffic routes.
 * Prefetching is triggered on pointer enter and keyboard focus, but skipped on mobile/touch devices.
 * 
 * Phase 1 supports:
 * - Accounts → EntityDetail (lazy component + React Query data)
 * - BusinessCaseList → BusinessCase (lazy component + React Query data)
 */
import { useEffect, useRef, useCallback, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { QK } from "./queryKeys";
import { apiClient } from "@/api/client";

// ── Prefetch Registry ────────────────────────────────────────────────────────

interface PrefetchTarget {
  preloadComponent: () => Promise<unknown>;
  prefetchData: (id: string) => Promise<unknown>;
}

const PREFETCH_REGISTRY: Record<string, PrefetchTarget> = {
  account: {
    preloadComponent: () => import("@/pages/EntityDetail"),
    prefetchData: async (accountId: string) => {
      const response = await apiClient.get("l4", `/accounts/${accountId}`);
      return response;
    },
  },
  businessCase: {
    preloadComponent: () => import("@/pages/BusinessCase"),
    prefetchData: async (caseId: string) => {
      const response = await apiClient.get("l4", `/workflows/${caseId}/result`);
      return response;
    },
  },
};

// ── Hook Implementation ───────────────────────────────────────────────────────

interface UseRoutePrefetchOptions {
  /** Debounce delay in milliseconds (default: 150ms) */
  debounceMs?: number;
  /** Whether to skip prefetching on mobile/touch devices (default: true) */
  skipMobile?: boolean;
}

/**
 * Hook to prefetch routes and data when user hovers or focuses on navigation elements
 */
export function useRoutePrefetch(options: UseRoutePrefetchOptions = {}) {
  const { debounceMs = 150, skipMobile = true } = options;
  const queryClient = useQueryClient();
  const timeoutRef = useRef<number | null>(null);
  
  // Component-level deduplication state (ref to avoid dependency issues with Set)
  const prefetchedIdsRef = useRef<Set<string>>(new Set());

  // Prefetch deduplication helper
  const prefetchOnce = useCallback((key: string, fn: () => Promise<unknown>): void => {
    if (prefetchedIdsRef.current.has(key)) return;
    prefetchedIdsRef.current.add(key);
    void fn().catch(() => {
      // On failure, remove from set to allow retry
      prefetchedIdsRef.current.delete(key);
    });
  }, []);

  // Check if device is mobile/touch
  const isMobile = useCallback(() => {
    if (typeof window === "undefined") return false;
    if (skipMobile && window.matchMedia("(pointer: coarse)").matches) {
      return true;
    }
    return false;
  }, [skipMobile]);

  // Prefetch account detail (component + data)
  const prefetchAccountDetail = useCallback(
    (accountId: string) => {
      if (isMobile() || !accountId) return;

      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = window.setTimeout(() => {
        const target = PREFETCH_REGISTRY.account;
        if (!target) return;

        const componentKey = `account-component-${accountId}`;
        const dataKey = `account-data-${accountId}`;

        // Prefetch lazy component
        prefetchOnce(componentKey, () => target.preloadComponent());

        // Prefetch React Query data
        prefetchOnce(dataKey, () =>
          queryClient.prefetchQuery({
            queryKey: QK.accounts.detail(accountId),
            queryFn: () => target.prefetchData(accountId),
          })
        );
      }, debounceMs);
    },
    [debounceMs, isMobile, queryClient, prefetchOnce]
  );

  // Prefetch business case detail (component + data)
  const prefetchBusinessCaseDetail = useCallback(
    (caseId: string) => {
      if (isMobile() || !caseId) return;

      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = window.setTimeout(() => {
        const target = PREFETCH_REGISTRY.businessCase;
        if (!target) return;

        const componentKey = `businessCase-component-${caseId}`;
        const dataKey = `businessCase-data-${caseId}`;

        // Prefetch lazy component
        prefetchOnce(componentKey, () => target.preloadComponent());

        // Prefetch React Query data
        prefetchOnce(dataKey, () =>
          queryClient.prefetchQuery({
            queryKey: QK.businessCases.detail(caseId),
            queryFn: () => target.prefetchData(caseId),
          })
        );
      }, debounceMs);
    },
    [debounceMs, isMobile, queryClient, prefetchOnce]
  );

  // Cancel pending prefetch
  const cancelPrefetch = useCallback(() => {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return cancelPrefetch;
  }, [cancelPrefetch]);

  return {
    prefetchAccountDetail,
    prefetchBusinessCaseDetail,
    cancelPrefetch,
    isMobile,
  };
}
