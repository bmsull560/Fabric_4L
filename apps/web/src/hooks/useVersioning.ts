import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { apiGet, apiPost } from '@/api/typedClient';
import { QK } from './queryKeys';
import { STALE_TIME, BaseApiError } from './useApiShared';

export class VersioningApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'VersioningApiError';
  }
}

export interface AccountVersionSnapshot {
  id: string;
  account_id: string;
  tenant_id: string;
  created_by: string;
  snapshot_type: 'auto' | 'manual';
  label: string | null;
  created_at: string;
}

export interface SnapshotDiff {
  base_snapshot_id: string;
  compare_snapshot_id: string;
  changes: Array<{
    field: string;
    from: unknown;
    to: unknown;
  }>;
  created_at_base: string;
  created_at_compare: string;
}

export function useSnapshots(accountId: string | null) {
  return useQuery<AccountVersionSnapshot[], VersioningApiError>({
    queryKey: QK.versions.list(accountId || ''),
    queryFn: async () => {
      if (!accountId) throw new Error('No account ID provided');
      const response = await apiGet<AccountVersionSnapshot[]>('l4', `/accounts/${accountId}/snapshots`);
      return response.data;
    },
    enabled: !!accountId,
    staleTime: STALE_TIME.list,
  });
}

export function useCreateSnapshot() {
  const qc = useQueryClient();
  return useMutation<AccountVersionSnapshot, VersioningApiError, { accountId: string; label?: string }>({
    mutationFn: async ({ accountId, label }) => {
      const payload = {
        id: crypto.randomUUID(),
        created_by: 'current-user',
        snapshot_type: 'manual',
        label: label || `Snapshot ${new Date().toLocaleString()}`,
      };
      const response = await apiPost<AccountVersionSnapshot>('l4', `/accounts/${accountId}/snapshots`, payload);
      return response.data;
    },
    onSuccess: (_, { accountId }) => {
      qc.invalidateQueries({ queryKey: QK.versions.list(accountId) });
    },
  });
}

export function useSnapshotDiff() {
  return useMutation<SnapshotDiff, VersioningApiError, { accountId: string; baseId: string; compareId: string }>({
    mutationFn: async ({ accountId, baseId, compareId }) => {
      const response = await apiPost<SnapshotDiff>('l4', `/accounts/${accountId}/snapshots/${baseId}/diff?compare_to_id=${compareId}`);
      return response.data;
    },
  });
}
