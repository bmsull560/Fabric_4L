/**
 * @deprecated Use Skeleton from "@/components/ui/skeleton" (primitive) or
 * SkeletonViews from "@/components/ui/SkeletonViews" (page-level skeletons).
 * This component is maintained for backward compatibility only.
 */
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export interface LoadingSkeletonProps {
  variant?: "card" | "table" | "metric" | "form" | "page";
  count?: number;
  className?: string;
}

export function LoadingSkeleton({ variant = "card", count = 1, className }: LoadingSkeletonProps) {
  if (variant === "metric") {
    return (
      <div className={cn("p-6 rounded-lg border border-border bg-card shadow-sm", className)}>
        <Skeleton className="h-3 w-24 mb-3" />
        <Skeleton className="h-8 w-32 mb-2" />
        <Skeleton className="h-3 w-20" />
      </div>
    );
  }

  if (variant === "table") {
    return (
      <div className={cn("rounded-lg border border-border overflow-hidden", className)}>
        <div className="h-10 bg-muted/50 px-4 flex items-center gap-4">
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-32" />
          <Skeleton className="h-3 w-20" />
        </div>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-12 border-t border-border px-4 flex items-center gap-4">
            <Skeleton className="h-3 w-28" />
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-3 w-16" />
          </div>
        ))}
      </div>
    );
  }

  if (variant === "form") {
    return (
      <div className={cn("space-y-4 p-6", className)}>
        <div className="space-y-2">
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-9 w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="h-9 w-full" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-3 w-14" />
          <Skeleton className="h-20 w-full" />
        </div>
      </div>
    );
  }

  if (variant === "page") {
    return (
      <div className={cn("space-y-6 p-6", className)}>
        <div className="space-y-2 pb-6 border-b border-border">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-4 w-64" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <LoadingSkeleton variant="metric" />
          <LoadingSkeleton variant="metric" />
          <LoadingSkeleton variant="metric" />
        </div>
        <LoadingSkeleton variant="card" />
      </div>
    );
  }

  // Default card
  return (
    <div className={cn("p-6 rounded-lg border border-border bg-card shadow-sm space-y-3", className)}>
      <Skeleton className="h-4 w-3/4" />
      <Skeleton className="h-3 w-full" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}
