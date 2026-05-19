import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { apiClient } from '@/api/client';
import { createWrapper } from '../test-utils';
import { useApplyWorkspacePageAction } from './useWorkspaceCase';

vi.mock('@/api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/client')>();
  return {
    ...actual,
    apiClient: {
      patch: vi.fn(),
      post: vi.fn(),
    },
  };
});

describe('useApplyWorkspacePageAction', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('maps signal review action and refreshes query-backed state', async () => {
    (apiClient.patch as Mock).mockResolvedValue({ data: { ok: true } });
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper });

    result.current.mutate({
      entityType: 'signal',
      entityId: 'sig-1',
      accountId: 'acc-1',
      caseId: 'case-1',
      intendedOperation: 'signal_review',
      payload: { reviewStatus: 'approved', decisionNote: 'validated' },
      runMetadataIds: { runId: 'run-1', traceId: 'trace-1' },
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiClient.patch).toHaveBeenCalledWith('l4', '/v1/signals/sig-1/review', expect.objectContaining({
      account_id: 'acc-1',
      review_status: 'approved',
      run_metadata_ids: { runId: 'run-1', traceId: 'trace-1' },
    }));
  });

  it('maps evidence attach action', async () => {
    (apiClient.post as Mock).mockResolvedValue({ data: { ok: true } });
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper });

    result.current.mutate({
      entityType: 'evidence',
      entityId: 'ev-1',
      accountId: 'acc-1',
      caseId: 'case-1',
      intendedOperation: 'evidence_attach',
      payload: { hypothesisId: 'hyp-1' },
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiClient.post).toHaveBeenCalledWith('l4', '/v1/hypotheses/hyp-1/attach-evidence', expect.objectContaining({ evidence_id: 'ev-1' }));
  });

  it('maps hypothesis convert action', async () => {
    (apiClient.post as Mock).mockResolvedValue({ data: { ok: true } });
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper });

    result.current.mutate({
      entityType: 'hypothesis',
      entityId: 'hyp-1',
      accountId: 'acc-1',
      caseId: 'case-1',
      intendedOperation: 'hypothesis_convert',
      payload: { feedback: 'converted from validated signal' },
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiClient.post).toHaveBeenCalledWith('l4', '/v1/hypotheses/hyp-1/validate', expect.objectContaining({ new_status: 'converted' }));
  });

  it('maps scenario update action', async () => {
    (apiClient.patch as Mock).mockResolvedValue({ data: { ok: true } });
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper });

    result.current.mutate({
      entityType: 'scenario',
      entityId: 'scn-1',
      accountId: 'acc-1',
      caseId: 'case-1',
      intendedOperation: 'scenario_update',
      payload: { uplift: 0.15 },
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(apiClient.patch).toHaveBeenCalledWith('l4', '/analysis/cases/case-1/workspace/value-model/scenarios/scn-1', expect.objectContaining({ updates: { uplift: 0.15 } }));
  });

  it('rejects with an error when the API call fails', async () => {
    (apiClient.patch as Mock).mockRejectedValue(new Error('network error'));
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper });

    result.current.mutate({
      entityType: 'signal',
      entityId: 'sig-1',
      accountId: 'acc-1',
      caseId: 'case-1',
      intendedOperation: 'signal_review',
      payload: { reviewStatus: 'approved' },
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeInstanceOf(Error);
  });

  it('throws for an unknown intendedOperation', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApplyWorkspacePageAction(), { wrapper });

    result.current.mutate({
      entityType: 'signal',
      entityId: 'sig-1',
      accountId: 'acc-1',
      caseId: 'case-1',
      // Cast to bypass TypeScript so we can test the runtime default branch
      intendedOperation: 'unknown_op' as never,
      payload: {},
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect((result.current.error as Error).message).toMatch(/Unknown workspace page action/);
  });
});
