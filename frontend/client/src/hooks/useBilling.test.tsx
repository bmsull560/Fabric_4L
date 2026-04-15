import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useBilling, useEntitlements, useFeatureCheck, billingKeys } from './useBilling';
import { apiClient } from '@/api/client';
import { createWrapper, createMockResponse } from '@/test-utils';

// Mock apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// Type for mocked apiClient
const mockGet = apiClient.get as Mock;
const mockPost = apiClient.post as Mock;

describe('useBilling', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch subscription data', async () => {
    const mockSubscription = {
      id: 'sub_123',
      plan_id: 'pro',
      status: 'active',
      current_period_start: '2024-01-01T00:00:00Z',
      current_period_end: '2024-02-01T00:00:00Z',
      cancel_at_period_end: false,
    };

    mockGet.mockResolvedValue(createMockResponse(mockSubscription));

    const { result } = renderHook(() => useBilling('user_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.subscription).toEqual(mockSubscription));

    expect(mockGet).toHaveBeenCalledWith('l4', '/billing/subscription?customer_id=user_123');
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should handle subscription error', async () => {
    mockGet.mockRejectedValue(new Error('Failed to fetch'));

    const { result } = renderHook(() => useBilling('user_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.error).toBeTruthy());
    expect(result.current.subscription).toBeUndefined();
  });

  it('should open customer portal', async () => {
    const mockPortalResponse = { url: 'https://billing.stripe.com/portal' };
    mockGet.mockResolvedValue(createMockResponse({ plan_id: 'pro' }));
    mockPost.mockResolvedValue(createMockResponse(mockPortalResponse));

    // Mock window.location.href
    const originalHref = window.location.href;
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { href: originalHref },
    });

    const { result } = renderHook(() => useBilling('user_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.subscription).toBeTruthy());

    await result.current.openCustomerPortal('http://localhost:5173/settings');

    expect(mockPost).toHaveBeenCalledWith(
      'l4',
      '/billing/portal?customer_id=user_123',
      { return_url: 'http://localhost:5173/settings' }
    );
    expect(window.location.href).toBe('https://billing.stripe.com/portal');
  });

  it('should initiate checkout for upgrade', async () => {
    const mockCheckoutResponse = { session_id: 'sess_123', url: 'https://checkout.stripe.com/pay' };
    mockGet.mockResolvedValue(createMockResponse({ plan_id: 'free' }));
    mockPost.mockResolvedValue(createMockResponse(mockCheckoutResponse));

    // Mock window.location.href
    Object.defineProperty(window, 'location', {
      writable: true,
      value: { href: 'http://localhost:5173' },
    });

    const { result } = renderHook(() => useBilling('user_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.subscription).toBeTruthy());

    await result.current.subscribe('pro', 'http://localhost:5173/success', 'http://localhost:5173/cancel');

    expect(mockPost).toHaveBeenCalledWith(
      'l4',
      '/billing/checkout?customer_id=user_123',
      {
        plan_id: 'pro',
        success_url: 'http://localhost:5173/success',
        cancel_url: 'http://localhost:5173/cancel',
      }
    );
    expect(window.location.href).toBe('https://checkout.stripe.com/pay');
  });

  it('should track loading states', async () => {
    mockGet.mockImplementation(() => new Promise(() => {})); // Never resolves

    const { result } = renderHook(() => useBilling('user_123'), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(true);
  });
});

describe('useEntitlements', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should fetch entitlements', async () => {
    const mockEntitlements = {
      plan_id: 'pro',
      plan_name: 'Pro',
      features: {
        basic_extraction: { enabled: true, name: 'Basic Extraction', description: '...' },
        advanced_models: { enabled: true, name: 'Advanced Models', description: '...' },
      },
    };

    mockGet.mockResolvedValue(createMockResponse(mockEntitlements));

    const { result } = renderHook(() => useEntitlements('user_123'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.data).toEqual(mockEntitlements));
    expect(mockGet).toHaveBeenCalledWith('l4', '/billing/entitlements?customer_id=user_123');
  });
});

describe('useFeatureCheck', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should check feature access', async () => {
    mockGet.mockResolvedValue(createMockResponse({ feature_id: 'advanced_models', has_access: true }));

    const { result } = renderHook(() => useFeatureCheck('user_123', 'advanced_models'), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.data?.has_access).toBe(true));
    expect(mockGet).toHaveBeenCalledWith(
      'l4',
      '/billing/check-feature?customer_id=user_123&feature_id=advanced_models'
    );
  });

  it('should not run when customerId is empty', async () => {
    mockGet.mockResolvedValue(createMockResponse({ has_access: false }));

    const { result } = renderHook(() => useFeatureCheck('', 'feature_1'), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
    expect(mockGet).not.toHaveBeenCalled();
  });

  it('should not run when featureId is empty', async () => {
    mockGet.mockResolvedValue(createMockResponse({ has_access: false }));

    const { result } = renderHook(() => useFeatureCheck('user_123', ''), {
      wrapper: createWrapper(),
    });

    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
    expect(mockGet).not.toHaveBeenCalled();
  });
});

describe('billingKeys', () => {
  it('should generate correct query keys', () => {
    expect(billingKeys.all).toEqual(['billing']);
    expect(billingKeys.subscription('user_123')).toEqual(['billing', 'subscription', 'user_123']);
    expect(billingKeys.entitlements('user_123')).toEqual(['billing', 'entitlements', 'user_123']);
    expect(billingKeys.feature('user_123', 'feature_1')).toEqual(['billing', 'feature', 'user_123', 'feature_1']);
  });
});
