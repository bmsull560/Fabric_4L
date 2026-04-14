/**
 * Shared utilities for API hooks
 *
 * Single source of truth for cache durations, retry logic, and error handling.
 * All hooks MUST import stale-time values from here instead of defining local
 * constants. This prevents divergence and makes cache tuning a one-line change.
 */

// ── Cache duration constants (milliseconds) ───────────────────────────────────
export const STALE_TIME = {
  // Short-lived — frequently changing data (job queues, sync status)
  realtime:  1_000,           //  1 second  — live job/extraction status
  poll:      30_000,          // 30 seconds — lists, bindings, ingestion jobs
  // Medium-lived — moderately changing data
  list:      30_000,          // 30 seconds — generic list queries
  stats:     60_000,          //  1 minute  — aggregate stats
  activity:  5 * 60_000,      //  5 minutes — account activity, filter options
  // Long-lived — rarely changing reference data
  detail:    5 * 60_000,      //  5 minutes — single-item detail views
  reference: 10 * 60_000,     // 10 minutes — provenance, ontology, value packs
  // Aliases kept for backward compatibility with hooks already using STALE_TIME
  bindings:  30_000,          // 30 seconds (= poll)
  // Domain-specific durations (previously scattered across individual hook files)
  policies:  60_000,          //  1 minute  — benchmark/governance policies
  approvals: 10_000,          // 10 seconds — pending approval queues
} as const;

// ── Retry configuration ───────────────────────────────────────────────────────
// Vitest detection disables retries to prevent test timeouts
const isTestEnv = typeof process !== 'undefined' && process.env?.VITEST === 'true';

export const RETRY_CONFIG = {
  maxRetries: isTestEnv ? false : 3,
  retryDelay: (attemptIndex: number) => Math.min(1_000 * 2 ** attemptIndex, 30_000),
} as const;

// ── Base API error class ──────────────────────────────────────────────────────
export class BaseApiError extends Error {
  constructor(
    message: string,
    public statusCode?: number,
    public responseData?: unknown
  ) {
    super(message);
    this.name = 'BaseApiError';
  }
}

// Domain-specific error classes
export class FormulaApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'FormulaApiError';
  }
}

export class BenchmarkApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'BenchmarkApiError';
  }
}

export class VariableApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'VariableApiError';
  }
}

export type ApiErrorClass =
  | typeof FormulaApiError
  | typeof BenchmarkApiError
  | typeof VariableApiError
  | typeof BaseApiError;

// ── Error wrapper ─────────────────────────────────────────────────────────────
/**
 * Wraps an API call with standardized error handling.
 * Extracts status code and response data from axios-style errors.
 */
export async function withApiError<T, E extends BaseApiError>(
  promise: Promise<T>,
  ErrorClass: new (message: string, statusCode?: number, responseData?: unknown) => E
): Promise<T> {
  try {
    return await promise;
  } catch (err: unknown) {
    if (err instanceof Error && 'response' in err) {
      const axiosErr = err as { response?: { status?: number; data?: unknown } };
      throw new ErrorClass(
        err.message,
        axiosErr.response?.status,
        axiosErr.response?.data
      );
    }
    throw new ErrorClass(err instanceof Error ? err.message : 'Unknown error');
  }
}
