import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { DataTable, PageHeader } from '@/components/ui/fabric';
import { InvoiceStatusBadge } from '@/components/billing/InvoiceStatusBadge';
import { InvoiceDetailDrawer } from '@/components/billing/InvoiceDetailDrawer';
import { useInvoiceList, useInvoiceDetail, type Invoice } from '@/hooks/useInvoices';
import { useBillingContext } from '@/context/BillingContext';
import type { DataTableColumn } from '@/components/ui/fabric/DataTable';
import { formatDate, formatCurrency } from '@/lib/formatters';
import { Eye, FileText } from 'lucide-react';

export function InvoiceList() {
  const { customerId } = useBillingContext();
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);

  const { data, isLoading } = useInvoiceList(customerId);

  const { data: invoiceDetail } = useInvoiceDetail(customerId, selectedInvoice?.id || null);

  const invoices = data?.invoices || [];

  const columns: DataTableColumn<Invoice>[] = [
    {
      key: 'invoice_number',
      header: 'Invoice #',
      render: (invoice: Invoice) => (
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-muted-foreground" />
          <span className="font-medium">{invoice.invoice_number}</span>
        </div>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      render: (invoice: Invoice) => <InvoiceStatusBadge status={invoice.status} />,
    },
    {
      key: 'period',
      header: 'Period',
      render: (invoice: Invoice) => (
        <span className="text-sm text-muted-foreground">
          {formatDate(invoice.period_start)} - {formatDate(invoice.period_end)}
        </span>
      ),
    },
    {
      key: 'total_dollars',
      header: 'Amount',
      render: (invoice: Invoice) => (
        <span className="font-medium">{formatCurrency(invoice.total_dollars)}</span>
      ),
    },
    {
      key: 'amount_due_dollars',
      header: 'Balance',
      render: (invoice: Invoice) => {
        const due = invoice.amount_due_dollars;
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
      key: 'due_date',
      header: 'Due Date',
      render: (invoice: Invoice) => formatDate(invoice.due_date),
    },
    {
      key: 'actions',
      header: 'Actions',
      render: (invoice: Invoice) => (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setSelectedInvoice(invoice)}
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
              <DataTable
                columns={columns}
                data={invoices}
                keyExtractor={(invoice) => invoice.id}
              />
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
