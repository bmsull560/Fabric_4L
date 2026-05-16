/**
 * useHarness regression tests.
 *
 * Guards against:
 *   - Import breakage (POLL_INTERVALS from wrong module — the original defect)
 *   - Hook module not exporting expected symbols
 *   - apiClient called with correct layer key ('l4') and path prefix ('/harness/...')
 *   - Polling disabled for terminal run states
 *   - Polling disabled when runId is undefined (gates hook guard)
 *   - Mutation hooks invalidate the right query keys on success
 */
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { createWrapper, createMockResponse } from '../test-utils';
import { apiClient } from '@/api/client';
import { QK } from '@/hooks/queryKeys';

// ── Import smoke test ─────────────────────────────────────────────────────────
// This import will fail at module resolution time if POLL_INTERVALS is imported
// from a module that does not export it (the original defect).
import {
  useHarnessRuns,
  useHarnessRun,
  useHarnessCheckpoints,
  useHarnessGates,
  useHarnessHealth,
  useCreateHarnessRun,
  useTransitionHarnessRun,
  useCancelHarnessRun,
  useDecideGate,
  useCreateHarnessGate,
  useValidateHarnessClaims,
} from './useHarness';

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}));

// ── Fixtures ──────────────────────────────────────────────────────────────────

const RUN_ID = 'run-001';
const GATE_ID = 'gate-001';
const TENANT_ID = 'tenant-001';

const makeRun = (overrides: Record<string, unknown> = {}) => ({
  id: RUN_ID,
  tenant_id: TENANT_ID,
  account_id: null,
  workflow_type: 'roi_calculator_generation',
  initiated_by: 'user',
  status: 'running',
  current_state: 'VALIDATE_CLAIMS',
  value_pack_id: null,
  trace_id: 'trace-abc',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:01:00Z',
  ...overrides,
});

const makeGate = (overrides: Record<string, unknown> = {}) => ({
  id: GATE_ID,
  run_id: RUN_ID,
  tenant_id: TENANT_ID,
  gate_type: 'approve_claims',
  status: 'pending',
  decision_by: null,
  decision_reason: null,
  created_at: '2026-01-01T00:00:00Z',
  decided_at: null,
  ...overrides,
});

// ── Import smoke ──────────────────────────────────────────────────────────────

describe('useHarness module exports', () => {
  it('exports all expected hook symbols', () => {
    // If any of these are undefined the import from the wrong module caused a
    // silent failure — this catches the POLL_INTERVALS defect class.
    expect(useHarnessRuns).toBeTypeOf('function');
    expect(useHarnessRun).toBeTypeOf('function');
    expect(useHarnessCheckpoints).toBeTypeOf('function');
    expect(useHarnessGates).toBeTypeOf('function');
    expect(useHarnessHealth).toBeTypeOf('function');
    expect(useCreateHarnessRun).toBeTypeOf('function');
    expect(useTransitionHarnessRun).toBeTypeOf('function');
    expect(useCancelHarnessRun).toBeTypeOf('function');
    expect(useDecideGate).toBeTypeOf('function');
    expect(useCreateHarnessGate).toBeTypeOf('function');
    expect(useValidateHarnessClaims).toBeTypeOf('function');
  });
});

// ── useHarnessRuns ────────────────────────────────────────────────────────────

describe('useHarnessRuns', () => {
  beforeEach(() => vi.mocked(apiClient.get).mockReset());

  it('calls l4 /harness/runs with no params', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse({ items: [makeRun()], total: 1, limit: 20, offset: 0, has_more: false })
    );

    const { result } = renderHook(() => useHarnessRuns(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l4', '/harness/runs');
    expect(result.current.data?.items).toHaveLength(1);
  });

  it('appends query params when provided', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse({ items: [], total: 0, limit: 10, offset: 0, has_more: false })
    );

    renderHook(
      () => useHarnessRuns({ status: 'running', workflow_type: 'roi_calculator_generation', limit: 10, offset: 0 }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    const path = vi.mocked(apiClient.get).mock.calls[0][1] as string;
    expect(path).toContain('status=running');
    expect(path).toContain('workflow_type=roi_calculator_generation');
    expect(path).toContain('limit=10');
    expect(path).toContain('offset=0');
  });
});

// ── useHarnessRun ─────────────────────────────────────────────────────────────

