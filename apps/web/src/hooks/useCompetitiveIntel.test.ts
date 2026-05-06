/**
 * useCompetitiveIntel Hook Tests
 *
 * Tests for competitive intelligence hooks including:
 * - useBattlecard: Single battlecard fetch by competitor + product
 * - useBattlecards: List battlecards for a competitor (existing)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper, createMockResponse } from '../test-utils';
import { apiClient } from '@/api/client';
import {
  useBattlecard,
  useBattlecards,
  type Battlecard,
} from './useCompetitiveIntel';

// Mock the apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

const sampleBattlecard: Battlecard = {
  id: 'bc-001',
  competitor_id: 'comp-001',
  product_id: 'prod-001',
  positioning: 'Leader in enterprise security',
  differentiators: ['AI-powered detection', 'Zero-trust architecture'],
  key_differentiators: ['AI-powered detection', 'Zero-trust architecture'],
  objection_handlers: ['Price objection: ROI proven within 6 months'],
  talk_tracks: ['Security is not a cost center, it is revenue protection'],
  win_themes: ['Faster time to value', 'Lower TCO'],
  trap_questions: ['How do you currently measure security ROI?'],
  status: 'created',
  entity_type: 'battlecard',
  tenant_id: 'tenant-001',
  last_reviewed_at: '2024-01-15T00:00:00Z',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-15T00:00:00Z',
};

const sampleBattlecardList: Battlecard[] = [
  sampleBattlecard,
  {
    ...sampleBattlecard,
    id: 'bc-002',
    product_id: 'prod-002',
    positioning: 'Best for mid-market',
  },
];

describe('useBattlecard', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it('fetches a single battlecard by competitor and product', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse(sampleBattlecard)
    );

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useBattlecard('comp-001', 'prod-001'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleBattlecard);
    expect(apiClient.get).toHaveBeenCalledWith(
      'l3',
      '/v1/competitive/competitors/comp-001/battlecard?product_id=prod-001'
    );
  });

  it('is disabled when competitorId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useBattlecard(null, 'prod-001'),
      { wrapper }
    );

    expect(result.current.isPending).toBe(true);
    expect(result.current.fetchStatus).toBe('idle');
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('is disabled when productId is null', () => {
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useBattlecard('comp-001', null),
      { wrapper }
    );

    expect(result.current.isPending).toBe(true);
    expect(result.current.fetchStatus).toBe('idle');
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('handles API errors gracefully', async () => {
    vi.mocked(apiClient.get).mockRejectedValue(
      new Error('Battlecard not found')
    );

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useBattlecard('comp-001', 'prod-001'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
    expect(result.current.error?.message).toContain('Battlecard not found');
  });

  it('encodes URL parameters', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse(sampleBattlecard)
    );

    const wrapper = createWrapper();
    renderHook(() => useBattlecard('comp with spaces', 'prod/slash'), {
      wrapper,
    });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());

    const callArg = vi.mocked(apiClient.get).mock.calls[0][1] as string;
    expect(callArg).toContain(encodeURIComponent('comp with spaces'));
    expect(callArg).toContain(encodeURIComponent('prod/slash'));
  });
});

describe('useBattlecards (regression)', () => {
  beforeEach(() => {
    vi.mocked(apiClient.get).mockReset();
  });

  it('still fetches battlecard list correctly', async () => {
    vi.mocked(apiClient.get).mockResolvedValue(
      createMockResponse(sampleBattlecardList)
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useBattlecards('comp-001'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toHaveLength(2);
    expect(apiClient.get).toHaveBeenCalledWith(
      'l3',
      '/v1/competitive/competitors/comp-001/battlecards'
    );
  });
});
