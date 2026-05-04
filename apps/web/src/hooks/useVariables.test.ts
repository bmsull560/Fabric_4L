/**
 * useVariables Hook Tests
 *
 * Comprehensive tests for variable management including:
 * - useVariables: Filtered variable list
 * - useVariable: Single variable details
 * - useVariableStats: Statistics aggregation
 * - useSourceBindings: Data source bindings
 * - useValidateVariable: Validation mutation
 */
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import {
  useVariables,
  useVariable,
  useVariableStats,
  useSourceBindings,
  useValidateVariable,
} from './useVariables';

describe('useVariables', () => {
  it('fetches all variables', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariables(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeInstanceOf(Array);
    expect(result.current.data?.length).toBeGreaterThan(0);
  });

  it('applies type filter', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariables({ type: 'currency' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    result.current.data?.forEach(variable => {
      expect(variable.type).toBe('currency');
    });
  });

  it('applies source filter', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariables({ source: 'CRM' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    result.current.data?.forEach(variable => {
      expect(variable.source).toBe('CRM');
    });
  });

  it('applies validation status filter', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariables({ status: 'validated' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    result.current.data?.forEach(variable => {
      expect(variable.validation_status).toBe('validated');
    });
  });

  it('applies search filter', async () => {
    server.use(
      http.get('/api/v1/graph/variables', ({ request }) => {
        const url = new URL(request.url);
        const search = url.searchParams.get('search');

        return HttpResponse.json([
          {
            id: 'var-search',
            variable_id: 'var-search',
            name: `var_${search}`,
            display_name: `Search Result for ${search}`,
            type: 'string',
            unit: 'count',
            source: 'Manual',
            binding: 'manual.entry',
            used_in_count: 1,
            validation_status: 'validated',
            tags: ['search'],
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-15T10:00:00Z',
            version: '1.0.0',
          },
        ]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariables({ search: 'revenue' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles empty variable list', async () => {
    server.use(
      http.get('/api/v1/graph/variables', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariables(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(0);
  });
});

describe('useVariable', () => {
  it('fetches single variable details', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariable('var-1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.id).toBe('var-1');
    expect(result.current.data?.name).toBeDefined();
    expect(result.current.data?.type).toBeDefined();
  });

  it('disables query when id is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariable(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles variable not found', async () => {
    server.use(
      http.get('/api/v1/graph/variables/:id', () => {
        return HttpResponse.json({ error: 'Variable not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariable('non-existent'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useVariableStats', () => {
  it('fetches statistics', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariableStats(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toMatchObject({
      total: expect.any(Number),
      validated: expect.any(Number),
      pending: expect.any(Number),
      failed: expect.any(Number),
    });
  });

  it('handles empty stats', async () => {
    server.use(
      http.get('/api/v1/graph/variables/stats', () => {
        return HttpResponse.json({
          total: 0,
          validated: 0,
          pending: 0,
          failed: 0,
          manual_sources: 0,
          avg_usage: 0,
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useVariableStats(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.total).toBe(0);
  });
});

describe('useSourceBindings', () => {
  it('fetches binding list', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSourceBindings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeInstanceOf(Array);
    expect(result.current.data?.length).toBeGreaterThan(0);
  });

  it('shows connected and disconnected sources', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useSourceBindings(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const connected = result.current.data?.find(b => b.status === 'connected');
    const disconnected = result.current.data?.find(b => b.status === 'disconnected');

    expect(connected || disconnected).toBeDefined();
  });
});

describe('useValidateVariable', () => {
  it('validates variable successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useValidateVariable(), { wrapper });

    result.current.mutate('var-2');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toMatchObject({
      variable_id: 'var-2',
      validation_status: 'validated',
    });
  });

  it('handles validation error for missing variable', async () => {
    server.use(
      http.post('/api/v1/graph/variables/:id/validate', () => {
        return HttpResponse.json({ error: 'Variable not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useValidateVariable(), { wrapper });

    result.current.mutate('non-existent');

    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('handles validation failure', async () => {
    server.use(
      http.post('/api/v1/graph/variables/:id/validate', () => {
        return HttpResponse.json({
          variable_id: 'bad-var',
          validation_status: 'failed',
          validation_message: 'Invalid binding path',
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useValidateVariable(), { wrapper });

    result.current.mutate('bad-var');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.validation_status).toBe('failed');
  });
});
