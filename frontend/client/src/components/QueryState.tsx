/**
 * QueryState — Shared loading, error, and empty-state renderer
 *
 * Eliminates 30+ repeated inline loading spinners and error banners scattered
 * across page components. Every page that calls a React Query hook can delegate
 * its loading/error/empty rendering to this single component.
 *
 * Usage:
 *   const { data, isLoading, error } = useFormulas();
 *
 *   return (
 *     <QueryState isLoading={isLoading} error={error} isEmpty={!data?.length}
 *                 emptyMessage="No formulas found.">
 *       <FormulaList items={data!} />
 *     </QueryState>
 *   );
 */

import { ReactNode } from "react";
import { Loader2, AlertCircle, Inbox } from "lucide-react";
import { cn } from "@/lib/utils";

// ── Props ─────────────────────────────────────────────────────────────────────
interface QueryStateProps {
  /** Whether the query is currently fetching */
  isLoading: boolean;
  /** Error object from React Query (or null/undefined) */
  error?: Error | null | unknown;
  /** When true, renders the empty-state slot instead of children */
  isEmpty?: boolean;
  /** Message shown in the empty state */
  emptyMessage?: string;
  /** Optional sub-message shown below the empty-state label */
  emptySubMessage?: string;
  /** Content to render when data is available */
  children: ReactNode;
  /** Override the loading message (default: "Loading…") */
  loadingMessage?: string;
  /** Extra className applied to the wrapper div */
  className?: string;
  /** Render as a full-page centred block (default: false — inline block) */
  fullPage?: boolean;
}

// ── Component ─────────────────────────────────────────────────────────────────
export function QueryState({
  isLoading,
  error,
  isEmpty = false,
  emptyMessage = "No items found.",
  emptySubMessage,
  children,
  loadingMessage = "Loading…",
  className,
  fullPage = false,
}: QueryStateProps) {
  const wrapperClass = cn(
    "flex flex-col items-center justify-center gap-3 text-neutral-500",
    fullPage ? "min-h-[60vh]" : "py-16",
    className
  );

  if (isLoading) {
    return (
      <div className={wrapperClass}>
        <Loader2 size={24} className="animate-spin text-neutral-400" />
        <span className="text-sm">{loadingMessage}</span>
      </div>
    );
  }

  if (error) {
    const message =
      error instanceof Error
        ? error.message
        : typeof error === "string"
        ? error
        : "An unexpected error occurred. Please try again.";

    return (
      <div className={wrapperClass}>
        <AlertCircle size={24} className="text-red-500" />
        <span className="text-sm text-red-600 text-center max-w-sm">{message}</span>
      </div>
    );
  }

  if (isEmpty) {
    return (
      <div className={wrapperClass}>
        <Inbox size={24} className="text-neutral-300" />
        <span className="text-sm">{emptyMessage}</span>
        {emptySubMessage && (
          <span className="text-xs text-neutral-400 text-center max-w-sm">
            {emptySubMessage}
          </span>
        )}
      </div>
    );
  }

  return <>{children}</>;
}

export default QueryState;
