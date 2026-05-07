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
import { server } from '../test/mocks/server';
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

const mockTenantSettingsResponse = {
  id: mockTenantSettings.tenant_id,
  name: mockTenantSettings.tenant_name,
  slug: 'acme-corp',
  status: 'active',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: mockTenantSettings.updated_at,
  settings: {
    custom_branding: mockTenantSettings.branding,
    notification_preferences: mockTenantSettings.notifications,
    security: {
      ...mockTenantSettings.security,
      require_mfa: mockTenantSettings.security.require_2fa,
    },
    feature_flags: mockTenantSettings.features,
    limits: mockTenantSettings.limits,
  },
};

function buildSettingsResponse(overrides: Partial<TenantSettings> = {}) {
  const merged: TenantSettings = {
    ...mockTenantSettings,
    ...overrides,
    features: {
      ...mockTenantSettings.features,
      ...overrides.features,
    },
    limits: {
      ...mockTenantSettings.limits,
      ...overrides.limits,
    },
    notifications: {
      ...mockTenantSettings.notifications,
      ...overrides.notifications,
    },
    security: {
      ...mockTenantSettings.security,
      ...overrides.security,
    },
    branding: {
      ...mockTenantSettings.branding,
      ...overrides.branding,
    },
  };

  return {
    id: merged.tenant_id,
    name: merged.tenant_name,
    slug: merged.tenant_slug ?? mockTenantSettingsResponse.slug,
    status: merged.tenant_status ?? mockTenantSettingsResponse.status,
    created_at: merged.tenant_created_at ?? mockTenantSettingsResponse.created_at,
    updated_at: merged.updated_at,
    updated_by: merged.updated_by,
    settings: {
      custom_branding: merged.branding,
      notification_preferences: merged.notifications,
      security: {
        ...merged.security,
        require_mfa: merged.security.require_2fa,
      },
      feature_flags: merged.features,
      limits: merged.limits,
      webhook_url: merged.notifications.webhook_url,
    },
  };
}

