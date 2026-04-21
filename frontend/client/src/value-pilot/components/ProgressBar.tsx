/**
 * ProgressBar Component
 *
 * Progress indicator used in AI Model, Calculator, and Operations steps.
 */

import { cn } from '@/lib/utils';
import { Progress } from '@/components/ui/progress';

interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  size?: 'sm' | 'md';
  variant?: 'default' | 'success' | 'gradient';
  className?: string;
  animated?: boolean;
}

export function ProgressBar({
  value,
  max = 100,
  label,
  showPercentage = true,
  size = 'md',
  variant = 'default',
  className,
  animated = false,
}: ProgressBarProps) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn('w-full', className)}>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <span
              className={cn(
                'text-muted-foreground',
                size === 'sm' ? 'text-[10px]' : 'text-xs'
              )}
            >
              {label}
            </span>
          )}
          {showPercentage && (
            <span
              className={cn(
                'font-medium text-foreground tabular-nums',
                size === 'sm' ? 'text-[10px]' : 'text-xs'
              )}
            >
              {Math.round(percentage)}%
            </span>
          )}
        </div>
      )}
      <Progress
        value={percentage}
        className={cn(
          size === 'sm' ? 'h-1.5' : 'h-2',
          variant === 'gradient' && '[&>div]:bg-gradient-to-r [&>div]:from-primary [&>div]:to-emerald-500'
        )}
      />
      {animated && percentage < 100 && (
        <div className="mt-1 flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
          <span className="text-[10px] text-muted-foreground">Processing...</span>
        </div>
      )}
    </div>
  );
}
