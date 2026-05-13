/**
 * useWorkspaceTabQuery — Generic workspace data fetcher
 *
 * Provides a standard query pattern for workspace tabs that fetch
 * data scoped to an account + tab key.
 */
import { useQuery } from "@tanstack/react-query";
import { apiGet } from "@/api/typedClient";
import { QK } from "@/hooks/queryKeys";
import { STALE_TIME } from "@/hooks/useApiShared";

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
    queryKey: QK.workspace.accountTab(accountId, tabKey),
    queryFn: async () => {
      const response = await apiGet<T>("l4", `/workspace/${accountId}/${tabKey}`);
      return response.data;
    },
    enabled: enabled && Boolean(accountId),
    staleTime: STALE_TIME.poll,
  });
}
