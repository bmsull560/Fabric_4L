import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import axiosRetry from 'axios-retry';
import { z } from 'zod';

// ============================================================================
// MANDATE 4: INPUT VALIDATION - Runtime validation schemas
// ============================================================================

/** Valid layer keys - single source of truth */
const VALID_LAYER_KEYS = ['l1', 'l2', 'l3', 'l4', 'l5', 'l6'] as const;

/** Zod schema for layer key validation */
const LayerKeySchema = z.enum(VALID_LAYER_KEYS);
export type LayerKey = z.infer<typeof LayerKeySchema>;

/** API path validation - must start with / */
const ApiPathSchema = z.string().regex(/^\//, 'API path must start with /');

/** Backend error response schema - replaces unsafe `as ErrorResponse` */
const ErrorResponseSchema = z.object({
  message: z.string().optional(),
  code: z.string().optional(),
  trace_id: z.string().optional(),
});

type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

/**
 * Safe localStorage accessor with null checks and try/catch.
 *
 * P1-21 SECURITY WARNING: Storing access tokens in localStorage makes them
 * vulnerable to XSS extraction. This is a known risk that should be
 * migrated to httpOnly cookies with CSRF protection in a future release.
 *
 * TODO(P1-21): Migrate to httpOnly cookie-based auth with SameSite=Strict
 */
const safeLocalStorage = {
  isAvailable(): boolean {
    try {
      return typeof window !== 'undefined' && window.localStorage !== null;
    } catch {
      return false;
    }
  },

  getItem(key: string): string | null {
    try {
      if (!this.isAvailable()) return null;
      return window.localStorage.getItem(key);
    } catch (error) {
      logError('localStorage.getItem failed', { key, error });
      return null;
    }
  },

  removeItem(key: string): void {
    try {
      if (!this.isAvailable()) return;
      window.localStorage.removeItem(key);
    } catch (error) {
      logError('localStorage.removeItem failed', { key, error });
    }
  },
};

/** Safe logging that guards against production leakage */
function logError(message: string, context?: Record<string, unknown>): void {
  if (process.env.NODE_ENV === 'development') {
    // eslint-disable-next-line no-console
    console.error(`[ApiClient] ${message}`, context ?? '');
  }
}

function logWarn(message: string, context?: Record<string, unknown>): void {
  if (process.env.NODE_ENV === 'development') {
    // eslint-disable-next-line no-console
    console.warn(`[ApiClient] ${message}`, context ?? '');
  }
}

// ============================================================================
// Environment Configuration with Validation
// ============================================================================

/** Get environment variable with fallback and validation */
function getEnvVar(name: string, fallback: string): string {
  const value = import.meta.env[name];
  if (typeof value === 'string' && value.length > 0) {
    return value;
  }
  logWarn(`Environment variable ${name} not set, using fallback`, { fallback });
  return fallback;
}

// Base API path - layer prefixes must include /v1 to match backend OpenAPI routes
const API_BASE = getEnvVar('VITE_API_BASE', '/api');

// Layer prefixes (must match .env.example to avoid double-/v1 when VITE_API_BASE is set)
const LAYER_PREFIXES = {
  l1: getEnvVar('VITE_L1_PREFIX', '/ingest'),
  l2: getEnvVar('VITE_L2_PREFIX', '/extract'),
  l3: getEnvVar('VITE_L3_PREFIX', '/graph'),
  l4: getEnvVar('VITE_L4_PREFIX', '/agents'),
  l5: getEnvVar('VITE_L5_PREFIX', '/truths'),
  l6: getEnvVar('VITE_L6_PREFIX', '/benchmarks'),
} as const;

/**
 * Generate a request correlation ID for tracing
 */
function generateRequestId(): string {
  return `req_${Math.random().toString(36).substring(2, 15)}${Math.random().toString(36).substring(2, 15)}`;
}

/**
 * Custom API error class with trace ID support
 */
export class ApiError extends Error {
  public traceId: string | null;
  public statusCode: number;
  public errorCode: string;

  constructor(
    message: string,
    statusCode: number = 500,
    errorCode: string = 'INTERNAL_ERROR',
    traceId: string | null = null
  ) {
    super(message);
    this.name = 'ApiError';
    this.traceId = traceId;
    this.statusCode = statusCode;
    this.errorCode = errorCode;
  }
}

/**
 * Request deduplication cache entry
 * Stores in-flight promise to be shared by duplicate requests
 */
interface InFlightRequest<T> {
  promise: Promise<T>;
  timestamp: number;
}

class ApiClient {
  private clients: Map<LayerKey, AxiosInstance> = new Map();
  // PERF: Request deduplication - share in-flight promises for identical requests
  private inFlightRequests: Map<string, InFlightRequest<unknown>> = new Map();
  // Maximum age for in-flight request entries (prevents memory leaks)
  private readonly DEDUPE_TTL_MS = 30000;

  constructor() {
    this.initializeClients();
    // Cleanup stale entries periodically
    setInterval(() => this.cleanupStaleRequests(), this.DEDUPE_TTL_MS);
  }

  /**
   * Cleanup stale in-flight request entries to prevent memory leaks
   */
  private cleanupStaleRequests(): void {
    const now = Date.now();
    for (const [key, entry] of this.inFlightRequests.entries()) {
      if (now - entry.timestamp > this.DEDUPE_TTL_MS) {
        this.inFlightRequests.delete(key);
      }
    }
  }

  /**
   * Generate unique key for request deduplication
   */
  private getRequestKey(layer: LayerKey, method: string, path: string, data?: unknown): string {
    return `${layer}:${method}:${path}:${data ? JSON.stringify(data) : ''}`;
  }

  private initializeClients() {
    (Object.keys(LAYER_PREFIXES) as LayerKey[]).forEach((layer) => {
      const client = axios.create({
        baseURL: `${API_BASE}${LAYER_PREFIXES[layer]}`,
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 30000,
      });

      // Configure retry: 3 attempts with exponential delay for transient errors
      axiosRetry(client, {
        retries: 3,
        retryDelay: axiosRetry.exponentialDelay,
        retryCondition: (error) => {
          // Retry on network errors and 5xx responses
          return axiosRetry.isNetworkOrIdempotentRequestError(error) ||
            (error.response?.status !== undefined && error.response.status >= 500);
        },
      });

      client.interceptors.request.use(
        (config) => {
          // MANDATE 1: NULL/UNDEFINED SAFETY - Safe localStorage access
          // Add correlation ID for request tracing
          config.headers['X-Request-ID'] = generateRequestId();

          const tenantId = safeLocalStorage.getItem('tenantId') ?? 'default';
          config.headers['X-Tenant-ID'] = tenantId;

          const token = safeLocalStorage.getItem('accessToken');
          if (typeof token === 'string' && token.length > 0) {
            config.headers['Authorization'] = `Bearer ${token}`;
          }

          return config;
        },
        (error: AxiosError) => {
          // MANDATE 3: ERROR HANDLING COMPLETENESS - Log request errors with context
          logError('Request interceptor error', {
            message: error.message,
            code: error.code,
            stack: error.stack,
          });
          return Promise.reject(error);
        }
      );

      client.interceptors.response.use(
        (response) => response,
        (error: AxiosError) => {
          // MANDATE 2: TYPE SAFETY - Runtime validation with Zod instead of `as` assertion
          const parseResult = ErrorResponseSchema.safeParse(error.response?.data);
          const errorData: ErrorResponse = parseResult.success ? parseResult.data : {};

          // MANDATE 1: NULL/UNDEFINED SAFETY - Optional chaining with nullish coalescing
          const traceId =
            (typeof error.response?.headers['x-request-id'] === 'string'
              ? error.response.headers['x-request-id']
              : null) ??
            errorData.trace_id ??
            null;

          // MANDATE 3: ERROR HANDLING COMPLETENESS - Auth error handling with safe storage
          if (error.response?.status === 401) {
            // Clear auth state and redirect to login
            safeLocalStorage.removeItem('accessToken');
            safeLocalStorage.removeItem('userInfo');
            safeLocalStorage.removeItem('tenantId');
            // Avoid infinite redirect loop: only redirect if not already on /login
            if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
              window.location.replace('/login');
            }
          }

          // MANDATE 3: Log error with full context for debugging
          logError('API request failed', {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            errorCode: errorData.code,
            traceId,
            message: error.message,
          });

          // Transform to ApiError with trace ID for ErrorBoundary
          const apiError = new ApiError(
            errorData.message ?? error.message ?? 'API request failed',
            error.response?.status ?? 500,
            errorData.code ?? 'INTERNAL_ERROR',
            traceId
          );

          return Promise.reject(apiError);
        }
      );

      this.clients.set(layer, client);
    });
  }

  /**
   * MANDATE 4: INPUT VALIDATION - Get client for layer with fail-fast validation
   * @throws {TypeError} If layer is invalid
   * @throws {Error} If client not initialized for valid layer
   */
  getClient(layer: LayerKey): AxiosInstance {
    // Validate layer key at runtime
    const validation = LayerKeySchema.safeParse(layer);
    if (!validation.success) {
      const error = new TypeError(
        `Invalid layer key: ${String(layer)}. Must be one of: ${VALID_LAYER_KEYS.join(', ')}`
      );
      logError('Layer validation failed', { layer, error: error.message });
      throw error;
    }

    const client = this.clients.get(layer);
    if (!client) {
      const error = new Error(`API client for layer ${layer} not initialized`);
      logError('Client lookup failed', { layer, error: error.message });
      throw error;
    }
    return client;
  }

  // MANDATE 4: INPUT VALIDATION - All HTTP methods validate path starts with /
  // PERF: Request deduplication applied to GET requests
  async get(layer: LayerKey, path: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    const validatedPath = ApiPathSchema.parse(path);
    const requestKey = this.getRequestKey(layer, 'GET', validatedPath);

    // Check for existing in-flight request
    const existing = this.inFlightRequests.get(requestKey);
    if (existing) {
      logWarn('Deduplicating identical in-flight GET request', { path: validatedPath, layer });
      return existing.promise as Promise<AxiosResponse>;
    }

    // Create new request promise
    const promise = this.getClient(layer).get(validatedPath, config);

    // Track in-flight request
    this.inFlightRequests.set(requestKey, {
      promise: promise as Promise<AxiosResponse>,
      timestamp: Date.now(),
    });

    // Cleanup when complete
    promise.finally(() => {
      this.inFlightRequests.delete(requestKey);
    });

    return promise;
  }

  // PERF: Request deduplication applied to POST requests (for idempotent operations)
  async post(layer: LayerKey, path: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    const validatedPath = ApiPathSchema.parse(path);
    const requestKey = this.getRequestKey(layer, 'POST', validatedPath, data);

    // Check for existing in-flight request
    const existing = this.inFlightRequests.get(requestKey);
    if (existing) {
      logWarn('Deduplicating identical in-flight POST request', { path: validatedPath, layer });
      return existing.promise as Promise<AxiosResponse>;
    }

    // Create new request promise
    const promise = this.getClient(layer).post(validatedPath, data, config);

    // Track in-flight request
    this.inFlightRequests.set(requestKey, {
      promise: promise as Promise<AxiosResponse>,
      timestamp: Date.now(),
    });

    // Cleanup when complete
    promise.finally(() => {
      this.inFlightRequests.delete(requestKey);
    });

    return promise;
  }

  async put(layer: LayerKey, path: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    const validatedPath = ApiPathSchema.parse(path);
    return this.getClient(layer).put(validatedPath, data, config);
  }

  async patch(layer: LayerKey, path: string, data?: unknown, config?: AxiosRequestConfig) {
    const validatedPath = ApiPathSchema.parse(path);
    return this.getClient(layer).patch(validatedPath, data, config);
  }

  async delete(layer: LayerKey, path: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    const validatedPath = ApiPathSchema.parse(path);
    return this.getClient(layer).delete(validatedPath, config);
  }
}

export const apiClient = new ApiClient();
export { LAYER_PREFIXES };
