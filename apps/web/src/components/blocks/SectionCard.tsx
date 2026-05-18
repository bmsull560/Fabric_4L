/**
 * SectionCard — Consistent card wrapper with header for workflow steps.
 *
 * UI Contract (Data):
 *   - `title` : optional section title
 *   - `description` : optional subtitle (also accepts `subtitle` as alias)
 *   - `icon` : optional icon element
 *   - `action` : optional action button or element
 *   - `noPad` : when true, removes default content padding (for flush-edge content)
 *   - `children` : card content
 *
 * UI Contract (Rendering):
 *   - Rounded card with border
 *   - Header with title/description/icon/action
 *   - Content area below header
 *
 * Consolidated from: value-pilot/components/SectionCard.tsx
 * Extended: added `subtitle` alias and `noPad` prop (migrated from WfPrimitives shim)
 */
import { cn } from "@/lib/utils";
import type { ReactNode } from 'react';

export interface SectionCardProps {
  title?: string;
  /** Subtitle text shown below the title. Alias: `subtitle`. */
  description?: string;
  /** Alias for `description` — accepted for backward compatibility. */
  subtitle?: string;
  icon?: ReactNode;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  contentClassName?: string;
  headerClassName?: string;
  /** When true, removes default padding from the content area. */
  noPad?: boolean;
}

export function SectionCard({
  title,
  description,
  subtitle,
  icon,
  action,
  children,
  className,
  contentClassName,
  headerClassName,
  noPad,
}: SectionCardProps) {
  const resolvedDescription = description ?? subtitle;
  return (
    <section
      className={cn(
        'bg-card rounded-xl border border-border overflow-hidden',
        className
      )}
    >
      {(title || action) && (
        <div
          className={cn(
            'px-5 py-3 border-b border-border/60 flex items-center justify-between',
            headerClassName
          )}
        >
          <div className="flex items-center gap-2">
            {icon && <span className="text-muted-foreground">{icon}</span>}
            <div>
              {title && (
                <h3 className="text-sm font-semibold text-foreground">{title}</h3>
              )}
              {resolvedDescription && (
                <p className="text-xs text-muted-foreground mt-0.5">{resolvedDescription}</p>
              )}
            </div>
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className={cn(!noPad && "p-4", contentClassName)}>{children}</div>
    </section>
  );
}
