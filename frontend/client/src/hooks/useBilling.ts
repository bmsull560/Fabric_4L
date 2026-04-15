import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';
import { apiClient } from '@/api/client';
import { withApiError, BaseApiError, STALE_TIME } from './useApiShared';

// Types
export interface Subscription {
  id: string | null;
  plan_id: 'free' | 'pro' | 'enterprise';
  status: string;
  current_period_start: string | null;
  current_period_end: string | null;
  cancel_at_period_end: boolean;
}

export interface EntitlementsResponse {
  plan_id: string;
  plan_name: string;
  features: Record<string, {
    enabled: boolean;
    name: string;
    description: string;
  }>;
}

export interface FeatureCheck {
  feature_id: string;
  has_access: boolean;
}

export interface CheckoutResponse {
  session_id: string;
  url: string;
}

export interface PortalResponse {
  url: string;
}

// Query keys
export const billingKeys = {
  all: ['billing'] as const,
  subscription: (customerId: string) => [...billingKeys.all, 'subscription', customerId] as const,
  entitlements: (customerId: string) => [...billingKeys.all, 'entitlements', customerId] as const,
  feature: (customerId: string, featureId: string) => [...billingKeys.all, 'feature', customerId, featureId] as const,
};

// Hooks
export function useBilling(customerId: string) {
  const queryClient = useQueryClient();
  const [checkoutError, setCheckoutError] = useState<Error | null>(null);
  const [portalError, setPortalError] = useState<Error | null>(null);

  const subscriptionQuery = useQuery({
    queryKey: billingKeys.subscription(customerId),
    queryFn: async () => {
      const response = await apiClient.get('l4', `/billing/subscription?customer_id=${customerId}`);
      return response.data as Subscription;
    },
    enabled: !!customerId,
    staleTime: STALE_TIME.detail,
  });

  const createCheckoutMutation = useMutation({
    mutationFn: async (params: {
      plan_id: string;
      success_url: string;
      cancel_url: string;
    }) => {
      setCheckoutError(null);
      return withApiError(
        apiClient.post('l4', `/billing/checkout?customer_id=${customerId}`, params).then(r => r.data as CheckoutResponse),
        BaseApiError
      );
    },
    onSuccess: () => {
      // Invalidate all billing-related queries (subscription, entitlements, features)
      queryClient.invalidateQueries({ queryKey: billingKeys.all });
    },
    onError: (error) => {
      setCheckoutError(error instanceof Error ? error : new Error(String(error)));
      console.error('Checkout mutation failed:', error);
    },
  });

  const createPortalMutation = useMutation({
    mutationFn: async (returnUrl: string) => {
      setPortalError(null);
      return withApiError(
        apiClient.post('l4', `/billing/portal?customer_id=${customerId}`, { return_url: returnUrl }).then(r => r.data as PortalResponse),
        BaseApiError
      );
    },
    onError: (error) => {
      setPortalError(error instanceof Error ? error : new Error(String(error)));
      console.error('Portal mutation failed:', error);
    },
  });

  const openCustomerPortal = async (returnUrl: string) => {
    const result = await createPortalMutation.mutateAsync(returnUrl);
    if (result.url) {
      window.location.href = result.url;
    }
  };

  const subscribe = async (planId: string, successUrl: string, cancelUrl: string) => {
    const result = await createCheckoutMutation.mutateAsync({
      plan_id: planId,
      success_url: successUrl,
      cancel_url: cancelUrl,
    });
    if (result.url) {
      window.location.href = result.url;
    }
  };

  const clearErrors = useCallback(() => {
    setCheckoutError(null);
    setPortalError(null);
  }, []);

  return {
    // Data
    subscription: subscriptionQuery.data,
    isLoading: subscriptionQuery.isLoading,
    error: subscriptionQuery.error,

    // Mutation errors (exposed for UI display)
    checkoutError,
    portalError,
    clearErrors,

    // Actions
    openCustomerPortal,
    subscribe,

    // Mutation states
    isSubscribing: createCheckoutMutation.isPending,
    isOpeningPortal: createPortalMutation.isPending,
  };
}

export function useEntitlements(customerId: string) {
  return useQuery({
    queryKey: billingKeys.entitlements(customerId),
    queryFn: async () => {
      const response = await apiClient.get('l4', `/billing/entitlements?customer_id=${customerId}`);
      return response.data as EntitlementsResponse;
    },
    enabled: !!customerId,
    staleTime: STALE_TIME.detail,
  });
}

export function useFeatureCheck(customerId: string, featureId: string) {
  return useQuery({
    queryKey: billingKeys.feature(customerId, featureId),
    queryFn: async () => {
      const response = await apiClient.get(
        'l4',
        `/billing/check-feature?customer_id=${customerId}&feature_id=${featureId}`
      );
      return response.data as FeatureCheck;
    },
    enabled: !!customerId && !!featureId,
    staleTime: STALE_TIME.detail,
  });
}
