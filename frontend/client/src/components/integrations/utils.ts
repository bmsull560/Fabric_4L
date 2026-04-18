import type { Integration } from '@/hooks/useIntegrations';

export type StatusType = 'idle' | 'running' | 'failed' | 'pending';

export function getStatusBadgeClasses(status: StatusType, isConnected: boolean): string {
  if (!isConnected) {
    return 'bg-neutral-100 text-neutral-500 border border-neutral-200';
  }

  switch (status) {
    case 'failed':
      return 'bg-red-100 text-red-700 border border-red-200';
    case 'running':
      return 'bg-amber-100 text-amber-700 border border-amber-200';
    default:
      return 'bg-emerald-100 text-emerald-700 border border-emerald-200';
  }
}

export function getStatusText(status: StatusType, isConnected: boolean): string {
  if (!isConnected) return 'Disconnected';

  switch (status) {
    case 'failed':
      return 'Error';
    case 'running':
      return 'Syncing...';
    default:
      return 'Connected';
  }
}

export function getStatusTextColor(status: StatusType, isConnected: boolean): string {
  if (!isConnected) return 'text-neutral-500';

  switch (status) {
    case 'failed':
      return 'text-red-600';
    case 'running':
      return 'text-amber-600';
    default:
      return 'text-emerald-600';
  }
}

export function formatLastSync(date: string | null | undefined): string {
  if (!date) return 'Never';
  return new Date(date).toLocaleDateString();
}

export function formatRecordCount(count: number | undefined): string {
  if (count === undefined || count === null) return '0';
  return count.toLocaleString();
}
