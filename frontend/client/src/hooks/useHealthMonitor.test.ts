/**
 * useHealthMonitor Hook Tests
 *
 * Tests for system health monitoring:
 * - useSystemHealth: Fetch overall system health with polling
 * - useHealthAlerts: Fetch active health alerts
 */
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useSystemHealth,
  useHealthAlerts,
  type SystemHealth,
  type HealthAlert,
} from './useHealthMonitor';

const mockSystemHealth: SystemHealth = {
  overall_status: 'healthy',
  checked_at: '2024-01-15T10:00:00Z',
  services: [
    {
      name: 'l1-ingestion',
      status: 'healthy',
      version: '1.2.3',
      uptime_seconds: 86400,
      last_check_at: '2024-01-15T10:00:00Z',
      response_time_ms: 45,
    },
    {
      name: 'l2-extraction',
      status: 'healthy',
      version: '1.2.3',
      uptime_seconds: 86400,
      last_check_at: '2024-01-15T10:00:00Z',
      response_time_ms: 52,
    },
    {
      name: 'l3-knowledge',
      status: 'healthy',
      version: '2.0.1',
      uptime_seconds: 43200,
      last_check_at: '2024-01-15T10:00:00Z',
      response_time_ms: 120,
    },
    {
      name: 'l4-agents',
      status: 'degraded',
      version: '1.5.0',
      uptime_seconds: 21600,
      last_check_at: '2024-01-15T10:00:00Z',
      response_time_ms: 2500,
      error_message: 'High memory usage',
    },
  ],
  summary: {
    healthy: 3,
    degraded: 1,
    unhealthy: 0,
    unknown: 0,
    total: 4,
  },
};

const mockHealthAlerts: HealthAlert[] = [
  {
    id: 'alert-1',
    service_name: 'l4-agents',
    severity: 'warning',
    message: 'Memory usage above 85%',
    started_at: '2024-01-15T09:30:00Z',
  },
  {
    id: 'alert-2',
    service_name: 'l3-knowledge',
    severity: 'critical',
    message: 'Database connection pool exhausted',
    started_at: '2024-01-15T08:15:00Z',
    acknowledged: true,
  },
];

describe('useSystemHealth', () => {
  it('fetches system health successfully', async () => {
    server.use(
      http.get('/api/v1/agents/health', () => {
        return HttpResponse.json(mockSystemHealth);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useSystemHealth(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.overall_status).toBe('healthy');
    expect(result.current.data?.services).toHaveLength(4);
    expect(result.current.data?.summary.healthy).toBe(3);
    expect(result.current.data?.summary.degraded).toBe(1);
  });

  it('identifies degraded services', async () => {
    server.use(
      http.get('/api/v1/agents/health', () => {
        return HttpResponse.json(mockSystemHealth);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useSystemHealth(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const degradedService = result.current.data?.services.find(s => s.status === 'degraded');
    expect(degradedService?.name).toBe('l4-agents');
    expect(degradedService?.response_time_ms).toBe(2500);
    expect(degradedService?.error_message).toBe('High memory usage');
  });

  it('handles unhealthy system status', async () => {
    server.use(
      http.get('/api/v1/agents/health', () => {
        return HttpResponse.json({
          ...mockSystemHealth,
          overall_status: 'unhealthy',
          summary: { healthy: 1, degraded: 1, unhealthy: 2, unknown: 0, total: 4 },
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useSystemHealth(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.overall_status).toBe('unhealthy');
  });

  it('handles unknown status for new services', async () => {
    server.use(
      http.get('/api/v1/agents/health', () => {
        return HttpResponse.json({
          ...mockSystemHealth,
          services: [
            ...mockSystemHealth.services,
            {
              name: 'l5-truth',
              status: 'unknown',
              version: '0.0.1',
              uptime_seconds: 0,
              last_check_at: '2024-01-15T10:00:00Z',
              response_time_ms: 0,
            },
          ],
          summary: { healthy: 3, degraded: 1, unhealthy: 0, unknown: 1, total: 5 },
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useSystemHealth(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.summary.unknown).toBe(1);
  });

  it('handles error state', async () => {
    server.resetHandlers();
    server.use(
      http.get('/api/v1/agents/health', () => {
        return HttpResponse.json(
          { error: 'Health service unavailable' },
          { status: 503 }
        );
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useSystemHealth(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });
});

describe('useHealthAlerts', () => {
  it('fetches active alerts', async () => {
    server.use(
      http.get('/api/v1/agents/health/alerts', () => {
        return HttpResponse.json(mockHealthAlerts);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useHealthAlerts(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0].severity).toBe('warning');
    expect(result.current.data?.[1].severity).toBe('critical');
  });

  it('filters critical alerts', async () => {
    server.use(
      http.get('/api/v1/agents/health/alerts', () => {
        return HttpResponse.json(mockHealthAlerts);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useHealthAlerts(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const criticalAlerts = result.current.data?.filter(a => a.severity === 'critical');
    expect(criticalAlerts).toHaveLength(1);
    expect(criticalAlerts?.[0].service_name).toBe('l3-knowledge');
  });

  it('handles empty alerts list', async () => {
    server.use(
      http.get('/api/v1/agents/health/alerts', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useHealthAlerts(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it('handles acknowledged alerts', async () => {
    server.use(
      http.get('/api/v1/agents/health/alerts', () => {
        return HttpResponse.json(mockHealthAlerts);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useHealthAlerts(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const acknowledgedAlert = result.current.data?.find(a => a.acknowledged);
    expect(acknowledgedAlert?.id).toBe('alert-2');
  });
});
