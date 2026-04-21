/**
 * StatCard Component
 *
 * Icon + label + value + sublabel pattern used across Value Pilot steps.
 */

import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface StatCardProps {
  icon: ReactNode;
  label: string;
  value: string;
  sublabel?: string;
  variant?: 'default' | 'success' | 'warning' | 'error';
  className?: string;
  size?: 'sm' | 'md';
}

export function StatCard({
  icon,
  label,
  value,
  sublabel,
  variant = 'default',
  className,
  size = 'md',
}: StatCardProps) {
  const variantStyles = {
    default: 'bg-muted/50 border-border',
    success: 'bg-emerald-500/10 border-emerald-500/20',
    warning: 'bg-amber-500/10 border-amber-500/20',
    error: 'bg-destructive/10 border-destructive/20',
  };

  const iconColors = {
    default: 'text-muted-foreground',
    success: 'text-emerald-500',
    warning: 'text-amber-500',
    error: 'text-destructive',
  };

  return (
    <div
      className={cn(
        'rounded-xl border p-3 transition-all',
        variantStyles[variant],
        size === 'sm' ? 'p-2' : 'p-3',
        className
      )}
    >
      <div className="flex items-start gap-3">
        <div className={cn('shrink-0 mt-0.5', iconColors[variant])}>{icon}</div>
        <div className="min-w-0 flex-1">
          <p className={cn('text-xs text-muted-foreground', size === 'sm' && 'text-[10px]')}>
            {label}
          </p>
          <p
            className={cn(
              'font-semibold text-foreground truncate',
              size === 'sm' ? 'text-sm' : 'text-base'
            )}
          >
            {value}
          </p>
          {sublabel && (
            <p className={cn('text-[10px] text-muted-foreground/70', size === 'sm' && 'text-[9px]')}>
              {sublabel}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
