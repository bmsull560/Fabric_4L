import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import { apiGet } from '@/api/typedClient';
import { STALE_TIME } from './useApiShared';

// ============================================================================
// Types
// ============================================================================

export interface Invoice {
  id: string;
  invoice_number: string;
  customer_id: string;
  status: 'draft' | 'open' | 'paid' | 'void' | 'uncollectible';
  currency: string;
  subtotal_cents: number;
  tax_cents: number;
  total_cents: number;
  total_dollars: number;
  amount_paid_cents: number;
  amount_due_cents: number;
  amount_due_dollars: number;
  balance_cents: number;
  period_start: string;
  period_end: string;
  due_date: string;
  paid_at: string | null;
  voided_at: string | null;
  created_at: string;
  description: string | null;
  hosted_invoice_url: string | null;
  invoice_pdf_url: string | null;
  item_count: number;
}

export interface InvoiceItem {
  id: string;
  type: 'subscription' | 'metered' | 'one_time' | 'proration';
  description: string;
  quantity: number;
  unit_amount_cents: number;
  amount_cents: number;
  amount_dollars: number;
  period_start: string | null;
  period_end: string | null;
  usage_quantity: number | null;
  usage_metric: string | null;
  tax_cents: number;
  discount_cents: number;
}

export interface Charge {
  id: string;
  customer_id: string;
  invoice_id: string | null;
  invoice_number: string | null;
  status: 'succeeded' | 'pending' | 'failed';
  amount_cents: number;
  amount_dollars: number;
  amount_refunded_cents: number;
  net_amount_cents: number;
  stripe_charge_id: string | null;
  payment_method_id: string | null;
  payment_method_type: string | null;
  failure_code: string | null;
  failure_message: string | null;
  receipt_url: string | null;
  description: string | null;
  created_at: string;
  captured_at: string | null;
  refunded_at: string | null;
}

// ============================================================================
// Query Keys
// ============================================================================

export const invoiceKeys = {
  all: ['invoices'] as const,
  list: (customerId: string) => [...invoiceKeys.all, 'list', customerId] as const,
  detail: (customerId: string, invoiceId: string) =>
    [...invoiceKeys.all, 'detail', customerId, invoiceId] as const,
  charges: (customerId: string) => [...invoiceKeys.all, 'charges', customerId] as const,
};

// ============================================================================
// Hooks
// ============================================================================

/**
 * Hook for fetching paginated list of invoices.
 */
export function useInvoiceList(customerId: string, options: { limit?: number; offset?: number } = {}) {
  const { limit = 50, offset = 0 } = options;

  return useQuery({
    queryKey: invoiceKeys.list(customerId),
    queryFn: async () => {
      const response = await apiGet<{ invoices: Invoice[]; pagination: { limit: number; offset: number } }>(
        'l4',
        `/billing/invoices?customer_id=${encodeURIComponent(customerId)}&limit=${limit}&offset=${offset}`
      );
      return response.data;
    },
    enabled: !!customerId,
    staleTime: STALE_TIME.list,
  });
}

/**
 * Hook for fetching a single invoice with full details including items and charges.
 */
export function useInvoiceDetail(customerId: string, invoiceId: string | null) {
  return useQuery({
    queryKey: invoiceKeys.detail(customerId, invoiceId || 'null'),
    queryFn: async () => {
      if (!invoiceId) return null;
      const response = await apiGet<Invoice & { items: InvoiceItem[]; charges: Charge[] }>(
        'l4',
        `/billing/invoices/${encodeURIComponent(invoiceId)}?customer_id=${encodeURIComponent(customerId)}`
      );
      return response.data;
    },
    enabled: !!customerId && !!invoiceId,
    staleTime: STALE_TIME.detail,
  });
}

/**
 * Hook for fetching charge/payment history.
 */
export function useChargeList(customerId: string, options: { limit?: number; offset?: number } = {}) {
  const { limit = 50, offset = 0 } = options;

  return useQuery({
    queryKey: invoiceKeys.charges(customerId),
    queryFn: async () => {
      const response = await apiGet<{ charges: Charge[]; pagination: { limit: number; offset: number } }>(
        'l4',
        `/billing/charges?customer_id=${encodeURIComponent(customerId)}&limit=${limit}&offset=${offset}`
      );
      return response.data;
    },
    enabled: !!customerId,
    staleTime: STALE_TIME.list,
  });
}

/**
 * Combined hook for all invoice-related operations.
 */
export function useInvoices(customerId: string) {
  const queryClient = useQueryClient();
  const listQuery = useInvoiceList(customerId);
  const chargesQuery = useChargeList(customerId);

  // Manual fetch for invoice detail (used when clicking on invoice in list)
  const getInvoice = useCallback(
    async (invoiceId: string) => {
      const response = await apiGet<Invoice & { items: InvoiceItem[]; charges: Charge[] }>(
        'l4',
        `/billing/invoices/${encodeURIComponent(invoiceId)}?customer_id=${encodeURIComponent(customerId)}`
      );
      return response.data;
    },
    [customerId]
  );

  // Invalidate queries helper
  const invalidateInvoices = useCallback(() => {
    queryClient.invalidateQueries({
      queryKey: invoiceKeys.list(customerId),
    });
  }, [queryClient, customerId]);

  return {
    // Data
    invoices: listQuery.data?.invoices || [],
    charges: chargesQuery.data?.charges || [],
    pagination: listQuery.data?.pagination || { limit: 50, offset: 0 },

    // Loading states
    isLoading: listQuery.isLoading,
    isLoadingCharges: chargesQuery.isLoading,

    // Errors
    error: listQuery.error,
    chargesError: chargesQuery.error,

    // Actions
    getInvoice,
    invalidateInvoices,

    // Refetch
    refetch: () => {
      listQuery.refetch();
      chargesQuery.refetch();
    },
  };
}
