import { Badge, type BadgeProps } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { CheckCircle, Clock, XCircle } from 'lucide-react';

type ChargeStatus = 'succeeded' | 'pending' | 'failed';

interface ChargeStatusBadgeProps extends Omit<BadgeProps, 'children'> {
  status: ChargeStatus | string;
  showIcon?: boolean;
}

const statusConfig: Record<
  ChargeStatus,
  { label: string; variant: BadgeProps['variant']; className: string; icon: typeof CheckCircle }
> = {
  succeeded: {
    label: 'Succeeded',
    variant: 'default',
    className: 'bg-green-100 text-green-800 hover:bg-green-100 border-green-200',
    icon: CheckCircle,
  },
  pending: {
    label: 'Pending',
    variant: 'default',
    className: 'bg-yellow-100 text-yellow-800 hover:bg-yellow-100 border-yellow-200',
    icon: Clock,
  },
  failed: {
    label: 'Failed',
    variant: 'destructive',
    className: 'bg-red-100 text-red-800 hover:bg-red-100 border-red-200',
    icon: XCircle,
  },
};

export function ChargeStatusBadge({ status, showIcon = true, className, ...props }: ChargeStatusBadgeProps) {
  const config = statusConfig[status as ChargeStatus] || {
    label: status,
    variant: 'secondary',
    className: '',
    icon: Clock,
  };

  const Icon = config.icon;

  return (
    <Badge variant={config.variant} className={cn(config.className, className)} {...props}>
      {showIcon && <Icon className="mr-1 h-3 w-3" />}
      {config.label}
    </Badge>
  );
}
