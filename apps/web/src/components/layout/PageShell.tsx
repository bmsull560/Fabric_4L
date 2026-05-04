/**
 * PageShell Component
 * Shared layout wrapper for page content with consistent padding and max-width.
 */

import { cn } from "@/lib/utils";

export interface PageShellProps {
  children: React.ReactNode;
  className?: string;
  fullWidth?: boolean;
}

/**
 * Page content wrapper providing consistent layout.
 *
 * @param fullWidth - If true, uses full viewport width; otherwise max-w-7xl
 */
export function PageShell({ children, className, fullWidth }: PageShellProps) {
  return (
    <div className={cn("mx-auto px-6 py-6", fullWidth ? "w-full" : "max-w-7xl", className)}>
      {children}
    </div>
  );
}
