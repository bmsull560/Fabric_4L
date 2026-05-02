/**
 * StatusBadge Component
 *
 * Status indicator used in Setup, Operations, and workflow steps.
 */

import { cn } from '@/lib/utils';

export type StatusVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'active';

interface StatusBadgeProps {
  status: StatusVariant;
  label?: string;
  size?: 'sm' | 'md';
  className?: string;
  pulse?: boolean;
}

const variantConfig: Record<StatusVariant, { bg: string; text: string; dot: string }> = {
  default: {
    bg: 'bg-muted',
    text: 'text-muted-foreground',
    dot: 'bg-muted-foreground',
  },
  success: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-500',
    dot: 'bg-emerald-500',
  },
  warning: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-500',
    dot: 'bg-amber-500',
  },
  error: {
    bg: 'bg-destructive/10',
    text: 'text-destructive',
    dot: 'bg-destructive',
  },
  info: {
    bg: 'bg-blue-500/10',
    text: 'text-blue-500',
    dot: 'bg-blue-500',
  },
  active: {
    bg: 'bg-primary/10',
    text: 'text-primary',
    dot: 'bg-primary',
  },
};

const defaultLabels: Record<StatusVariant, string> = {
  default: 'Pending',
  success: 'Complete',
  warning: 'Warning',
  error: 'Error',
  info: 'Info',
  active: 'Active',
};

export function StatusBadge({
  status,
  label,
  size = 'md',
  className,
  pulse = false,
}: StatusBadgeProps) {
  const config = variantConfig[status];
  const displayLabel = label || defaultLabels[status];

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full font-medium',
        config.bg,
        config.text,
        size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs',
        className
      )}
    >
      <span
        className={cn(
          'rounded-full',
          config.dot,
          size === 'sm' ? 'w-1.5 h-1.5' : 'w-2 h-2',
          pulse && 'animate-pulse'
        )}
      />
      {displayLabel}
    </span>
  );
}