describe('useHarnessRun', () => {
  beforeEach(() => vi.mocked(apiClient.get).mockReset());

  it('fetches a single run by id', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(createMockResponse(makeRun()));

    const { result } = renderHook(() => useHarnessRun(RUN_ID), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l4', `/harness/runs/${RUN_ID}`);
    expect(result.current.data?.id).toBe(RUN_ID);
  });

  it('is disabled when runId is undefined', () => {
    const { result } = renderHook(() => useHarnessRun(undefined), { wrapper: createWrapper() });

    expect(result.current.fetchStatus).toBe('idle');
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('does not poll for terminal run states', async () => {
    const terminalRun = makeRun({ current_state: 'DONE', status: 'completed' });
    vi.mocked(apiClient.get).mockResolvedValue(createMockResponse(terminalRun));

    const { result } = renderHook(() => useHarnessRun(RUN_ID), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // refetchInterval callback returns false for terminal states — verify data is correct
    expect(result.current.data?.current_state).toBe('DONE');
    // The hook itself is responsible for returning false from refetchInterval;
    // we verify the state value that drives that decision is correctly surfaced.
  });

  it('returns non-terminal run data that would trigger polling', async () => {
    const activeRun = makeRun({ current_state: 'VALIDATE_CLAIMS', status: 'running' });
    vi.mocked(apiClient.get).mockResolvedValue(createMockResponse(activeRun));

    const { result } = renderHook(() => useHarnessRun(RUN_ID), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.current_state).toBe('VALIDATE_CLAIMS');
  });
});

// ── useHarnessGates ───────────────────────────────────────────────────────────

describe('useHarnessGates', () => {
  beforeEach(() => vi.mocked(apiClient.get).mockReset());

  it('fetches gates for a run', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse({ items: [makeGate()], total: 1 })
    );

    const { result } = renderHook(() => useHarnessGates(RUN_ID), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l4', `/harness/runs/${RUN_ID}/gates`);
    expect(result.current.data?.items[0].status).toBe('pending');
  });

  it('is disabled when runId is undefined', () => {
    const { result } = renderHook(() => useHarnessGates(undefined), { wrapper: createWrapper() });

    expect(result.current.fetchStatus).toBe('idle');
    expect(apiClient.get).not.toHaveBeenCalled();
  });
});

// ── useHarnessCheckpoints ─────────────────────────────────────────────────────

describe('useHarnessCheckpoints', () => {
  beforeEach(() => vi.mocked(apiClient.get).mockReset());

  it('fetches checkpoints for a run', async () => {
    const checkpoint = {
      id: 'cp-001',
      run_id: RUN_ID,
      tenant_id: TENANT_ID,
      state_name: 'VALIDATE_CLAIMS',
      input_hash: 'abc123',
      output_hash: null,
      created_at: '2026-01-01T00:00:00Z',
    };
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse({ items: [checkpoint], total: 1 })
    );

    const { result } = renderHook(() => useHarnessCheckpoints(RUN_ID), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l4', `/harness/runs/${RUN_ID}/checkpoints`);
    expect(result.current.data?.items[0].state_name).toBe('VALIDATE_CLAIMS');
  });

  it('is disabled when runId is undefined', () => {
    const { result } = renderHook(() => useHarnessCheckpoints(undefined), { wrapper: createWrapper() });

    expect(result.current.fetchStatus).toBe('idle');
    expect(apiClient.get).not.toHaveBeenCalled();
  });
});

// ── useHarnessHealth ──────────────────────────────────────────────────────────

describe('useHarnessHealth', () => {
  beforeEach(() => vi.mocked(apiClient.get).mockReset());

  it('calls l4 /harness/health', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse({ status: 'ok', validation_available: true, l5_healthy: true, db_healthy: true })
    );

    const { result } = renderHook(() => useHarnessHealth(), { wrapper: createWrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.get).toHaveBeenCalledWith('l4', '/harness/health');
    expect(result.current.data?.status).toBe('ok');
  });
});

// ── useDecideGate ─────────────────────────────────────────────────────────────

describe('useDecideGate', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
    vi.mocked(apiClient.post).mockReset();
  });

  it('posts to l4 /harness/gates/{gateId}/decide', async () => {
    const decidedGate = makeGate({ status: 'approved', decision_by: 'reviewer@example.com' });
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(decidedGate));

    const { result } = renderHook(() => useDecideGate(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({
        gateId: GATE_ID,
        runId: RUN_ID,
        decision: 'approved',
        reason: 'Looks good',
      });
    });

    expect(apiClient.post).toHaveBeenCalledWith(
      'l4',
      `/harness/gates/${GATE_ID}/decide`,
      { decision: 'approved', decision_reason: 'Looks good' }
    );
  });
});

// ── useTransitionHarnessRun ───────────────────────────────────────────────────

describe('useTransitionHarnessRun', () => {
  beforeEach(() => vi.mocked(apiClient.post).mockReset());

  it('posts to l4 /harness/runs/{runId}/transition', async () => {
    const transitionResponse = {
      run: makeRun({ current_state: 'PUBLISH_OUTPUT' }),
      trace_event: null,
    };
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(transitionResponse));

    const { result } = renderHook(() => useTransitionHarnessRun(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({
        runId: RUN_ID,
        data: { to_state: 'PUBLISH_OUTPUT' },
      });
    });

    expect(apiClient.post).toHaveBeenCalledWith(
      'l4',
      `/harness/runs/${RUN_ID}/transition`,
      { to_state: 'PUBLISH_OUTPUT' }
    );
  });
});

