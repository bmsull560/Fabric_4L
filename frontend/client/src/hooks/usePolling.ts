/**
 * usePolling.ts — Centralized polling configuration and hook
 *
 * Previously, four hooks defined their own POLL_INTERVAL_MS constants and
 * managed setInterval/refetchInterval independently:
 *
 *   useJobStream.ts   — POLL_INTERVAL_MS = 2000  (setInterval fallback)
 *   useDocuments.ts   — EXPORT_POLL_INTERVAL_MS = 2000  (setInterval)
 *   useWorkflows.ts   — POLL_INTERVAL_MS = 5000  (refetchInterval)
 *   useIngestion.ts   — refetchInterval: 5000    (inline magic number)
 *
 * This module provides:
 *   1. A single POLL_INTERVALS registry — change once, applies everywhere.
 *   2. A usePolling() hook that wraps setInterval with proper cleanup,
 *      replacing the repeated useRef + setInterval + clearInterval pattern.
 */

import { useEffect, useRef, useCallback } from 'react';

// ── Interval registry ─────────────────────────────────────────────────────────

/**
 * All polling intervals used across the application, in milliseconds.
 * Adjust here to tune polling behaviour globally.
 */
export const POLL_INTERVALS = {
  /** Fast polling for active job streams (ingestion, export) */
  jobStream:   2_000,
  /** Standard polling for document export status checks */
  exportStatus: 2_000,
  /** Standard polling for long-running workflow status */
  workflows:   5_000,
  /** Standard polling for ingestion job list refresh */
  ingestion:   5_000,
} as const;

export type PollIntervalKey = keyof typeof POLL_INTERVALS;

// ── Hook ──────────────────────────────────────────────────────────────────────

interface UsePollingOptions {
  /** Whether polling is currently active */
  enabled: boolean;
  /** Interval in ms — use POLL_INTERVALS[key] for named intervals */
  intervalMs: number;
  /** Callback to invoke on each tick */
  onTick: () => void;
}

/**
 * usePolling — A stable, cleanup-safe polling hook.
 *
 * Replaces the repeated pattern of:
 *   const intervalRef = useRef(null);
 *   useEffect(() => {
 *     intervalRef.current = setInterval(fn, ms);
 *     return () => clearInterval(intervalRef.current);
 *   }, [deps]);
 *
 * The callback is always kept up-to-date via a ref so that stale closures
 * never cause bugs when dependencies change mid-poll.
 *
 * @example
 *   usePolling({
 *     enabled: isJobRunning,
 *     intervalMs: POLL_INTERVALS.jobStream,
 *     onTick: () => refetch(),
 *   });
 */
export function usePolling({ enabled, intervalMs, onTick }: UsePollingOptions): void {
  // Keep the callback ref fresh so we never capture a stale closure
  const callbackRef = useRef(onTick);
  useEffect(() => {
    callbackRef.current = onTick;
  }, [onTick]);

  const stableCallback = useCallback(() => {
    callbackRef.current();
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const id = setInterval(stableCallback, intervalMs);
    return () => clearInterval(id);
  }, [enabled, intervalMs, stableCallback]);
}
