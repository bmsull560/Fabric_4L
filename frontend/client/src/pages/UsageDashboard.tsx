import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { PageHeader } from '@/components/ui/fabric';
import { UsageMetricCard } from '@/components/billing/UsageMetricCard';
import { useUsage } from '@/hooks/useUsage';
import { useBillingContext } from '@/context/BillingContext';
import { formatDate, formatRelativeTime } from '@/lib/formatters';
import { AlertTriangle, RefreshCw, Activity } from 'lucide-react';

export function UsageDashboard() {
  const { customerId } = useBillingContext();

  const { metrics, events, isLoading, isLoadingEvents, refetch } = useUsage(customerId);

  const [showAllEvents, setShowAllEvents] = useState(false);
  const displayedEvents = showAllEvents ? events : events.slice(0, 10);

  // Check if any metric is over warning threshold
  const warningMetrics = metrics.filter((m) => m.percentage >= 75 && m.percentage < 90);
  const dangerMetrics = metrics.filter((m) => m.percentage >= 90);

  return (
    <div className="container mx-auto p-6 max-w-6xl">
      <PageHeader
        title="Usage & Limits"
        subtitle="Monitor your platform usage and plan limits"
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isLoading}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        }
      />

      {/* Overage Alerts */}
      {dangerMetrics.length > 0 && (
        <Alert variant="destructive" className="mb-6">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>Usage Limit Approaching</AlertTitle>
          <AlertDescription>
            {dangerMetrics.map((m) => m.metric).join(', ')} are at {Math.round(dangerMetrics[0].percentage)}% of your plan limit. Overage charges may apply.
          </AlertDescription>
        </Alert>
      )}

      {warningMetrics.length > 0 && dangerMetrics.length === 0 && (
        <Alert className="mb-6 border-yellow-200 bg-yellow-50">
          <AlertTriangle className="h-4 w-4 text-yellow-600" />
          <AlertTitle className="text-yellow-800">Approaching Limit</AlertTitle>
          <AlertDescription className="text-yellow-700">
            {warningMetrics.map((m) => m.metric).join(', ')} are approaching your plan limits.
          </AlertDescription>
        </Alert>
      )}

      {/* Usage Metric Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mb-8">
        {isLoading ? (
          <>
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
          </>
        ) : metrics.length === 0 ? (
          <Card className="col-span-full">
            <CardContent className="flex flex-col items-center justify-center py-12 text-center">
              <Activity className="h-12 w-12 text-muted-foreground mb-4" />
              <p className="text-muted-foreground">No usage data available yet.</p>
              <p className="text-sm text-muted-foreground mt-1">
                Usage will appear as you use platform features.
              </p>
            </CardContent>
          </Card>
        ) : (
          metrics.map((metric) => (
            <UsageMetricCard
              key={metric.metric}
              metric={metric.metric}
              current={metric.total_quantity}
              limit={metric.limit}
              unit={metric.unit}
              warningThreshold={metric.warning_threshold}
            />
          ))
        )}
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Last 30 days of usage events</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoadingEvents ? (
            <div className="space-y-2">
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
              <Skeleton className="h-10 w-full" />
            </div>
          ) : events.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p>No usage events recorded yet.</p>
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Event</TableHead>
                    <TableHead>Metric</TableHead>
                    <TableHead className="text-right">Quantity</TableHead>
                    <TableHead className="text-right">When</TableHead>
                    <TableHead>Status</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {displayedEvents.map((event) => (
                    <TableRow key={event.id}>
                      <TableCell className="font-medium">{event.event_name}</TableCell>
                      <TableCell className="capitalize">
                        {event.metric_name.replace(/_/g, ' ')}
                      </TableCell>
                      <TableCell className="text-right">
                        {event.quantity.toLocaleString()}
                      </TableCell>
                      <TableCell className="text-right text-muted-foreground">
                        {formatRelativeTime(event.timestamp)}
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant={event.status === 'processed' ? 'default' : 'secondary'}
                          className="text-xs"
                        >
                          {event.status}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {events.length > 10 && (
                <div className="flex justify-center mt-4">
                  <Button variant="outline" onClick={() => setShowAllEvents(!showAllEvents)}>
                    {showAllEvents ? 'Show Less' : `Show All ${events.length} Events`}
                  </Button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Period Info */}
      {metrics.length > 0 && (
        <p className="text-sm text-muted-foreground mt-4 text-center">
          Current billing period: {formatDate(metrics[0]?.period_start)} -{' '}
          {formatDate(metrics[0]?.period_end)}
        </p>
      )}
    </div>
  );
}
