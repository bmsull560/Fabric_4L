import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { PageHeader } from '@/components/ui/fabric';
import { ChargeStatusBadge } from '@/components/billing/ChargeStatusBadge';
import { useChargeList } from '@/hooks/useInvoices';
import { useBillingContext } from '@/context/BillingContext';
import { formatDate, formatCurrency, formatRelativeTime } from '@/lib/formatters';
import { CreditCard, Download, RefreshCw, Receipt } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

// Payment method icons mapping
const PaymentMethodIcon = ({ type }: { type: string | null }) => {
  const iconMap: Record<string, string> = {
    card: '💳',
    bank_transfer: '🏦',
    paypal: '🅿️',
    apple_pay: '🍎',
    google_pay: 'G',
  };
  return <span className="text-lg">{iconMap[type || 'card'] || '💳'}</span>;
};

export function PaymentHistory() {
  const { customerId } = useBillingContext();

  const { data, isLoading, refetch } = useChargeList(customerId);
  const charges = data?.charges || [];

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <PageHeader
        title="Payment History"
        subtitle="View your payment transactions and receipts"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Transactions</CardTitle>
          <CardDescription>
            {charges.length} transaction{charges.length !== 1 ? 's' : ''} found
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : charges.length === 0 ? (
            <div className="text-center py-12">
              <Receipt className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">No payment history yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Payments will appear here once processed
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Receipt</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {charges.map((charge) => (
                  <TableRow key={charge.id}>
                    <TableCell>
                      <div className="space-y-0.5">
                        <p className="font-medium">{formatDate(charge.created_at)}</p>
                        <p className="text-xs text-muted-foreground">
                          {formatRelativeTime(charge.created_at)}
                        </p>
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="space-y-0.5">
                        <p className="font-medium">{charge.description || 'Payment'}</p>
                        {charge.invoice_number && (
                          <p className="text-xs text-muted-foreground">
                            Invoice {charge.invoice_number}
                          </p>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <PaymentMethodIcon type={charge.payment_method_type} />
                        <span className="capitalize text-sm">
                          {charge.payment_method_type?.replace(/_/g, ' ') || 'Card'}
                        </span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <ChargeStatusBadge status={charge.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <span
                        className={`font-medium ${
                          charge.status === 'succeeded'
                            ? 'text-green-600'
                            : charge.status === 'failed'
                            ? 'text-red-600'
                            : ''
                        }`}
                      >
                        {formatCurrency(charge.amount_dollars)}
                      </span>
                    </TableCell>
                    <TableCell className="text-right">
                      {charge.receipt_url ? (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => window.open(charge.receipt_url!, '_blank')}
                        >
                          <Download className="h-4 w-4 mr-1" />
                          Receipt
                        </Button>
                      ) : (
                        <span className="text-muted-foreground text-sm">—</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Summary Card */}
      {charges.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3 mt-6">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <CreditCard className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">Total Spent</span>
              </div>
              <p className="text-2xl font-bold mt-2">
                {formatCurrency(
                  charges
                    .filter((c) => c.status === 'succeeded')
                    .reduce((sum, c) => sum + c.amount_dollars, 0)
                )}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Badge variant="default" className="h-4 w-4 p-0" />
                <span className="text-sm text-muted-foreground">Successful</span>
              </div>
              <p className="text-2xl font-bold mt-2">
                {charges.filter((c) => c.status === 'succeeded').length}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2">
                <Badge variant="destructive" className="h-4 w-4 p-0" />
                <span className="text-sm text-muted-foreground">Failed</span>
              </div>
              <p className="text-2xl font-bold mt-2">
                {charges.filter((c) => c.status === 'failed').length}
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
