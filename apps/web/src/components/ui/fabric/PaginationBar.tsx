import * as React from "react";
import {
  ChevronLeftIcon,
  ChevronRightIcon,
  MoreHorizontalIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

export interface PaginationBarProps {
  /** Current page number (1-based) */
  page: number;
  /** Number of items per page */
  pageSize?: number;
  /** Total number of items (required for range variant) */
  totalItems?: number;
  /** Total number of pages (required for page variant) */
  totalPages?: number;
  /** Whether previous page is available */
  canPrevious?: boolean;
  /** Whether next page is available */
  canNext?: boolean;
  /** Callback when previous page is clicked */
  onPrevious?: () => void;
  /** Callback when next page is clicked */
  onNext?: () => void;
  /** Callback when a specific page is clicked */
  onPageChange?: (page: number) => void;
  /** Label for items (e.g., "accounts", "jobs") */
  itemLabel?: string;
  /** Summary display variant */
  summaryVariant?: "range" | "page";
  /** Additional class names */
  className?: string;
}

/**
 * PaginationBar - Standardized pagination wrapper around shadcn pagination
 * 
 * Provides consistent pagination UI across the application with two summary variants:
 * - "range": "Showing 1–25 of 143 accounts" (default for entity lists)
 * - "page": "Page 2 of 8" (for compact operational/admin tables)
 */
export function PaginationBar({
  page,
  pageSize = 20,
  totalItems,
  totalPages,
  canPrevious = true,
  canNext = true,
  onPrevious,
  onNext,
  onPageChange,
  itemLabel = "items",
  summaryVariant = "range",
  className,
}: PaginationBarProps) {
  // Calculate derived values
  const calculatedTotalPages = totalPages || (totalItems ? Math.ceil(totalItems / pageSize) : 1);
  const startIndex = (page - 1) * pageSize + 1;
  const endIndex = Math.min(page * pageSize, totalItems || 0);

  // Render summary text based on variant
  const renderSummary = () => {
    if (summaryVariant === "page") {
      return (
        <span className="text-[12px] text-muted-foreground">
          Page {page} of {calculatedTotalPages}
        </span>
      );
    }

    // range variant
    if (totalItems) {
      return (
        <span className="text-[12px] text-muted-foreground">
          Showing {startIndex}–{endIndex} of {totalItems} {itemLabel}
        </span>
      );
    }

    return null;
  };

  // Generate page numbers for display (show current, first, last, and neighbors)
  const generatePageNumbers = () => {
    const pages: (number | string)[] = [];
    const maxVisible = 5;

    if (calculatedTotalPages <= maxVisible) {
      return Array.from({ length: calculatedTotalPages }, (_, i) => i + 1);
    }

    pages.push(1);

    if (page > 3) {
      pages.push("...");
    }

    const start = Math.max(2, page - 1);
    const end = Math.min(calculatedTotalPages - 1, page + 1);

    for (let i = start; i <= end; i++) {
      pages.push(i);
    }

    if (page < calculatedTotalPages - 2) {
      pages.push("...");
    }

    pages.push(calculatedTotalPages);

    return pages;
  };

  const pageNumbers = generatePageNumbers();

  return (
    <div className={cn("flex items-center justify-between px-4 py-3 border-t border-border", className)}>
      {/* Summary */}
      {renderSummary()}

      {/* Pagination Controls */}
      <Pagination className="w-auto">
        <PaginationContent className="flex items-center gap-1">
          <PaginationItem>
            <button
              onClick={onPrevious}
              disabled={!canPrevious}
              className={cn(
                "inline-flex items-center gap-1 h-8 px-2.5 rounded-md text-sm font-medium transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                !canPrevious && "opacity-50 cursor-not-allowed pointer-events-none"
              )}
              aria-label="Go to previous page"
            >
              <ChevronLeftIcon size={14} />
              <span className="hidden sm:inline">Previous</span>
            </button>
          </PaginationItem>

          {pageNumbers.map((p, index) => (
            <React.Fragment key={index}>
              {p === "..." ? (
                <PaginationItem>
                  <PaginationEllipsis>
                    <MoreHorizontalIcon size={14} />
                  </PaginationEllipsis>
                </PaginationItem>
              ) : (
                <PaginationItem>
                  <PaginationLink
                    isActive={p === page}
                    onClick={() => onPageChange?.(p as number)}
                    className="h-8 w-8"
                  >
                    {p}
                  </PaginationLink>
                </PaginationItem>
              )}
            </React.Fragment>
          ))}

          <PaginationItem>
            <button
              onClick={onNext}
              disabled={!canNext}
              className={cn(
                "inline-flex items-center gap-1 h-8 px-2.5 rounded-md text-sm font-medium transition-colors",
                "hover:bg-accent hover:text-accent-foreground",
                "focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
                !canNext && "opacity-50 cursor-not-allowed pointer-events-none"
              )}
              aria-label="Go to next page"
            >
              <span className="hidden sm:inline">Next</span>
              <ChevronRightIcon size={14} />
            </button>
          </PaginationItem>
        </PaginationContent>
      </Pagination>
    </div>
  );
}
