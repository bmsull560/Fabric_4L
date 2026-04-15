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
import { server } from '../../../test/mocks/server';
import {
  useBenchmarks,
  useBenchmark,
} from './useBenchmarks';

// L6 Benchmark handlers for testing
const l6BenchmarkHandlers = [
  // List datasets (benchmarks)
  http.get('/api/v1/benchmarks/datasets', ({ request }) => {
    const url = new URL(request.url);
    const industry = url.searchParams.get('industry');
    const status = url.searchParams.get('status');
    const confidence = url.searchParams.get('confidence');

    let benchmarks = [
      {
        id: 'bench-1',
        benchmark_id: 'bench-1',
        name: 'Industry Average ROI',
        industry: industry || 'Software',
        vertical: 'SaaS',
        value_range: '2.5x - 4.0x',
        confidence: confidence || 'High',
        source: 'Industry Research',
        year: 2024,
        status: status || 'active',
        tags: ['roi', 'saas'],
        usage_count: 15,
      },
      {
        id: 'bench-2',
        benchmark_id: 'bench-2',
        name: 'Implementation Timeline',
        industry: industry || 'Software',
        vertical: 'Enterprise',
        value_range: '3-6 months',
        confidence: 'Medium',
        source: 'Survey Data',
        year: 2024,
        status: status || 'active',
        tags: ['timeline'],
        usage_count: 8,
      },
    ];

    // Apply status filter
    if (status && status !== 'all') {
      benchmarks = benchmarks.filter(b => b.status === status);
    }

    return HttpResponse.json(benchmarks);
  }),

  // Single dataset (benchmark)
  http.get('/api/v1/benchmarks/datasets/:id', ({ params }) => {
    const id = params.id as string;
    return HttpResponse.json({
      id,
      benchmark_id: id,
      name: 'Detailed Benchmark',
      industry: 'Software',
      vertical: 'SaaS',
      value_range: '2.5x - 4.0x',
      confidence: 'High',
      source: 'Industry Research',
      year: 2024,
      status: 'active',
      tags: ['detailed'],
      usage_count: 10,
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
      confidence: expect.any(String),
    });
  });

  it('applies industry filter', async () => {
    server.use(
      http.get('/api/v1/benchmarks/datasets', ({ request }) => {
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
      http.get('/api/v1/benchmarks/datasets', () => {
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
      http.get('/api/v1/benchmarks/datasets/:id', () => {
        return HttpResponse.json({ error: 'Benchmark not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmark('non-existent'), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));
  });
});

