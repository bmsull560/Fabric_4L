/**
 * useROICalculator Hook Tests
 *
 * Tests for ROI calculator hooks including:
 * - useBenchmarksList: Fetch all benchmarks
 * - useBenchmarkDetail: Fetch single benchmark by ID
 * - useROICalculationAgent: Agent-powered ROI calculation mutation
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper, createMockResponse } from '../test-utils';
import { apiClient } from '@/api/client';
import {
  useBenchmarksList,
  useBenchmarkDetail,
  useROICalculationAgent,
  type Benchmark,
  type BenchmarkListResponse,
  type ROICalculationAgentResult,
} from './useROICalculator';

// Mock the apiClient
vi.mock('@/api/client', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/api/client')>();
  return {
    ...actual,
    apiClient: {
      get: vi.fn(),
      post: vi.fn(),
    },
  };
});

const sampleBenchmarks: BenchmarkListResponse = {
  benchmarks: [
    {
      id: 'bench-001',
      name: 'SaaS Customer Acquisition Cost',
      industry: 'Software',
      metric: 'cac',
      value: 12500,
      unit: 'USD',
      source: 'Industry Research 2024',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-06-01T00:00:00Z',
    },
    {
      id: 'bench-002',
      name: 'Enterprise Sales Cycle',
      industry: 'Software',
      metric: 'sales_cycle_months',
      value: 4.5,
      unit: 'months',
      source: 'Survey Data',
      created_at: '2024-02-01T00:00:00Z',
      updated_at: '2024-06-01T00:00:00Z',
    },
  ],
  total: 2,
};

const sampleBenchmark: Benchmark = sampleBenchmarks.benchmarks[0];

const sampleAgentResult: ROICalculationAgentResult = {
  id: 'calc-agent-001',
  npv: 850000,
  irr: 0.35,
  payback_months: 14,
  total_roi_pct: 280,
  annual_projections: [
    { year: 1, cost: 300000, benefit: 450000, cumulative_net: 150000, discounted_benefit: 409091 },
    { year: 2, cost: 150000, benefit: 600000, cumulative_net: 600000, discounted_benefit: 495868 },
  ],
  scenarios: {
    conservative: { npv: 600000, irr: 0.28, payback_months: 18 },
    optimistic: { npv: 1100000, irr: 0.42, payback_months: 10 },
  },
  confidence_score: 0.87,
  recommended_actions: [
    'Focus on Q1 implementation to capture early benefits',
    'Monitor customer adoption metrics closely',
  ],
  created_at: '2024-01-15T10:00:00Z',
};

describe('useBenchmarksList', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it('fetches all benchmarks', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse(sampleBenchmarks)
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarksList(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleBenchmarks);
    expect(result.current.data?.benchmarks).toHaveLength(2);
    expect(apiClient.get).toHaveBeenCalledWith('l3', '/v1/roi/benchmarks');
  });

  it('handles empty benchmark list', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse({ benchmarks: [], total: 0 })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarksList(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.benchmarks).toHaveLength(0);
    expect(result.current.data?.total).toBe(0);
  });

  it('handles API errors', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(
      new Error('Failed to fetch benchmarks')
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarksList(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toContain('Failed to fetch benchmarks');
  });
});

describe('useBenchmarkDetail', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it('fetches a single benchmark by ID', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse(sampleBenchmark)
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarkDetail('bench-001'), {
      wrapper,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleBenchmark);
    expect(apiClient.get).toHaveBeenCalledWith(
      'l3',
      '/v1/roi/benchmarks/bench-001'
    );
  });

  it('is disabled when benchmarkId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useBenchmarkDetail(null), { wrapper });

    expect(result.current.isPending).toBe(true);
    expect(result.current.fetchStatus).toBe('idle');
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('encodes benchmark ID in URL', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse(sampleBenchmark)
    );

    const wrapper = createWrapper();
    renderHook(() => useBenchmarkDetail('bench/with/slash'), { wrapper });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

    const callArg = vi.mocked(apiClient.get).mock.calls[0][1] as string;
    expect(callArg).toContain(encodeURIComponent('bench/with/slash'));
  });
});

describe('useROICalculationAgent', () => {
  beforeEach(() => {
    vi.mocked(apiClient.post).mockReset();
  });

  it('submits ROI calculation to agent endpoint', async () => {
    vi.mocked(apiClient.post).mockResolvedValue(
      createMockResponse(sampleAgentResult)
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useROICalculationAgent(), { wrapper });

    result.current.mutate({
      deal_size: 1000000,
      implementation_cost: 300000,
      annual_benefit: 500000,
      time_horizon_years: 3,
      discount_rate: 0.1,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleAgentResult);
    expect(apiClient.post).toHaveBeenCalledWith(
      'l3',
      '/v1/agents/roi-calculation',
      expect.objectContaining({
        deal_size: 1000000,
        implementation_cost: 300000,
        annual_benefit: 500000,
      })
    );
  });

  it('includes confidence score and recommendations in response', async () => {
    vi.mocked(apiClient.post).mockResolvedValue(
      createMockResponse(sampleAgentResult)
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useROICalculationAgent(), { wrapper });

    result.current.mutate({
      deal_size: 1000000,
      implementation_cost: 300000,
      annual_benefit: 500000,
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.confidence_score).toBe(0.87);
    expect(result.current.data?.recommended_actions).toHaveLength(2);
  });

  it('handles API errors', async () => {
    vi.mocked(apiClient.post).mockRejectedValue(
      new Error('Agent calculation failed')
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useROICalculationAgent(), { wrapper });

    result.current.mutate({
      deal_size: 1000000,
      implementation_cost: 300000,
      annual_benefit: 500000,
    });

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toContain('Agent calculation failed');
  });
});
