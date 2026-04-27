import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { ReactNode } from 'react';
import { http, HttpResponse, passthrough } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useGovernanceTruths,
  useGovernanceMaturityLadder,
  useGovernanceAuditLog,
} from './useGovernanceL5';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useGovernanceL5', () => {
  it('sends query params to /api/v1/truths', async () => {
    let capturedUrl = '';

    server.use(
      http.get(/.*/, ({ request }) => {
        const url = new URL(request.url);
        if (url.pathname === '/api/v1/truths') {
          capturedUrl = request.url;
          return HttpResponse.json({ items: [], total: 0 });
        }
        return passthrough();
      })
    );

    const { result } = renderHook(
      () => useGovernanceTruths({ status: 'stale', search: 'risk', limit: 5, offset: 10 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    const url = new URL(capturedUrl);
    expect(url.searchParams.get('status')).toBe('stale');
    expect(url.searchParams.get('search')).toBe('risk');
    expect(url.searchParams.get('limit')).toBe('5');
    expect(url.searchParams.get('offset')).toBe('10');
  });

  it('returns empty states without errors', async () => {
    server.use(
      http.get(/.*/, ({ request }) => {
        const url = new URL(request.url);
        if (url.pathname === '/api/v1/truths') return HttpResponse.json({ items: [], total: 0 });
        if (url.pathname === '/api/v1/maturity-ladder') return HttpResponse.json([]);
        return passthrough();
      })
    );

    const truths = renderHook(() => useGovernanceTruths(), { wrapper: createWrapper() });
    const ladder = renderHook(() => useGovernanceMaturityLadder(), { wrapper: createWrapper() });

    await waitFor(() => expect(truths.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(ladder.result.current.isSuccess).toBe(true));

    expect(truths.result.current.data).toEqual({ items: [], total: 0 });
    expect(ladder.result.current.data).toEqual([]);
  });

  it('surfaces server errors', async () => {
    server.use(
      http.get(/.*/, ({ request }) => {
        const url = new URL(request.url);
        if (url.pathname === '/api/v1/truths/audit/log') {
          return new HttpResponse(null, { status: 500 });
        }
        return passthrough();
      })
    );

    const { result } = renderHook(() => useGovernanceAuditLog(), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
