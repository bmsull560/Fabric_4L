/**
 * useFormulas Hook Tests
 *
 * Comprehensive tests for formula management including:
 * - useFormulas: Filtered formula list
 * - useFormula: Single formula details
 * - useFormulaApprovals: Pending approvals list
 * - useApproveFormula: Approval action mutation
 * - useSubmitFormula: Formula submission mutation
 */
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useFormulas,
  useFormula,
  useFormulaApprovals,
  useApproveFormula,
  useSubmitFormula,
  useUpdateFormula,
} from './useFormulas';

describe('useFormulas', () => {
  it('fetches all formulas', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulas(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeInstanceOf(Array);
    expect(result.current.data?.length).toBeGreaterThan(0);
  });

  it('applies status filter', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulas({ status: 'active' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    result.current.data?.forEach(formula => {
      expect(formula.status).toBe('active');
    });
  });

  it('applies search filter', async () => {
    server.use(
      http.get('/api/v1/graph/formulas', ({ request }) => {
        const url = new URL(request.url);
        const search = url.searchParams.get('search');

        return HttpResponse.json([
          {
            id: 'formula-search',
            formula_id: 'formula-search',
            name: `Search Result for ${search}`,
            version: '1.0.0',
            status: 'active',
            updated_at: '2024-01-15T10:00:00Z',
            created_at: '2024-01-01T00:00:00Z',
            used_in_count: 3,
          },
        ]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulas({ search: 'ROI' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles empty formula list', async () => {
    server.use(
      http.get('/api/v1/graph/formulas', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulas(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(0);
  });

  it('handles API errors', async () => {
    server.resetHandlers();
    server.use(
      http.get('/api/v1/graph/formulas', () => {
        return HttpResponse.json({ error: 'Database error' }, { status: 500 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulas(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });
});

describe('useFormula', () => {
  it('fetches single formula details', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormula('formula-1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.id).toBe('formula-1');
    expect(result.current.data?.name).toBeDefined();
    expect(result.current.data?.expression).toBeDefined();
    expect(result.current.data?.variables).toBeInstanceOf(Array);
  });

  it('disables query when id is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormula(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles formula not found', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/:id', () => {
        return HttpResponse.json({ error: 'Formula not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormula('non-existent'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useFormulaApprovals', () => {
  it('fetches pending approvals', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaApprovals(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeInstanceOf(Array);
  });

  it('returns empty array when no approvals', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/approvals/pending', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaApprovals(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(0);
  });
});

describe('useApproveFormula', () => {
  it('approves formula successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApproveFormula(), { wrapper });

    result.current.mutate({ formulaId: 'formula-2', action: 'approve', reason: 'Looks good' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('rejects formula successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useApproveFormula(), { wrapper });

    result.current.mutate({ formulaId: 'formula-2', action: 'reject', reason: 'Needs changes' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles approval error', async () => {
    server.use(
      http.post('/api/v1/graph/formulas/:id/approve', () => {
        return HttpResponse.json({ error: 'Formula not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useApproveFormula(), { wrapper });

    result.current.mutate({ formulaId: 'non-existent', action: 'approve' });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useSubmitFormula', () => {
  it('submits formula for approval', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSubmitFormula(), { wrapper });

    result.current.mutate('formula-draft');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toMatchObject({
      formula_id: 'formula-draft',
      status: 'pending_approval',
    });
  });

  it('handles submission error', async () => {
    server.use(
      http.post('/api/v1/graph/formulas/:id/submit', () => {
        return HttpResponse.json({ error: 'Formula already submitted' }, { status: 409 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useSubmitFormula(), { wrapper });

    result.current.mutate('already-submitted');

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useUpdateFormula', () => {
  it('updates formula with PATCH method', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateFormula(), { wrapper });

    result.current.mutate({
      formulaId: 'formula-1',
      name: 'Updated Formula Name',
      description: 'Updated description',
      expression: 'updated + expression',
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toMatchObject({
      formula_id: 'formula-1',
      name: 'Updated Formula Name',
      version: '1.0.1',
    });
  });

  it('handles update error', async () => {
    server.use(
      http.patch('/api/v1/graph/formulas/:id', () => {
        return HttpResponse.json({ error: 'Formula not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateFormula(), { wrapper });

    result.current.mutate({
      formulaId: 'non-existent',
      name: 'Will Fail',
    });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});