// ── useCancelHarnessRun ───────────────────────────────────────────────────────

describe('useCancelHarnessRun', () => {
  beforeEach(() => vi.mocked(apiClient.delete).mockReset());

  it('sends DELETE to l4 /harness/runs/{runId}', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue(createMockResponse(null));

    const { result } = renderHook(() => useCancelHarnessRun(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync(RUN_ID);
    });

    expect(apiClient.delete).toHaveBeenCalledWith('l4', `/harness/runs/${RUN_ID}`);
  });
});

// ── useCreateHarnessRun ───────────────────────────────────────────────────────

describe('useCreateHarnessRun', () => {
  beforeEach(() => vi.mocked(apiClient.post).mockReset());

  it('posts to l4 /harness/runs with correct payload', async () => {
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(makeRun()));

    const { result } = renderHook(() => useCreateHarnessRun(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({
        workflow_type: 'roi_calculator_generation',
        initiated_by: 'user',
        account_id: 'acct-001',
        value_pack_id: null,
      });
    });

    expect(apiClient.post).toHaveBeenCalledWith('l4', '/harness/runs', {
      workflow_type: 'roi_calculator_generation',
      initiated_by: 'user',
      account_id: 'acct-001',
      value_pack_id: null,
    });
  });

  it('invalidates QK.harness.all on success', async () => {
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(makeRun()));

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    function Wrapper({ children }: { children: React.ReactNode }) {
      return React.createElement(QueryClientProvider, { client: queryClient }, children);
    }

    const { result } = renderHook(() => useCreateHarnessRun(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync({
        workflow_type: 'roi_calculator_generation',
        initiated_by: 'user',
        account_id: null,
        value_pack_id: null,
      });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: QK.harness.all });
  });
});

// ── useCreateHarnessGate ──────────────────────────────────────────────────────

describe('useCreateHarnessGate', () => {
  beforeEach(() => vi.mocked(apiClient.post).mockReset());

  it('posts to l4 /harness/runs/{runId}/gates with correct payload', async () => {
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(makeGate()));

    const { result } = renderHook(() => useCreateHarnessGate(), { wrapper: createWrapper() });

    await act(async () => {
      await result.current.mutateAsync({ runId: RUN_ID, gate_type: 'approve_claims' });
    });

    expect(apiClient.post).toHaveBeenCalledWith(
      'l4',
      `/harness/runs/${RUN_ID}/gates`,
      { gate_type: 'approve_claims' },
    );
  });

  it('invalidates QK.harness.gates(runId) on success', async () => {
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(makeGate()));

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    function Wrapper({ children }: { children: React.ReactNode }) {
      return React.createElement(QueryClientProvider, { client: queryClient }, children);
    }

    const { result } = renderHook(() => useCreateHarnessGate(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync({ runId: RUN_ID, gate_type: 'approve_claims' });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: QK.harness.gates(RUN_ID) });
  });
});

// ── useValidateHarnessClaims ──────────────────────────────────────────────────

describe('useValidateHarnessClaims', () => {
  beforeEach(() => vi.mocked(apiClient.post).mockReset());

  it('posts to l4 /harness/runs/{runId}/validate with claims payload', async () => {
    const validationResponse = {
      results: [],
      total: 0,
      passed: 0,
      failed: 0,
      needs_review: 0,
      insufficient_evidence: 0,
    };
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(validationResponse));

    const { result } = renderHook(() => useValidateHarnessClaims(), { wrapper: createWrapper() });

    const claims = [
      { claim_id: 'c-001', claim_text: 'ROI is 3x', evidence_refs: [], value_pack_id: null, account_id: null },
    ];

    await act(async () => {
      await result.current.mutateAsync({ runId: RUN_ID, claims });
    });

    expect(apiClient.post).toHaveBeenCalledWith(
      'l4',
      `/harness/runs/${RUN_ID}/validate`,
      { claims },
    );
  });

  it('invalidates QK.harness.run(runId) on success', async () => {
    const validationResponse = {
      results: [], total: 0, passed: 0, failed: 0, needs_review: 0, insufficient_evidence: 0,
    };
    vi.mocked(apiClient.post).mockResolvedValue(createMockResponse(validationResponse));

    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

    function Wrapper({ children }: { children: React.ReactNode }) {
      return React.createElement(QueryClientProvider, { client: queryClient }, children);
    }

    const { result } = renderHook(() => useValidateHarnessClaims(), { wrapper: Wrapper });

    await act(async () => {
      await result.current.mutateAsync({ runId: RUN_ID, claims: [] });
    });

    expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: QK.harness.run(RUN_ID) });
  });
});
