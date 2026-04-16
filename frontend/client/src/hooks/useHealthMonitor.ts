/**
 * Health Monitor React Query Hooks
 * 
 * Server state management for system health monitoring:
 * - useSystemHealth: Fetch overall system health status
 * - useServiceHealth: Fetch individual service health
 * 
 * All hooks handle loading, error, and automatic refetching.
 */

import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, HealthMonitorApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ───────────────────────────────────────────────────────────────────

export type ServiceStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

export interface ServiceHealth {
  name: string;
  status: ServiceStatus;
  version: string;
  uptime_seconds: number;
  last_check_at: string;
  response_time_ms: number;
  error_message?: string;
  metadata?: Record<string, unknown>;
}

export interface SystemHealth {
  overall_status: ServiceStatus;
  checked_at: string;
  services: ServiceHealth[];
  summary: {
    healthy: number;
    degraded: number;
    unhealthy: number;
    unknown: number;
    total: number;
  };
}

export interface HealthAlert {
  id: string;
  service_name: string;
  severity: 'critical' | 'warning' | 'info';
  message: string;
  started_at: string;
  resolved_at?: string;
  acknowledged?: boolean;
}

// ── Fetch Functions ─────────────────────────────────────────────────────────

async function fetchSystemHealth(): Promise<SystemHealth> {
  const response = await apiClient.get('l4', '/health');
  return response.data as SystemHealth;
}

async function fetchHealthAlerts(): Promise<HealthAlert[]> {
  const response = await apiClient.get('l4', '/health/alerts');
  return response.data as HealthAlert[];
}

// ── Hooks ───────────────────────────────────────────────────────────────────

/**
 * Fetch overall system health status
 * Auto-refetches every 30 seconds for live monitoring
 * 
 * @returns Query result with system health and loading/error states
 * 
 * @example
 * ```tsx
 * const { data: health, isLoading } = useSystemHealth();
 * // health.overall_status: 'healthy' | 'degraded' | 'unhealthy'
 * // health.services: [{ name: 'l1-ingestion', status: 'healthy', ... }]
 * ```
 */
export function useSystemHealth() {
  return useQuery<SystemHealth, HealthMonitorApiError>({
    queryKey: QK.platform.health,
    queryFn: () => withApiError(fetchSystemHealth(), HealthMonitorApiError),
    staleTime: STALE_TIME.realtime,
    refetchInterval: STALE_TIME.poll, // 30 seconds for live monitoring
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/**
 * Fetch active health alerts
 * 
 * @returns Query result with active alerts
 * 
 * @example
 * ```tsx
 * const { data: alerts } = useHealthAlerts();
 * const criticalAlerts = alerts?.filter(a => a.severity === 'critical');
 * ```
 */
export function useHealthAlerts() {
  return useQuery<HealthAlert[], HealthMonitorApiError>({
    queryKey: [...QK.platform.health, 'alerts'] as const,
    queryFn: () => withApiError(fetchHealthAlerts(), HealthMonitorApiError),
    staleTime: STALE_TIME.poll,
    refetchInterval: STALE_TIME.stats, // 1 minute
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}
