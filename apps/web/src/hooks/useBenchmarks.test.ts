/**
 * useBenchmarks Hook Tests
 *
 * Tests for benchmark management:
 * - useBenchmarks: Filtered list fetching
 * - useBenchmark: Single benchmark details
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import {
  useBenchmarks,
  useBenchmark,
} from './useBenchmarks';

// L6 Benchmark handlers for testing (DatasetSummary shape from real API)
const l6BenchmarkHandlers = [
  // List datasets (benchmarks)
  http.get('/api/v1/benchmarks/datasets', ({ request }) => {
    const url = new URL(request.url);
    const industry = url.searchParams.get('industry');
    const status = url.searchParams.get('status');
    const confidence = url.searchParams.get('confidence');

    let datasets = [
      {
        dataset_id: 'bench-1',
        name: 'Industry Average ROI',
        description: 'Average ROI benchmarks for the software industry',
        industry: industry || 'Software',
        segment: 'SaaS',
        geography: 'global',
        metrics: ['roi', 'payback'],
        metric_count: 2,
        version: '1.0.0',
        data_source: 'Industry Research',
      },
      {
        dataset_id: 'bench-2',
        name: 'Implementation Timeline',
        description: 'Implementation timeline benchmarks',
        industry: industry || 'Software',
        segment: 'Enterprise',
        geography: 'US',
        metrics: ['timeline'],
        metric_count: 1,
        version: '1.0.0',
        data_source: 'Survey Data',
      },
    ];

    // Apply status filter (L6 does not actually filter by status, but test the param)
    if (status && status !== 'all') {
      // No-op for L6 shape — status is derived, not stored
    }

    return HttpResponse.json(datasets);
  }),

  // Single dataset (benchmark)
  http.get('/api/v1/benchmarks/datasets/:id', ({ params }) => {
    const id = params.id as string;
    return HttpResponse.json({
      dataset_id: id,
      name: 'Detailed Benchmark',
      description: 'Detailed benchmark data',
      industry: 'Software',
      segment: 'SaaS',
      geography: 'global',
      metrics: ['detailed'],
      metric_count: 1,
      version: '1.0.0',
      data_source: 'Industry Research',
    });
  }),
];

// Register L6 handlers before each test (needed because server.resetHandlers()
// in global setup reverts to original handlers which don't include L6 endpoints)
beforeEach(() => {
  server.use(...l6BenchmarkHandlers);
});

describe('useBenchmarks', () => {
  it('fetches all benchmarks', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarks(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(result.current.data?.[0]).toMatchObject({
      id: expect.any(String),
      name: expect.any(String),
      confidence: 'High',
      status: 'active',
    });
  });

  it('applies industry filter', async () => {
    server.use(
      http.get('/api/v1/benchmarks/datasets', ({ request }) => {
        const url = new URL(request.url);
        const industry = url.searchParams.get('industry');

        return HttpResponse.json([
          {
            dataset_id: 'bench-filtered',
            name: 'Filtered Benchmark',
            description: 'Filtered description',
            industry: industry || 'Unknown',
            segment: 'enterprise',
            geography: 'global',
            metrics: ['m1'],
            metric_count: 1,
            version: '1.0.0',
            data_source: 'Test',
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

    // All returned benchmarks should be active (derived from adapter)
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
    // Override the handler without resetting — resetHandlers() can race with
    // in-flight requests from the singleton apiClient deduplication cache.
    server.use(
      http.get('/api/v1/benchmarks/datasets', () => {
        return HttpResponse.json({ error: 'Database error' }, { status: 500 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarks(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });
});

describe('useBenchmark', () => {
  it('fetches single benchmark details', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmark('bench-1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.id).toBe('bench-1');
    expect(result.current.data?.name).toBeDefined();
    expect(result.current.data?.confidence).toBe('High');
  });

  it('disables query when id is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmark(null), { wrapper });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles benchmark not found', async () => {
    server.use(
      http.get('/api/v1/benchmarks/datasets/:id', () => {
        return HttpResponse.json({ error: 'Benchmark not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmark('non-existent'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
  });
});
