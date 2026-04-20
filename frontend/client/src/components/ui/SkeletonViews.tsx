/**
 * SkeletonViews — Apple-Quality Loading States
 *
 * Provides shimmer-style skeleton screens for all major content patterns.
 * Follows Apple's Human Interface Guidelines for loading states.
 */

import { cn } from '@/lib/utils';
import { Card, CardContent, CardHeader } from './card';

/**
 * Base shimmer animation class
 */
const shimmerClass = 'animate-pulse bg-muted rounded';

/**
 * Skeleton line - single text line placeholder
 */
export function SkeletonLine({
  width = '100%',
  height = '1em',
  className,
}: {
  width?: string;
  height?: string;
  className?: string;
}) {
  return (
    <div
      className={cn(shimmerClass, className)}
      style={{ width, height }}
    />
  );
}

/**
 * Skeleton text block - multiple lines
 */
export function SkeletonText({
  lines = 3,
  lineHeight = '0.875em',
  gap = '0.5em',
  lastLineWidth = '60%',
  className,
}: {
  lines?: number;
  lineHeight?: string;
  gap?: string;
  lastLineWidth?: string;
  className?: string;
}) {
  return (
    <div className={cn('flex flex-col', className)} style={{ gap }}>
      {Array.from({ length: lines }).map((_, i) => (
        <SkeletonLine
          key={i}
          height={lineHeight}
          width={i === lines - 1 ? lastLineWidth : '100%'}
        />
      ))}
    </div>
  );
}

/**
 * Skeleton card - complete card placeholder
 */
export function SkeletonCard({
  hasHeader = true,
  hasFooter = false,
  contentLines = 3,
  className,
}: {
  hasHeader?: boolean;
  hasFooter?: boolean;
  contentLines?: number;
  className?: string;
}) {
  return (
    <Card className={cn('overflow-hidden', className)}>
      {hasHeader && (
        <CardHeader className="pb-4">
          <SkeletonLine width="60%" height="1.25em" className="mb-2" />
          <SkeletonLine width="40%" height="0.875em" />
        </CardHeader>
      )}
      <CardContent>
        <SkeletonText lines={contentLines} />
      </CardContent>
      {hasFooter && (
        <div className="px-6 py-4 border-t border-border bg-muted/30">
          <div className="flex justify-end gap-2">
            <SkeletonLine width="80px" height="2em" />
            <SkeletonLine width="100px" height="2em" />
          </div>
        </div>
      )}
    </Card>
  );
}

/**
 * Skeleton table row
 */
export function SkeletonTableRow({
  columns = 4,
  className,
}: {
  columns?: number;
  className?: string;
}) {
  return (
    <div className={cn('flex items-center gap-4 py-3', className)}>
      {Array.from({ length: columns }).map((_, i) => (
        <SkeletonLine
          key={i}
          width={i === 0 ? '30%' : `${70 / (columns - 1)}%`}
          height="1em"
        />
      ))}
    </div>
  );
}

/**
 * Skeleton table - complete table placeholder
 */
export function SkeletonTable({
  rows = 5,
  columns = 4,
  hasHeader = true,
  className,
}: {
  rows?: number;
  columns?: number;
  hasHeader?: boolean;
  className?: string;
}) {
  return (
    <div className={cn('w-full', className)}>
      {hasHeader && (
        <div className="flex items-center gap-4 py-3 border-b border-border">
          {Array.from({ length: columns }).map((_, i) => (
            <SkeletonLine
              key={i}
              width={i === 0 ? '30%' : `${70 / (columns - 1)}%`}
              height="0.875em"
              className="bg-muted-foreground/20"
            />
          ))}
        </div>
      )}
      <div className="divide-y divide-border">
        {Array.from({ length: rows }).map((_, i) => (
          <SkeletonTableRow key={i} columns={columns} />
        ))}
      </div>
    </div>
  );
}

/**
 * Skeleton page - full page loading state
 */
export function SkeletonPage({
  hasHeader = true,
  sidebarWidth = '260px',
  className,
}: {
  hasHeader?: boolean;
  sidebarWidth?: string;
  className?: string;
}) {
  return (
    <div className={cn('flex h-screen bg-background', className)}>
      {/* Sidebar */}
      <div
        className="border-r border-border bg-card p-4 flex flex-col gap-4"
        style={{ width: sidebarWidth }}
      >
        <SkeletonLine width="80%" height="1.5em" />
        <div className="flex-1 space-y-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonLine key={i} width={`${70 + ((i * 17) % 30)}%`} height="1em" />
          ))}
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {hasHeader && (
          <div className="h-14 border-b border-border flex items-center px-6 gap-4">
            <SkeletonLine width="200px" height="1.25em" />
            <div className="ml-auto flex items-center gap-3">
              <SkeletonLine width="32px" height="32px" />
              <SkeletonLine width="32px" height="32px" />
            </div>
          </div>
        )}
        <div className="flex-1 p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            <SkeletonCard hasHeader contentLines={4} />
            <SkeletonCard hasHeader contentLines={3} />
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton stats - metric cards placeholder
 */
export function SkeletonStats({
  cards = 4,
  className,
}: {
  cards?: number;
  className?: string;
}) {
  return (
    <div className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4', className)}>
      {Array.from({ length: cards }).map((_, i) => (
        <Card key={i} className="p-6">
          <SkeletonLine width="40%" height="0.875em" className="mb-2" />
          <SkeletonLine width="60%" height="2em" className="mb-1" />
          <SkeletonLine width="30%" height="0.75em" />
        </Card>
      ))}
    </div>
  );
}

/**
 * Skeleton form - form fields placeholder
 */
export function SkeletonForm({
  fields = 4,
  className,
}: {
  fields?: number;
  className?: string;
}) {
  return (
    <div className={cn('space-y-4', className)}>
      {Array.from({ length: fields }).map((_, i) => (
        <div key={i} className="space-y-2">
          <SkeletonLine width="30%" height="0.875em" />
          <SkeletonLine width="100%" height="2.25em" />
        </div>
      ))}
      <div className="pt-4 flex gap-3">
        <SkeletonLine width="120px" height="2.25em" />
        <SkeletonLine width="100px" height="2.25em" />
      </div>
    </div>
  );
}
