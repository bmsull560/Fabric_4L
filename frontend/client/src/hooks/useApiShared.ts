/**
 * Shared utilities for API hooks
 * 
 * Provides common error handling, cache configuration, and retry logic
 * to eliminate duplication across useFormulas, useBenchmarks, useVariables, etc.
 */

// Cache duration constants (milliseconds)
export const STALE_TIME = {
  list: 30 * 1000,       // 30 seconds for lists
  detail: 5 * 60 * 1000, // 5 minutes for single item
  stats: 60 * 1000,      // 1 minute for stats
  bindings: 30 * 1000,   // 30 seconds for bindings
} as const;

// Retry configuration for transient failures
// Detects Vitest environment and disables retries to prevent test timeouts
const isTestEnv = typeof process !== 'undefined' && process.env?.VITEST === 'true';

export const RETRY_CONFIG = {
  maxRetries: isTestEnv ? false : 3,
  retryDelay: (attemptIndex: number) => Math.min(1000 * 2 ** attemptIndex, 30000),
} as const;

// Base API error class with structured error information
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

// Type for error class constructors
export type ApiErrorClass = 
  | typeof FormulaApiError 
  | typeof BenchmarkApiError 
  | typeof VariableApiError 
  | typeof BaseApiError;

/**
 * Wraps an API call with standardized error handling
 * Extracts status code and response data from axios-style errors
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
