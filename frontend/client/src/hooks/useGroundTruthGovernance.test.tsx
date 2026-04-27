import React from 'react';
import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import {
  useGroundTruths,
  useGroundTruthAuditTrail,
  useGroundTruthFreshnessSummary,
  useGroundTruthStaleTruths,
  useGroundTruthMaturityLadder,
  type TruthListResponse,
  type StaleTruthsResponse,
  type FreshnessSummaryResponse,
} from './useGroundTruthGovernance';

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
  },
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return function Wrapper({ children }: { children: React.ReactNode }) {
    return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
  };
}

function mockResponse<T>(data: T): { data: T; status: number } {
  return { data, status: 200 };
}

const truthList: TruthListResponse = {
  items: [
    {
      id: 'truth-1',
      claim: 'Test claim',
      claim_type: 'factual',
      confidence: 0.9,
      status: 'APPROVED',
      maturity_level: 4,
      is_stale: false,
      source_count: 2,
      approved_by: null,
      freshness: '2026-01-01T00:00:00Z',
      created_at: '2026-01-01T00:00:00Z',
    },
  ],
  total: 1,
  limit: 50,
  offset: 0,
  has_more: false,
};

const freshnessSummary: FreshnessSummaryResponse = {
  stale_count: 3,
  fresh_count: 8,
  expiring_soon_count: 2,
};

const staleTruths: StaleTruthsResponse = {
  items: truthList.items,
  total: 1,
  limit: 50,
  offset: 0,
};

describe('useGroundTruthGovernance', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches truths list with relative L5 root path and query params', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(mockResponse(truthList));

    const { result } = renderHook(
      () => useGroundTruths({ status: 'APPROVED', is_stale: true, limit: 25, offset: 10 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledTimes(1);
    expect((apiClient.get as Mock).mock.calls[0][0]).toBe('l5');
    const calledPath = (apiClient.get as Mock).mock.calls[0][1] as string;
    expect(calledPath.startsWith('/?')).toBe(true);
    expect(calledPath).toContain('status=APPROVED');
    expect(calledPath).toContain('is_stale=true');
    expect(calledPath).toContain('limit=25');
    expect(calledPath).toContain('offset=10');
  });

  it('does not fetch truths list when disabled', () => {
    renderHook(() => useGroundTruths({}, false), { wrapper: createWrapper() });
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('fetches truth audit trail with encoded id', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(mockResponse([]));

    const { result } = renderHook(() => useGroundTruthAuditTrail('truth id/1'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l5', '/truth%20id%2F1/audit');
  });

  it('does not fetch truth audit trail when id is null', () => {
    renderHook(() => useGroundTruthAuditTrail(null), { wrapper: createWrapper() });
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('fetches freshness summary and stale truths using relative L5 paths', async () => {
    (apiClient.get as Mock)
      .mockResolvedValueOnce(mockResponse(freshnessSummary))
      .mockResolvedValueOnce(mockResponse(staleTruths));

    const freshnessHook = renderHook(() => useGroundTruthFreshnessSummary(), {
      wrapper: createWrapper(),
    });
    const staleHook = renderHook(() => useGroundTruthStaleTruths(20, 5), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(freshnessHook.result.current.isSuccess).toBe(true));
    await waitFor(() => expect(staleHook.result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l5', '/freshness-summary');
    expect(apiClient.get).toHaveBeenCalledWith('l5', '/stale?limit=20&offset=5');
  });

  it('fetches maturity ladder from L5 path', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(
      mockResponse({ levels: [{ level: 0, name: 'Extracted', description: 'Initial state', criteria: [] }] })
    );

    const { result } = renderHook(() => useGroundTruthMaturityLadder(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l5', '/maturity-ladder');
  });
});
