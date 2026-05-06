import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { apiClient } from '@/api/client';
import { createWrapper, createMockResponse } from '../test-utils';
import { useAccountBriefing, useDealReadiness, usePipelineSummary } from './useIntelligence';

vi.mock('@/api/client', () => ({
  apiClient: { get: vi.fn() },
}));

describe('useIntelligence URL paths', () => {
  beforeEach(() => vi.clearAllMocks());

  it('uses canonical account briefing path', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse({ account_id: 'acc-1' }));
    renderHook(() => useAccountBriefing('acc-1'), { wrapper: createWrapper() });
    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('l4', '/v1/accounts/acc-1/briefing');
  });

  it('uses canonical deal readiness path', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse({ account_id: 'acc-1' }));
    renderHook(() => useDealReadiness('acc-1'), { wrapper: createWrapper() });
    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('l4', '/v1/accounts/acc-1/deal-readiness');
  });

  it('keeps pipeline summary under intelligence namespace', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse({ total_accounts: 0 }));
    renderHook(() => usePipelineSummary(), { wrapper: createWrapper() });
    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('l4', '/v1/intelligence/pipeline-summary');
  });
});
