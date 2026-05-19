import { describe, it, expect, vi, beforeEach } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook, act, waitFor } from '@testing-library/react';
import React from 'react';
import { useApplyWorkspacePageAction } from './useWorkspaceCase';

const patchMock = vi.fn();
const postMock = vi.fn();

vi.mock('@/api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/client')>();
  return {
    ...actual,
    apiClient: {
      patch: (...args: unknown[]) => patchMock(...args),
      post: (...args: unknown[]) => postMock(...args),
    },
  };
});

function wrapperFactory(client: QueryClient) {
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={client}>{children}</QueryClientProvider>
  );
}

describe('useApplyWorkspacePageAction integration', () => {
  beforeEach(() => {
    patchMock.mockReset();
    postMock.mockReset();
  });

  it('executes signal_review mutation and refreshes affected queries', async () => {
    patchMock.mockResolvedValue({ data: { ok: true } });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper: wrapperFactory(queryClient) });

    await act(async () => {
      await result.current.mutateAsync({
        entityType: 'signal',
        entityId: 'sig-1',
        accountId: 'acc-1',
        caseId: 'case-1',
        intendedOperation: 'signal_review',
        payload: { reviewStatus: 'approved' },
        runMetadataIds: { runId: 'run-1', traceId: 'trace-1', auditEventId: 'audit-1' },
      });
    });

    expect(patchMock).toHaveBeenCalledWith('l4', '/v1/signals/sig-1/review', expect.objectContaining({ run_metadata_ids: { runId: 'run-1', traceId: 'trace-1', auditEventId: 'audit-1' } }));
    await waitFor(() => expect(invalidateSpy).toHaveBeenCalled());
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['workspace', 'tab', 'case-1'] });
  });

  it('executes scenario_update mutation and refreshes affected queries', async () => {
    patchMock.mockResolvedValue({ data: { scenario_id: 'scenario-1', name: 'updated' } });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper: wrapperFactory(queryClient) });

    await act(async () => {
      await result.current.mutateAsync({
        entityType: 'scenario',
        entityId: 'scenario-1',
        accountId: 'acc-1',
        caseId: 'case-9',
        intendedOperation: 'scenario_update',
        payload: { name: 'updated' },
        runMetadataIds: { runId: 'run-9', traceId: 'trace-9', auditEventId: 'audit-9' },
      });
    });

    expect(patchMock).toHaveBeenCalledWith('l4', '/analysis/cases/case-9/workspace/value-model/scenarios/scenario-1', expect.objectContaining({ updates: { name: 'updated' } }));
    await waitFor(() => expect(invalidateSpy).toHaveBeenCalled());
    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['workspace', 'tab', 'case-9'] });
  });
});
