import React from 'react';
import { useBillingContext } from '@/context/BillingContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Loader2, CreditCard, Check } from 'lucide-react';

const PLAN_INFO: Record<string, { name: string; description: string; price: string }> = {
  free: {
    name: 'Free',
    description: 'Basic extraction and knowledge exploration',
    price: '$0',
  },
  pro: {
    name: 'Pro',
    description: 'Advanced AI models and team collaboration',
    price: '$19/mo',
  },
  enterprise: {
    name: 'Enterprise',
    description: 'Full platform with custom integrations',
    price: 'Custom',
  },
};

export function BillingSettings() {
  const {
    subscription,
    isLoading,
    error,
    entitlements,
    openCustomerPortal,
    subscribe,
    isSubscribing,
    isOpeningPortal,
    hasFeature,
    canUpgrade,
  } = useBillingContext();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    );
  }

  if (error) {
    // Sanitize error message to prevent XSS from malicious Stripe payloads
    const sanitizedMessage = error.message?.replace(/[<>&"']/g, '') || 'Unknown error';
    return (
      <div className="p-6">
        <Card>
          <CardContent className="pt-6">
            <p className="text-red-600">Failed to load billing information: {sanitizedMessage}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const currentPlan = subscription?.plan_id || 'free';
  const planInfo = PLAN_INFO[currentPlan];

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Billing & Subscription</h1>

      {/* Current Plan Card */}
      <Card className="mb-6">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Current Plan</CardTitle>
              <CardDescription>Manage your subscription and billing</CardDescription>
            </div>
            <Badge variant={currentPlan === 'free' ? 'secondary' : 'default'} className="text-lg px-3 py-1">
              {planInfo.name}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-baseline gap-2">
              <span className="text-4xl font-bold">{planInfo.price}</span>
              {currentPlan !== 'free' && currentPlan !== 'enterprise' && (
                <span className="text-muted-foreground">/month</span>
              )}
            </div>
            <p className="text-muted-foreground">{planInfo.description}</p>

            {subscription?.cancel_at_period_end && (
              <div className="bg-yellow-50 border border-yellow-200 rounded p-3 text-yellow-800">
                Your subscription will cancel at the end of the current billing period
                {subscription.current_period_end && (
                  <> ({new Date(subscription.current_period_end).toLocaleDateString()})</>
                )}
              </div>
            )}

            <div className="flex gap-3 pt-4">
              {currentPlan !== 'free' ? (
                <Button
                  onClick={() => openCustomerPortal(window.location.href)}
                  disabled={isOpeningPortal}
                  variant="outline"
                >
                  {isOpeningPortal ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Opening...
                    </>
                  ) : (
                    <>
                      <CreditCard className="mr-2 h-4 w-4" />
                      Manage Billing
                    </>
                  )}
                </Button>
              ) : null}

              {canUpgrade && (
                <Button
                  onClick={() => {
                    const plan = currentPlan === 'free' ? 'pro' : 'enterprise';
                    subscribe(plan, window.location.href, window.location.href);
                  }}
                  disabled={isSubscribing}
                >
                  {isSubscribing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Upgrading...
                    </>
                  ) : (
                    <>Upgrade to {currentPlan === 'free' ? 'Pro' : 'Enterprise'}</>
                  )}
                </Button>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Features Card */}
      <Card>
        <CardHeader>
          <CardTitle>Plan Features</CardTitle>
          <CardDescription>Features included in your current plan</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4 md:grid-cols-2">
            {entitlements?.features && Object.entries(entitlements.features).map(([featureId, feature]) => (
              <div
                key={featureId}
                className={`flex items-start gap-3 p-3 rounded-lg border ${
                  feature.enabled ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200 opacity-60'
                }`}
              >
                <div className={`mt-0.5 ${feature.enabled ? 'text-green-600' : 'text-gray-400'}`}>
                  <Check className="h-4 w-4" />
                </div>
                <div>
                  <p className={`font-medium ${feature.enabled ? 'text-green-900' : 'text-gray-600'}`}>
                    {feature.name}
                  </p>
                  <p className={`text-sm ${feature.enabled ? 'text-green-700' : 'text-gray-500'}`}>
                    {feature.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
