/**
 * usePlatformSettings Hook Tests
 *
 * Tests for tenant platform settings management:
 * - usePlatformSettings: Fetch tenant settings
 * - useUpdatePlatformSettings: Update tenant configuration
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper, createTestQueryClient } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { type ReactNode } from 'react';
import {
  usePlatformSettings,
  useUpdatePlatformSettings,
  type TenantSettings,
} from './usePlatformSettings';

const mockTenantSettings: TenantSettings = {
  tenant_id: 'tenant-123',
  tenant_name: 'Acme Corp',
  features: {
    advanced_analytics: true,
    custom_integrations: false,
    ai_assistant: true,
    audit_trail: true,
  },
  limits: {
    max_users: 100,
    max_api_calls_per_day: 10000,
    storage_gb: 50,
  },
  notifications: {
    email_alerts: true,
    slack_webhook: 'https://hooks.slack.com/test',
  },
  security: {
    require_2fa: false,
    session_timeout_minutes: 60,
    ip_allowlist: ['192.168.1.0/24'],
  },
  branding: {
    logo_url: 'https://example.com/logo.png',
    primary_color: '#2563eb',
  },
  updated_at: '2024-01-15T10:00:00Z',
};

describe('usePlatformSettings', () => {
  it('fetches tenant settings successfully', async () => {
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json(mockTenantSettings);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(mockTenantSettings);
    expect(result.current.data?.tenant_name).toBe('Acme Corp');
    expect(result.current.data?.features.advanced_analytics).toBe(true);
  });

  it('handles loading state', async () => {
    server.use(
      http.get('/api/v1/agents/tenant/settings', async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return HttpResponse.json(mockTenantSettings);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles error state', async () => {
    server.resetHandlers();
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json(
          { error: 'Failed to fetch settings' },
          { status: 500 }
        );
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
    expect(result.current.error).toBeDefined();
  });

  it('handles 404 not found', async () => {
    server.resetHandlers();
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return new HttpResponse(null, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
    expect(result.current.error?.statusCode).toBe(404);
  });
});

describe('useUpdatePlatformSettings', () => {
  it('updates tenant settings successfully', async () => {
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json(mockTenantSettings);
      }),
      http.patch('/api/v1/agents/tenant/settings', async ({ request }) => {
        const body = (await request.json()) as Partial<TenantSettings>;
        return HttpResponse.json({
          ...mockTenantSettings,
          ...body,
          updated_at: new Date().toISOString(),
        });
      })
    );

    const wrapper = createWrapper();
    const { result: updateResult } = renderHook(() => useUpdatePlatformSettings(), { wrapper });

    updateResult.current.mutate({
      tenant_name: 'Updated Corp',
      features: { advanced_analytics: false },
    });

    await waitFor(() => expect(updateResult.current.isSuccess).toBe(true));
    expect(updateResult.current.data?.tenant_name).toBe('Updated Corp');
  });

  it('updates feature flags', async () => {
    server.use(
      http.patch('/api/v1/agents/tenant/settings', async ({ request }) => {
        const body = (await request.json()) as Partial<TenantSettings>;
        return HttpResponse.json({
          ...mockTenantSettings,
          ...body,
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdatePlatformSettings(), { wrapper });

    result.current.mutate({
      features: { ai_assistant: false, audit_trail: false },
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.features.ai_assistant).toBe(false);
  });

  it('handles update error', async () => {
    server.use(
      http.patch('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json(
          { error: 'Permission denied' },
          { status: 403 }
        );
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdatePlatformSettings(), { wrapper });

    result.current.mutate({ tenant_name: 'Test' });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.statusCode).toBe(403);
  });
});

describe('usePlatformSettings - cache behavior', () => {
  it('uses cached data without unnecessary refetch', async () => {
    let requestCount = 0;
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        requestCount++;
        return HttpResponse.json(mockTenantSettings);
      })
    );

    // Use a shared QueryClient for both hook instances
    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();
    const { result: result1 } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result1.current.isSuccess).toBe(true));
    expect(requestCount).toBe(1);

    // Second hook instance should use cached data without new request
    const { result: result2 } = renderHook(() => usePlatformSettings(), { wrapper });
    await waitFor(() => expect(result2.current.isSuccess).toBe(true));
    expect(result2.current.data).toEqual(mockTenantSettings);
    expect(requestCount).toBe(1); // No additional request
  });

  it('refetches when cache is stale', async () => {
    let requestCount = 0;
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        requestCount++;
        return HttpResponse.json({
          ...mockTenantSettings,
          tenant_name: `Acme Corp v${requestCount}`,
        });
      })
    );

    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(requestCount).toBe(1);
    expect(result.current.data?.tenant_name).toBe('Acme Corp v1');

    // Invalidate cache to trigger refetch (simulating stale cache)
    await sharedQueryClient.invalidateQueries({ queryKey: ['platform', 'settings'] });

    // Trigger refetch by creating new hook instance
    const { result: result2 } = renderHook(() => usePlatformSettings(), { wrapper });
    await waitFor(() => expect(result2.current.isSuccess).toBe(true));
    expect(result2.current.data?.tenant_name).toBe('Acme Corp v2');
    expect(requestCount).toBe(2);
  });
});

describe('usePlatformSettings - mutation and invalidation', () => {
  it('successful update invalidates and refreshes query data', async () => {
    let fetchCount = 0;
    let currentSettings = { ...mockTenantSettings };

    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        fetchCount++;
        return HttpResponse.json(currentSettings);
      }),
      http.patch('/api/v1/agents/tenant/settings', async ({ request }) => {
        const body = (await request.json()) as Partial<TenantSettings>;
        currentSettings = { ...currentSettings, ...body };
        return HttpResponse.json(currentSettings);
      })
    );

    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();
    const { result: settingsResult } = renderHook(() => usePlatformSettings(), { wrapper });
    const { result: updateResult } = renderHook(() => useUpdatePlatformSettings(), { wrapper });

    await waitFor(() => expect(settingsResult.current.isSuccess).toBe(true));
    expect(fetchCount).toBe(1);
    expect(settingsResult.current.data?.tenant_name).toBe('Acme Corp');

    // Update settings
    updateResult.current.mutate({ tenant_name: 'Updated Corp' });
    await waitFor(() => expect(updateResult.current.isSuccess).toBe(true));

    // Query should be invalidated and refetched
    await waitFor(() => expect(settingsResult.current.data?.tenant_name).toBe('Updated Corp'));
    expect(fetchCount).toBe(2); // Refetch occurred after invalidation
  });

  it('failed update preserves previous usable state', async () => {
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json(mockTenantSettings);
      }),
      http.patch('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json({ error: 'Server Error' }, { status: 500 });
      })
    );

    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();
    const { result: settingsResult } = renderHook(() => usePlatformSettings(), { wrapper });
    const { result: updateResult } = renderHook(() => useUpdatePlatformSettings(), { wrapper });

    await waitFor(() => expect(settingsResult.current.isSuccess).toBe(true));
    const originalData = settingsResult.current.data;

    // Failed update
    updateResult.current.mutate({ tenant_name: 'Should Fail' });
    await waitFor(() => expect(updateResult.current.isError).toBe(true), { timeout: 5000 });

    // Original data should still be available
    expect(settingsResult.current.data).toEqual(originalData);
    expect(settingsResult.current.data?.tenant_name).toBe('Acme Corp');
  });

  it('retry path works after transient failure', async () => {
    let failCount = 1; // First call fails, second succeeds
    server.use(
      http.patch('/api/v1/agents/tenant/settings', () => {
        if (failCount > 0) {
          failCount--;
          return HttpResponse.json({ error: 'Transient Error' }, { status: 503 });
        }
        return HttpResponse.json({
          ...mockTenantSettings,
          tenant_name: 'Recovered Corp',
        });
      })
    );

    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();
    const { result } = renderHook(() => useUpdatePlatformSettings(), { wrapper });

    // First attempt fails
    result.current.mutate({ tenant_name: 'Retry Test' });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.statusCode).toBe(503);

    // Wait for error state to settle before retry
    await new Promise(resolve => setTimeout(resolve, 10));

    // Retry succeeds
    result.current.mutate({ tenant_name: 'Retry Test' });
    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });
    expect(result.current.data?.tenant_name).toBe('Recovered Corp');
  }, 10000);
});

describe('usePlatformSettings - concurrency and lifecycle', () => {
  it('concurrent updates resolve predictably', async () => {
    const updates: string[] = [];
    server.use(
      http.patch('/api/v1/agents/tenant/settings', async ({ request }) => {
        const body = (await request.json()) as Partial<TenantSettings>;
        updates.push(body.tenant_name || 'unknown');
        return HttpResponse.json({
          ...mockTenantSettings,
          ...body,
        });
      })
    );

    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();
    const { result } = renderHook(() => useUpdatePlatformSettings(), { wrapper });

    // Fire two updates concurrently
    result.current.mutate({ tenant_name: 'First' });
    result.current.mutate({ tenant_name: 'Second' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Both should have been processed (order may vary by timing)
    expect(updates).toContain('First');
    expect(updates).toContain('Second');
    // Final state reflects last successful mutation
    expect(['First', 'Second']).toContain(result.current.data?.tenant_name);
  });

  it('unmounted/remounted consumer reuses QueryClient state', async () => {
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json(mockTenantSettings);
      })
    );

    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();

    // First mount
    const { result, unmount } = renderHook(() => usePlatformSettings(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const cachedData = result.current.data;

    // Unmount
    unmount();

    // Remount - should immediately have cached data from React Query's cache
    const { result: remountedResult } = renderHook(() => usePlatformSettings(), { wrapper });

    // Data should be immediately available without loading
    expect(remountedResult.current.data).toEqual(cachedData);
    expect(remountedResult.current.isLoading).toBe(false);
  });
});

describe('usePlatformSettings - edge cases', () => {
  it('delayed response does not break hook state transitions', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });

    server.use(
      http.get('/api/v1/agents/tenant/settings', async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return HttpResponse.json(mockTenantSettings);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    // Should be loading immediately
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isSuccess).toBe(false);

    // Advance timers to trigger the delay
    vi.advanceTimersByTime(150);
    await new Promise(resolve => setTimeout(resolve, 0));

    // After delay, should transition to success
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.isLoading).toBe(false);
    expect(result.current.data).toEqual(mockTenantSettings);

    vi.useRealTimers();
  }, 10000);

  it('one-off server override path behaves correctly', async () => {
    // Initial handler returns default
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json(mockTenantSettings);
      })
    );

    const sharedQueryClient = createTestQueryClient();
    const createSharedWrapper = () => {
      return function Wrapper({ children }: { children: ReactNode }) {
        return (
          <QueryClientProvider client={sharedQueryClient}>
            {children}
          </QueryClientProvider>
        );
      };
    };

    const wrapper = createSharedWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.tenant_name).toBe('Acme Corp');

    // Override with one-off handler for second fetch
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return HttpResponse.json({
          ...mockTenantSettings,
          tenant_name: 'Overridden Corp',
        });
      })
    );

    // Refetch by invalidating and creating new hook
    await sharedQueryClient.invalidateQueries({ queryKey: ['platform', 'settings'] });

    const { result: result2 } = renderHook(() => usePlatformSettings(), { wrapper });
    await waitFor(() => expect(result2.current.data?.tenant_name).toBe('Overridden Corp'));
  });
});
