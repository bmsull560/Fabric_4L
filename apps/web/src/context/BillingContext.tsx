import { createContext, useContext, useMemo, useCallback, type ReactNode } from 'react';
import { useBilling, useEntitlements, Subscription, EntitlementsResponse } from '@/hooks/useBilling';

interface BillingContextType {
  // Current subscription
  customerId: string;
  subscription: Subscription | undefined;
  isLoading: boolean;
  error: Error | null;

  // Entitlements
  entitlements: EntitlementsResponse | undefined;

  // Actions
  openCustomerPortal: (returnUrl: string) => Promise<void>;
  subscribe: (planId: string, successUrl: string, cancelUrl: string) => Promise<void>;

  // Loading states
  isSubscribing: boolean;
  isOpeningPortal: boolean;

  // Helper
  hasFeature: (featureId: string) => boolean;
  canUpgrade: boolean;
}

const BillingContext = createContext<BillingContextType | null>(null);

interface BillingProviderProps {
  children: ReactNode;
  customerId: string;
}

export function BillingProvider({ children, customerId }: BillingProviderProps) {
  const billing = useBilling(customerId);
  const entitlementsQuery = useEntitlements(customerId);

  const hasFeature = useCallback((featureId: string): boolean => {
    if (!entitlementsQuery.data) return false;
    return entitlementsQuery.data.features[featureId]?.enabled ?? false;
  }, [entitlementsQuery.data]);

  const canUpgrade = billing.subscription?.plan_id !== 'enterprise';

  const value = useMemo((): BillingContextType => ({
    customerId,
    subscription: billing.subscription,
    isLoading: billing.isLoading,
    error: billing.error,
    entitlements: entitlementsQuery.data,
    openCustomerPortal: billing.openCustomerPortal,
    subscribe: billing.subscribe,
    isSubscribing: billing.isSubscribing,
    isOpeningPortal: billing.isOpeningPortal,
    hasFeature,
    canUpgrade,
  }), [
    customerId,
    billing.subscription,
    billing.isLoading,
    billing.error,
    entitlementsQuery.data,
    billing.openCustomerPortal,
    billing.subscribe,
    billing.isSubscribing,
    billing.isOpeningPortal,
    hasFeature,
    canUpgrade,
  ]);

  return (
    <BillingContext.Provider value={value}>
      {children}
    </BillingContext.Provider>
  );
}

export function useBillingContext(): BillingContextType {
  const context = useContext(BillingContext);
  if (!context) {
    throw new Error('useBillingContext must be used within a BillingProvider');
  }
  return context;
}
