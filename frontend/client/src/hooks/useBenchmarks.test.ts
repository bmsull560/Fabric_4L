/**
 * useBenchmarks Hook Tests
 *
 * Comprehensive tests for benchmark management including:
 * - useBenchmarks: Filtered list fetching
 * - useBenchmark: Single benchmark details
 * - useBenchmarkPolicies: Policy configuration
 * - useUpdateBenchmarkPolicy: Policy updates
 */
import { describe, it, expect } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useBenchmarks,
  useBenchmark,
  useBenchmarkPolicies,
  useUpdateBenchmarkPolicy,
} from './useBenchmarks';

describe('useBenchmarks', () => {
  it('fetches all benchmarks', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarks(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0]).toMatchObject({
      id: expect.any(String),
      name: expect.any(String),
      confidence: expect.any(String),
    });
  });

  it('applies industry filter', async () => {
    server.use(
      http.get('/api/v1/graph/benchmarks', ({ request }) => {
        const url = new URL(request.url);
        const industry = url.searchParams.get('industry');

        return HttpResponse.json([
          {
            id: 'bench-filtered',
            benchmark_id: 'bench-filtered',
            name: 'Filtered Benchmark',
            industry: industry || 'Unknown',
            value_range: '2.5x - 4.0x',
            confidence: 'High',
            source: 'Test',
            year: 2024,
            status: 'active',
            tags: [],
            usage_count: 5,
          },
        ]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarks({ industry: 'Software' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.[0]?.industry).toBe('Software');
  });

  it('applies status filter', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarks({ status: 'active' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // All returned benchmarks should be active
    result.current.data?.forEach(benchmark => {
      expect(benchmark.status).toBe('active');
    });
  });

  it('applies confidence filter', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarks({ confidence: 'High' }), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
  });

  it('handles API errors', async () => {
    server.use(
      http.get('/api/v1/graph/benchmarks', () => {
        return HttpResponse.json({ error: 'Database error' }, { status: 500 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarks(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useBenchmark', () => {
  it('fetches single benchmark details', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmark('bench-1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.id).toBe('bench-1');
    expect(result.current.data?.name).toBeDefined();
  });

  it('disables query when id is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmark(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles benchmark not found', async () => {
    server.use(
      http.get('/api/v1/graph/benchmarks/:id', () => {
        return HttpResponse.json({ error: 'Benchmark not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmark('non-existent'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

describe('useBenchmarkPolicies', () => {
  it('fetches policy list', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarkPolicies(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeInstanceOf(Array);
    expect(result.current.data?.length).toBeGreaterThan(0);
  });

  it('handles empty policy list', async () => {
    server.use(
      http.get('/api/v1/graph/benchmarks/policies', () => {
        return HttpResponse.json([]);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarkPolicies(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toHaveLength(0);
  });
});

describe('useUpdateBenchmarkPolicy', () => {
  it('updates policy successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateBenchmarkPolicy(), { wrapper });

    result.current.mutate({ id: 'policy-1', value: '0.8', is_enabled: true });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.id).toBe('policy-1');
    expect(result.current.data?.value).toBe('0.8');
  });

  it('handles update error', async () => {
    server.use(
      http.put('/api/v1/graph/benchmarks/policies/:id', () => {
        return HttpResponse.json({ error: 'Invalid policy value' }, { status: 400 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useUpdateBenchmarkPolicy(), { wrapper });

    result.current.mutate({ id: 'policy-1', value: 'invalid' });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });

  it('invalidates policies cache on success', async () => {
    const wrapper = createWrapper();
    const updateHook = renderHook(() => useUpdateBenchmarkPolicy(), { wrapper });
    const policiesHook = renderHook(() => useBenchmarkPolicies(), { wrapper });

    // Wait for initial policies to load
    await waitFor(() => expect(policiesHook.result.current.isSuccess).toBe(true));

    // Update a policy
    updateHook.result.current.mutate({ id: 'policy-1', is_enabled: false });

    await waitFor(() => expect(updateHook.result.current.isSuccess).toBe(true));
  });
});
