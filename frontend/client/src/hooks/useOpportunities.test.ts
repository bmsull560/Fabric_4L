/**
 * useOpportunities Hook Tests
 *
 * Tests for the opportunities discovery API hook:
 * - Fetches opportunities from /v1/discover/opportunities
 * - Validates response format
 * - Handles errors appropriately
 * - Applies caching and retry logic
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper, createWrapperWithRetry } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useOpportunities,
  OpportunitiesApiError,
  type Opportunity,
} from './useOpportunities';

// Test data factory
function createMockOpportunity(overrides?: Partial<Opportunity>): Opportunity {
  return {
    id: 'opp-1',
    title: 'License Consolidation Opportunity',
    description: 'Customer has 5 separate license agreements that could be consolidated',
    account: 'Acme Corporation',
    accountId: 'acc-123',
    category: 'Cost Optimization',
    status: 'qualified',
    impact: 'high',
    estimatedValue: '$450K',
    confidenceScore: 87,
    aiScore: 92,
    discoveredAt: '2024-01-15T10:30:00Z',
    insights: ['5 active licenses detected'],
    recommendedActions: ['Schedule consolidation call'],
    sources: ['CRM Data', 'Contract Analysis'],
    ...overrides,
  };
}

const mockOpportunitiesResponse = {
  opportunities: [
    createMockOpportunity(),
    createMockOpportunity({
      id: 'opp-2',
      title: 'Analytics Upsell',
      category: 'Upsell',
      status: 'investigating',
      impact: 'medium',
    }),
  ],
  total: 2,
  generatedAt: '2024-01-15T10:30:00Z',
};

describe('useOpportunities', () => {
  it('fetches opportunities successfully', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', () => {
        return HttpResponse.json(mockOpportunitiesResponse);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.opportunities).toHaveLength(2);
    expect(result.current.data?.total).toBe(2);
    expect(result.current.data?.opportunities[0].title).toBe(
      'License Consolidation Opportunity'
    );
  });

  it('returns empty array when no opportunities exist', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', () => {
        return HttpResponse.json({
          opportunities: [],
          total: 0,
          generatedAt: '2024-01-15T10:30:00Z',
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.opportunities).toEqual([]);
    expect(result.current.data?.total).toBe(0);
  });

  it('validates response format and throws on invalid data', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', () => {
        // Return invalid response missing required 'opportunities' array
        return HttpResponse.json({
          total: 0,
          generatedAt: '2024-01-15T10:30:00Z',
        });
      })
    );

    // Use createWrapperWithRetry(false) for faster error state detection
    const wrapper = createWrapperWithRetry(false);
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 10000 });

    expect(result.current.error).toBeInstanceOf(OpportunitiesApiError);
    expect(result.current.error?.message).toContain('Missing or invalid opportunities array');
  }, 30000);

  it('validates that response data is an object', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', () => {
        // Return non-object response
        return HttpResponse.json('invalid response');
      })
    );

    // Use createWrapperWithRetry(false) for faster error state detection
    const wrapper = createWrapperWithRetry(false);
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 10000 });

    expect(result.current.error).toBeInstanceOf(OpportunitiesApiError);
    expect(result.current.error?.message).toContain('Invalid response format');
  }, 30000);

  it('handles API error responses', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', () => {
        return new HttpResponse(null, { status: 500 });
      })
    );

    // Use createWrapperWithRetry(false) for faster error state detection
    const wrapper = createWrapperWithRetry(false);
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 10000 });

    expect(result.current.error).toBeDefined();
    expect(result.current.error).toBeInstanceOf(OpportunitiesApiError);
  }, 30000);

  it('returns error with status code when API fails', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', () => {
        return new HttpResponse(JSON.stringify({ error: 'Unauthorized' }), {
          status: 401,
          headers: { 'Content-Type': 'application/json' },
        });
      })
    );

    // Use createWrapperWithRetry(false) for faster error state detection
    const wrapper = createWrapperWithRetry(false);
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 10000 });

    expect(result.current.error).toBeInstanceOf(OpportunitiesApiError);
    expect(result.current.error?.statusCode).toBe(401);
  }, 30000);

  it('indicates loading state while fetching', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', async () => {
        // Add slight delay to ensure loading state is visible
        await new Promise((resolve) => setTimeout(resolve, 50));
        return HttpResponse.json(mockOpportunitiesResponse);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    // Initially loading
    expect(result.current.isLoading).toBe(true);
    expect(result.current.isSuccess).toBe(false);

    // After completion
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.isLoading).toBe(false);
  });

  it('exposes opportunities array in consistent format', async () => {
    server.use(
      http.get('/api/v1/agents/discover/opportunities', () => {
        return HttpResponse.json(mockOpportunitiesResponse);
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useOpportunities(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    const opportunity = result.current.data?.opportunities[0];
    expect(opportunity).toMatchObject({
      id: expect.any(String),
      title: expect.any(String),
      description: expect.any(String),
      account: expect.any(String),
      accountId: expect.any(String),
      category: expect.any(String),
      status: expect.any(String),
      impact: expect.any(String),
      estimatedValue: expect.any(String),
      confidenceScore: expect.any(Number),
      aiScore: expect.any(Number),
      discoveredAt: expect.any(String),
      insights: expect.any(Array),
      recommendedActions: expect.any(Array),
      sources: expect.any(Array),
    });
  });
});
