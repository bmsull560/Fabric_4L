import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { cn } from '@/lib/utils';
import { Activity, AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';

interface UsageMetricCardProps {
  metric: string;
  current: number;
  limit: number;
  unit: string;
  warningThreshold?: number;
}

export function UsageMetricCard({
  metric,
  current,
  limit,
  unit,
  warningThreshold = 75,
}: UsageMetricCardProps) {
  const percentage = limit > 0 ? Math.min((current / limit) * 100, 100) : 0;
  const isWarning = percentage >= warningThreshold && percentage < 90;
  const isDanger = percentage >= 90;
  const isSafe = percentage < warningThreshold;

  const StatusIcon = isDanger ? AlertTriangle : isWarning ? AlertCircle : CheckCircle;
  const statusColor = isDanger ? 'text-red-600' : isWarning ? 'text-yellow-600' : 'text-green-600';
  const progressColor = isDanger
    ? 'bg-red-500'
    : isWarning
      ? 'bg-yellow-500'
      : 'bg-green-500';

  // Format metric name for display (e.g., "api_calls" -> "API Calls")
  const formatMetricName = (name: string): string => {
    return name
      .split('_')
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  return (
    <Card className={cn('transition-all', isDanger && 'border-red-200 bg-red-50/50')}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Activity className="h-4 w-4 text-muted-foreground" />
            {formatMetricName(metric)}
          </CardTitle>
          <StatusIcon className={cn('h-4 w-4', statusColor)} />
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-bold">
              {current.toLocaleString()}
              <span className="text-sm font-normal text-muted-foreground ml-1">{unit}</span>
            </span>
            <span className="text-sm text-muted-foreground">
              of {limit.toLocaleString()} {unit}
            </span>
          </div>

          <div className="relative">
            <Progress value={percentage} className="h-2" />
            <div
              className={cn('absolute top-0 h-2 rounded-full transition-all', progressColor)}
              style={{ width: `${percentage}%` }}
            />
          </div>

          <div className="flex items-center justify-between text-xs">
            <span className={cn('font-medium', statusColor)}>{percentage.toFixed(1)}% used</span>
            {isDanger && <span className="text-red-600 font-medium">Overage imminent</span>}
            {isWarning && <span className="text-yellow-600">Approaching limit</span>}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
