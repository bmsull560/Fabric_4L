/**
 * useWorkspaceTabQuery — Generic workspace data fetcher
 *
 * Provides a standard query pattern for workspace tabs that fetch
 * data scoped to an account + tab key.
 */
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/api/client";

interface UseWorkspaceTabQueryOptions {
  accountId: string;
  tabKey: string;
  enabled?: boolean;
}

export function useWorkspaceTabQuery<T = unknown>({
  accountId,
  tabKey,
  enabled = true,
}: UseWorkspaceTabQueryOptions) {
  return useQuery<T>({
    queryKey: ["workspace", accountId, tabKey],
    queryFn: async () => {
      const response = await apiClient.get("l4", `/workspace/${accountId}/${tabKey}`);
      return response.data as T;
    },
    enabled: enabled && Boolean(accountId),
    staleTime: 30_000,
  });
}
