import { cn } from '@/lib/utils';
import type { ReactNode } from 'react';

interface StepCardProps {
  title?: string;
  description?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function StepCard({ title, description, icon, children, className }: StepCardProps) {
  return (
    <section className={cn('bg-card rounded-xl border border-border overflow-hidden', className)}>
      {(title || description) && (
        <div className="px-5 py-3 border-b border-border/60">
          <div className="flex items-center gap-2">
            {icon && <span className="text-muted-foreground">{icon}</span>}
            <div>
              {title && <h3 className="text-sm font-semibold text-foreground">{title}</h3>}
              {description && <p className="text-xs text-muted-foreground mt-0.5">{description}</p>}
            </div>
          </div>
        </div>
      )}
      <div className="p-6">{children}</div>
    </section>
  );
}