describe('usePlatformSettings', () => {
  it('fetches tenant settings successfully', async () => {
    server.use(
      http.get('/api/v1/agents/tenants/current/settings', () => {
        return HttpResponse.json(mockTenantSettingsResponse);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toMatchObject(mockTenantSettings);
    expect(result.current.data?.tenant_name).toBe('Acme Corp');
    expect(result.current.data?.features.advanced_analytics).toBe(true);
  });

  it('handles loading state', async () => {
    server.use(
      http.get('/api/v1/agents/tenants/current/settings', async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return HttpResponse.json(mockTenantSettingsResponse);
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
      http.get('/api/v1/agents/tenants/current/settings', () => {
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
      http.get('/api/v1/agents/tenants/current/settings', () => {
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
      http.get('/api/v1/agents/tenants/current/settings', () => {
        return HttpResponse.json(mockTenantSettingsResponse);
      }),
      http.patch('/api/v1/agents/tenants/current/settings', async ({ request }) => {
        const body = (await request.json()) as { settings?: Record<string, unknown> };
        expect(body.settings?.feature_flags).toEqual({ advanced_analytics: false });
        return HttpResponse.json(
          buildSettingsResponse({
            tenant_name: 'Updated Corp',
            features: { ...mockTenantSettings.features, advanced_analytics: false },
            updated_at: new Date().toISOString(),
          })
        );
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
      http.patch('/api/v1/agents/tenants/current/settings', async ({ request }) => {
        const body = (await request.json()) as { settings?: Record<string, unknown> };
        expect(body.settings?.feature_flags).toEqual({ ai_assistant: false, audit_trail: false });
        return HttpResponse.json(
          buildSettingsResponse({
            features: { ...mockTenantSettings.features, ai_assistant: false, audit_trail: false },
          })
        );
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
      http.patch('/api/v1/agents/tenants/current/settings', () => {
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
      http.get('/api/v1/agents/tenants/current/settings', () => {
        requestCount++;
        return HttpResponse.json(mockTenantSettingsResponse);
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
    expect(result2.current.data).toMatchObject(mockTenantSettings);
    expect(requestCount).toBe(1); // No additional request
  });

  it('refetches when cache is stale', async () => {
    let requestCount = 0;
    server.use(
      http.get('/api/v1/agents/tenants/current/settings', () => {
        requestCount++;
        return HttpResponse.json(buildSettingsResponse({
          tenant_name: `Acme Corp v${requestCount}`,
        }));
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
      http.get('/api/v1/agents/tenants/current/settings', () => {
        fetchCount++;
        return HttpResponse.json(buildSettingsResponse(currentSettings));
      }),
      http.patch('/api/v1/agents/tenants/current/settings', async ({ request }) => {
        const body = (await request.json()) as { settings?: Record<string, unknown> };
        if (body.settings) {
          if (body.settings.custom_branding) {
            currentSettings.branding = {
              ...currentSettings.branding,
              ...(body.settings.custom_branding as TenantSettings['branding']),
            };
          }
          if (body.settings.notification_preferences) {
            currentSettings.notifications = {
              ...currentSettings.notifications,
              ...(body.settings.notification_preferences as TenantSettings['notifications']),
            };
          }
          if (body.settings.feature_flags) {
            currentSettings.features = {
              ...currentSettings.features,
              ...(body.settings.feature_flags as TenantSettings['features']),
            };
          }
          if (body.settings.security) {
            const security = body.settings.security as Record<string, unknown>;
            currentSettings.security = {
              ...currentSettings.security,
              require_2fa: Boolean(security.require_2fa ?? security.require_mfa ?? currentSettings.security.require_2fa),
              session_timeout_minutes: Number(security.session_timeout_minutes ?? currentSettings.security.session_timeout_minutes),
              ip_allowlist: Array.isArray(security.ip_allowlist)
                ? security.ip_allowlist as string[]
                : currentSettings.security.ip_allowlist,
            };
          }
        }
        if (body.settings && 'tenant_name' in body.settings && typeof body.settings.tenant_name === 'string') {
          currentSettings.tenant_name = body.settings.tenant_name;
        }
        return HttpResponse.json(buildSettingsResponse(currentSettings));
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
    updateResult.current.mutate({ branding: { primary_color: '#ff0000' } });
    await waitFor(() => expect(updateResult.current.isSuccess).toBe(true));

    // Query should be invalidated and refetched
    await waitFor(() => expect(settingsResult.current.data?.branding?.primary_color).toBe('#ff0000'));
    expect(fetchCount).toBe(2); // Refetch occurred after invalidation
  });

  it('failed update preserves previous usable state', async () => {
    server.use(
      http.get('/api/v1/agents/tenants/current/settings', () => {
        return HttpResponse.json(mockTenantSettingsResponse);
      }),
      http.patch('/api/v1/agents/tenants/current/settings', () => {
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
    updateResult.current.mutate({ branding: { primary_color: '#ffffff' } });
    await waitFor(() => expect(updateResult.current.isError).toBe(true), { timeout: 5000 });

    // Original data should still be available
    expect(settingsResult.current.data).toEqual(originalData);
    expect(settingsResult.current.data?.tenant_name).toBe('Acme Corp');
  });

  it('retry path works after transient failure', async () => {
    // Exhaust axios-retry (1 original + 3 retries = 4 attempts) so first mutate actually fails
    let failCount = 4;
    server.use(
      http.patch('/api/v1/agents/tenants/current/settings', () => {
        if (failCount > 0) {
          failCount--;
          return HttpResponse.json({ error: 'Transient Error' }, { status: 503 });
        }
        return HttpResponse.json(buildSettingsResponse({
          branding: { ...mockTenantSettings.branding, primary_color: '#22c55e' },
        }));
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

    // First attempt fails after exhausting axios retries
    result.current.mutate({ branding: { primary_color: '#000000' } });
    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 10000 });
    expect(result.current.error).toBeDefined();

    // Retry succeeds
    result.current.mutate({ branding: { primary_color: '#000000' } });
    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });
    expect(result.current.data?.branding?.primary_color).toBe('#22c55e');
  }, 15000);
});

describe('usePlatformSettings - concurrency and lifecycle', () => {
  it('concurrent updates resolve predictably', async () => {
    const updates: string[] = [];
    server.use(
      http.patch('/api/v1/agents/tenants/current/settings', async ({ request }) => {
        const body = (await request.json()) as { settings?: { custom_branding?: TenantSettings['branding'] } };
        updates.push(body.settings?.custom_branding?.primary_color || 'unknown');
        return HttpResponse.json(buildSettingsResponse({
          branding: body.settings?.custom_branding,
        }));
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
    result.current.mutate({ branding: { primary_color: 'First' } });
    result.current.mutate({ branding: { primary_color: 'Second' } });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Both should have been processed (order may vary by timing)
    expect(updates).toContain('First');
    expect(updates).toContain('Second');
    // Final state reflects last successful mutation
    expect(['First', 'Second']).toContain(result.current.data?.branding?.primary_color);
  });

  it('unmounted/remounted consumer reuses QueryClient state', async () => {
    server.use(
      http.get('/api/v1/agents/tenants/current/settings', () => {
        return HttpResponse.json(mockTenantSettingsResponse);
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
      http.get('/api/v1/agents/tenants/current/settings', async () => {
        await new Promise(resolve => setTimeout(resolve, 100));
        return HttpResponse.json(mockTenantSettingsResponse);
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
    expect(result.current.data).toMatchObject(mockTenantSettings);

    vi.useRealTimers();
  }, 10000);

  it('one-off server override path behaves correctly', async () => {
    // Initial handler returns default
    server.use(
      http.get('/api/v1/agents/tenants/current/settings', () => {
        return HttpResponse.json(mockTenantSettingsResponse);
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
      http.get('/api/v1/agents/tenants/current/settings', () => {
        return HttpResponse.json(buildSettingsResponse({
          tenant_name: 'Overridden Corp',
        }));
      })
    );

    // Refetch by invalidating and creating new hook
    await sharedQueryClient.invalidateQueries({ queryKey: ['platform', 'settings'] });

    const { result: result2 } = renderHook(() => usePlatformSettings(), { wrapper });
    await waitFor(() => expect(result2.current.data?.tenant_name).toBe('Overridden Corp'));
  });
});
