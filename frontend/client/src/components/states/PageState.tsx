/**
 * PageState — Route-level query state wrapper
 *
 * Combines LoadingState, EmptyState, and ErrorState into a single
 * component for route-level data fetching patterns.
 */
import { ReactNode } from "react";
import { LucideIcon } from "lucide-react";
import { LoadingState } from "./LoadingState";
import { EmptyState } from "./EmptyState";
import { ErrorState } from "./ErrorState";

interface PageStateProps<T> {
  isLoading: boolean;
  isError: boolean;
  error?: Error | unknown;
  data?: T;
  isEmpty?: (data: T) => boolean;
  loadingMessage?: string;
  emptyTitle: string;
  emptyDescription?: string;
  emptyIcon?: LucideIcon;
  emptyAction?: ReactNode;
  errorTitle: string;
  errorDescription?: string;
  onRetry?: () => void;
  retryLabel?: string;
  errorFallbackAction?: ReactNode;
  children: ReactNode;
}

export function PageState<T>({
  isLoading,
  isError,
  error,
  data,
  isEmpty,
  loadingMessage,
  emptyTitle,
  emptyDescription,
  emptyIcon,
  emptyAction,
  errorTitle,
  errorDescription,
  onRetry,
  retryLabel,
  errorFallbackAction,
  children,
}: PageStateProps<T>) {
  if (isLoading) {
    return <LoadingState message={loadingMessage} />;
  }

  if (isError) {
    return (
      <ErrorState
        title={errorTitle}
        description={errorDescription}
        error={error}
        onRetry={onRetry}
        retryLabel={retryLabel}
        fallbackAction={errorFallbackAction}
      />
    );
  }

  const hasData = data !== undefined && data !== null;
  const emptyCheck = isEmpty
    ? hasData ? isEmpty(data) : true
    : !hasData || (Array.isArray(data) && data.length === 0);
  
  if (emptyCheck) {
    return (
      <EmptyState
        title={emptyTitle}
        description={emptyDescription}
        icon={emptyIcon}
        action={emptyAction}
      />
    );
  }

  return <>{children}</>;
}

export default PageState;
