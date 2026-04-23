import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { DataTable, PageHeader } from '@/components/ui/fabric';
import { InvoiceStatusBadge } from '@/components/billing/InvoiceStatusBadge';
import { InvoiceDetailDrawer } from '@/components/billing/InvoiceDetailDrawer';
import { useInvoiceList, useInvoiceDetail, type Invoice } from '@/hooks/useInvoices';
import { useBillingContext } from '@/context/BillingContext';
import { formatDate, formatCurrency } from '@/lib/formatters';
import { Eye, FileText } from 'lucide-react';
import type { ColumnDef } from '@tanstack/react-table';

export function InvoiceList() {
  const { subscription } = useBillingContext();
  const customerId = subscription?.id || '';
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  const { data, isLoading, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInvoiceList(customerId);

  const { data: invoiceDetail } = useInvoiceDetail(selectedInvoice?.id || '');

  const invoices = data?.pages.flatMap((page) => page.invoices) || [];

  const columns: ColumnDef<Invoice>[] = [
    {
      accessorKey: 'invoice_number',
      header: 'Invoice #',
      cell: ({ row }) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{row.original.invoice_number}</span>
        </div>
      ),
    },
    {
      accessorKey: 'status',
      header: 'Status',
      cell: ({ row }) => <InvoiceStatusBadge status={row.original.status} />,
    },
    {
      accessorKey: 'period',
      header: 'Period',
      cell: ({ row }) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(row.original.period_start)} - {formatDate(row.original.period_end)}
        </span>
      ),
    },
    {
      accessorKey: 'total_dollars',
      header: 'Amount',
      cell: ({ row }) => (
        <span className="font-medium">{formatCurrency(row.original.total_dollars)}</span>
      ),
    },
    {
      accessorKey: 'amount_due_dollars',
      header: 'Balance',
      cell: ({ row }) => {
        const due = row.original.amount_due_dollars;
        if (due <= 0) {
          return <span className="text-green-600 font-medium">Paid</span>;
        }
        return (
          <span className="text-amber-600 font-medium">
            {formatCurrency(due)} due
          </span>
        );
      },
    },
    {
      accessorKey: 'due_date',
      header: 'Due Date',
      cell: ({ row }) => formatDate(row.original.due_date),
    },
    {
      id: 'actions',
      cell: ({ row }) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSelectedInvoice(row.original)}
        >
          <Eye className="h-4 w-4 mr-1" />
          View
        </Button>
      ),
    },
  ];

  return (
    <div className="container mx-auto p-6 max-w-7xl">
      <PageHeader
        title="Invoices"
        subtitle="View and manage your billing invoices"
      />

      <Card>
        <CardHeader>
          <CardTitle>All Invoices</CardTitle>
          <CardDescription>
            {invoices.length} invoice{invoices.length !== 1 ? 's' : ''} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : invoices.length === 0 ? (
            <div className="text-center py-12">
              <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No invoices yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Invoices will appear here once generated
              </p>
            </div>
          ) : (
            <>
              <DataTable columns={columns} data={invoices} />
              {hasNextPage && (
                <div className="flex justify-center mt-4">
                  <Button
                    variant="outline"
                    onClick={() => fetchNextPage()}
                    disabled={isFetchingNextPage}
                  >
                    {isFetchingNextPage ? 'Loading...' : 'Load More'}
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <InvoiceDetailDrawer
        invoice={invoiceDetail || selectedInvoice}
        onClose={() => setSelectedInvoice(null)}
      />
    </div>
  );
}
