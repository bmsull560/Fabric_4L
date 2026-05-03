import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import { useL5MaturityLadder, useL5TruthAudit, useL5Truths } from './useL5Governance';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

describe('useL5Governance hooks', () => {
  it('sends query params to /api/v1/truths', async () => {
    server.use(
      http.get('/api/v1/truths', ({ request }) => {
        const url = new URL(request.url);
        expect(url.searchParams.get('status')).toBe('verified');
        expect(url.searchParams.get('claim_type')).toBe('compliance_requirement');
        expect(url.searchParams.get('is_stale')).toBe('true');

        return HttpResponse.json({ items: [], total: 0 });
      })
    );

    const { result } = renderHook(
      () =>
        useL5Truths({
          status: 'verified',
          claim_type: 'compliance_requirement',
          is_stale: true,
        }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total).toBe(0);
  });

  it('handles empty responses for truths and maturity ladder', async () => {
    server.use(
      http.get('/api/v1/truths', () => HttpResponse.json({ items: [], total: 0 })),
      http.get('/api/v1/maturity-ladder', () => HttpResponse.json([]))
    );

    const truths = renderHook(() => useL5Truths(), { wrapper: createWrapper() });
    const maturity = renderHook(() => useL5MaturityLadder(), { wrapper: createWrapper() });

    await waitFor(() => expect(truths.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(maturity.result.current.isSuccess).toBe(true));

    expect(truths.result.current.data?.items).toHaveLength(0);
    expect(maturity.result.current.data).toEqual([]);
  });

  it('handles audit and error states', async () => {
    server.use(
      http.get('/api/v1/truths/:truthId/audit', ({ params }) => {
        if (params.truthId === 'broken') {
          return HttpResponse.json({ message: 'boom' }, { status: 500 });
        }
        return HttpResponse.json([
          { id: 'audit-1', timestamp: '2026-04-27T00:00:00Z', action: 'create' },
        ]);
      })
    );

    const ok = renderHook(() => useL5TruthAudit('truth-1'), { wrapper: createWrapper() });
    await waitFor(() => expect(ok.result.current.isSuccess).toBe(true));
    expect(ok.result.current.data?.[0].id).toBe('audit-1');

    const bad = renderHook(() => useL5TruthAudit('broken'), { wrapper: createWrapper() });
    await waitFor(() => expect(bad.result.current.isError).toBe(true));
  });
});
