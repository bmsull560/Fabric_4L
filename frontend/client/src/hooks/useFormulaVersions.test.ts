/**
 * useFormulaVersions Hook Tests
 *
 * Tests for formula versioning:
 * - useFormulaVersions: Fetch version history
 * - useFormulaGovernance: Fetch governance metadata with versions
 */
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useFormulaVersions,
  useFormulaGovernance,
  type FormulaVersion,
  type FormulaGovernance,
} from './useFormulaVersions';

const mockVersions: FormulaVersion[] = [
  {
    version: '1.2.0',
    formula_id: 'formula-123',
    status: 'active',
    created_at: '2024-01-15T10:00:00Z',
    created_by: 'J. Rivera',
    change_summary: 'Added Implementation_Cost variable',
    previous_version: '1.1.0',
  },
  {
    version: '1.1.0',
    formula_id: 'formula-123',
    status: 'approved',
    created_at: '2024-01-07T14:30:00Z',
    created_by: 'M. Chen',
    change_summary: 'Approved by Finance team',
    previous_version: '1.0.0',
  },
  {
    version: '1.0.0',
    formula_id: 'formula-123',
    status: 'deprecated',
    created_at: '2024-01-02T09:00:00Z',
    created_by: 'J. Rivera',
    change_summary: 'Initial version',
    previous_version: null,
  },
];

const mockGovernance: FormulaGovernance = {
  formula_id: 'formula-123',
  current_version: '1.2.0',
  status: 'active',
  owner: 'J. Rivera',
  department: 'Finance',
  review_cycle_days: 90,
  approved_by: 'M. Chen',
  approved_at: '2024-01-07T16:00:00Z',
  last_reviewed_at: '2024-01-15T11:00:00Z',
  next_review_at: '2024-04-15T00:00:00Z',
  versions: mockVersions,
};

describe('useFormulaVersions', () => {
  it('fetches version history for a formula', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-123/versions', () => {
        return HttpResponse.json(mockVersions);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions('formula-123'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(3);
    expect(result.current.data?.[0].version).toBe('1.2.0');
    expect(result.current.data?.[0].status).toBe('active');
  });

  it('handles formula with no versions', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/new-formula/versions', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions('new-formula'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual([]);
  });

  it('does not fetch when formulaId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
    expect(result.current.data).toBeUndefined();
  });

  it('handles different version statuses', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-123/versions', () => {
        return HttpResponse.json([
          { ...mockVersions[0], status: 'draft' },
          { ...mockVersions[1], status: 'under_review' },
          { ...mockVersions[2], status: 'retired' },
        ]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions('formula-123'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const statuses = result.current.data?.map((v: FormulaVersion) => v.status);
    expect(statuses).toContain('draft');
    expect(statuses).toContain('under_review');
    expect(statuses).toContain('retired');
  });

  it('handles version chain with previous_version links', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-123/versions', () => {
        return HttpResponse.json(mockVersions);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions('formula-123'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const v120 = result.current.data?.find((v: FormulaVersion) => v.version === '1.2.0');
    expect(v120?.previous_version).toBe('1.1.0');

    const v100 = result.current.data?.find((v: FormulaVersion) => v.version === '1.0.0');
    expect(v100?.previous_version).toBeNull();
  });

  it('handles error fetching versions', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/invalid-id/versions', () => {
        return HttpResponse.json(
          { error: 'Formula not found' },
          { status: 404 }
        );
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions('invalid-id'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.statusCode).toBe(404);
  });

  it('handles network error gracefully', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/network-error/versions', () => {
        return HttpResponse.error();
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions('network-error'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error).toBeDefined();
  });

  it('handles empty change_summary gracefully', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-123/versions', () => {
        return HttpResponse.json([
          { ...mockVersions[0], change_summary: '' },
        ]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaVersions('formula-123'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0].change_summary).toBe('');
  });
});

describe('useFormulaGovernance', () => {
  it('fetches governance metadata with versions', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-123/governance', () => {
        return HttpResponse.json(mockGovernance);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaGovernance('formula-123'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.formula_id).toBe('formula-123');
    expect(result.current.data?.owner).toBe('J. Rivera');
    expect(result.current.data?.department).toBe('Finance');
    expect(result.current.data?.versions).toHaveLength(3);
  });

  it('handles governance without approval data', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/draft-formula/governance', () => {
        return HttpResponse.json({
          ...mockGovernance,
          formula_id: 'draft-formula',
          status: 'draft',
          approved_by: null,
          approved_at: null,
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaGovernance('draft-formula'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.status).toBe('draft');
    expect(result.current.data?.approved_by).toBeNull();
  });

  it('calculates review cycle dates', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/formula-123/governance', () => {
        return HttpResponse.json(mockGovernance);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaGovernance('formula-123'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.review_cycle_days).toBe(90);
    expect(result.current.data?.last_reviewed_at).toBeDefined();
    expect(result.current.data?.next_review_at).toBeDefined();
  });

  it('does not fetch when formulaId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaGovernance(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.isSuccess).toBe(false);
  });

  it('handles governance not found error', async () => {
    server.use(
      http.get('/api/v1/graph/formulas/nonexistent/governance', () => {
        return HttpResponse.json(
          { error: 'Formula not found' },
          { status: 404 }
        );
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFormulaGovernance('nonexistent'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.error?.statusCode).toBe(404);
  });
});
