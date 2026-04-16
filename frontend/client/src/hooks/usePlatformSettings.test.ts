/**
 * usePlatformSettings Hook Tests
 *
 * Tests for tenant platform settings management:
 * - usePlatformSettings: Fetch tenant settings
 * - useUpdatePlatformSettings: Update tenant configuration
 */
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
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

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('handles 404 not found', async () => {
    server.use(
      http.get('/api/v1/agents/tenant/settings', () => {
        return new HttpResponse(null, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePlatformSettings(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
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
