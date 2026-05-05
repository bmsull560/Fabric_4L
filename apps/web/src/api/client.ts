import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import axiosRetry from 'axios-retry';
import { z } from 'zod';
import { createFeatureLogger } from '@/lib/telemetry';
import { sessionService } from '@/services/sessionService';

const log = createFeatureLogger('api-client');

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
  // FastAPI validation errors use `detail` — may be a string or array of issues
  detail: z.union([
    z.string(),
    z.array(z.object({ loc: z.array(z.unknown()), msg: z.string(), type: z.string() })),
    z.unknown(),
  ]).optional(),
});

type ErrorResponse = z.infer<typeof ErrorResponseSchema>;

/** Extract a human-readable message from a FastAPI detail field */
function extractDetailMessage(detail: ErrorResponse['detail']): string | null {
  if (!detail) return null;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        if (typeof d === 'object' && d !== null && 'msg' in d) {
          return String((d as { msg: unknown }).msg);
        }
        return JSON.stringify(d);
      })
      .join('; ');
  }
  return null;
}

function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;
  const key = `${name}=`;
  const match = document.cookie.split('; ').find((part) => part.startsWith(key));
  return match ? decodeURIComponent(match.slice(key.length)) : null;
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
  log.warn(`Environment variable ${name} not set, using fallback`, { fallback });
  return fallback;
}

// Base API path - layer prefixes must include /v1 to match backend OpenAPI routes
const API_BASE = getEnvVar('VITE_API_BASE', '/api/v1');

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
  private cleanupInterval: ReturnType<typeof setInterval> | null = null;

  constructor() {
    this.initializeClients();
    // Cleanup stale entries periodically
    this.cleanupInterval = setInterval(() => this.cleanupStaleRequests(), this.DEDUPE_TTL_MS);
  }

  /**
   * Destroy the ApiClient instance and clean up resources.
   * Call this in tests and during hot-reload to prevent interval leaks.
   */
  destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    this.inFlightRequests.clear();
    this.clients.clear();
  }

  /**
   * Cleanup stale in-flight request entries to prevent memory leaks
   */
  private cleanupStaleRequests(): void {
    const now = Date.now();
    const entries = Array.from(this.inFlightRequests.entries());
    for (const [key, entry] of entries) {
      if (now - entry.timestamp > this.DEDUPE_TTL_MS) {
        this.inFlightRequests.delete(key);
      }
    }
  }

  /**
   * Generate unique key for safe request deduplication.
   * GET dedupe intentionally ignores request bodies because GET requests must not rely on one.
   */
  private getRequestKey(layer: LayerKey, method: string, path: string): string {
    return `${layer}:${method}:${path}`;
  }

  private trackInFlight<T>(requestKey: string, promise: Promise<T>): Promise<T> {
    this.inFlightRequests.set(requestKey, {
      promise,
      timestamp: Date.now(),
    });

    // Cleanup when complete without creating a secondary unhandled rejection.
    void promise.finally(() => {
      this.inFlightRequests.delete(requestKey);
    }).catch(() => undefined);

    return promise;
  }

  private initializeClients() {
    (Object.keys(LAYER_PREFIXES) as LayerKey[]).forEach((layer) => {
      const client = axios.create({
        baseURL: `${API_BASE}${LAYER_PREFIXES[layer]}`,
        withCredentials: true,
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
          // Add correlation ID for request tracing
          config.headers['X-Request-ID'] = generateRequestId();
          config.headers['X-Tenant-ID'] = sessionService.getTenantId();

          // Access token is in the httpOnly vf_session cookie; sent automatically
          // via withCredentials: true. No Authorization header needed.

          const method = (config.method ?? 'get').toUpperCase();
          if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
            const csrfToken = getCookie('vf_csrf_token');
            if (csrfToken) {
              config.headers['X-CSRF-Token'] = csrfToken;
            }
          }

          return config;
        },
        (error: AxiosError) => {
          // MANDATE 3: ERROR HANDLING COMPLETENESS - Log request errors with context
          log.error('Request interceptor error', {
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

          if (error.response?.status === 401) {
            sessionService.handleUnauthorized({ route: typeof window !== 'undefined' ? window.location.pathname : undefined, traceId });
          }

          // MANDATE 3: Log error with full context for debugging
          log.error('API request failed', {
            url: error.config?.url,
            method: error.config?.method,
            status: error.response?.status,
            errorCode: errorData.code,
            traceId,
            message: error.message,
          });

          // Transform to ApiError with trace ID for ErrorBoundary.
          // Prefer `detail` (FastAPI format) over generic `message` for richer error messages.
          const detailMessage = extractDetailMessage(errorData.detail);
          const apiError = new ApiError(
            detailMessage ?? errorData.message ?? error.message ?? 'API request failed',
            error.response?.status ?? 500,
            errorData.code ?? 'INTERNAL_ERROR',
            traceId
          );

          throw apiError;
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
      log.error('Layer validation failed', { layer, error: error.message });
      throw error;
    }

    const client = this.clients.get(layer);
    if (!client) {
      const error = new Error(`API client for layer ${layer} not initialized`);
      log.error('Client lookup failed', { layer, error: error.message });
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
      log.warn('Deduplicating identical in-flight GET request', { path: validatedPath, layer });
      return existing.promise as Promise<AxiosResponse>;
    }

    return this.trackInFlight(requestKey, this.getClient(layer).get(validatedPath, config));
  }

  async post(layer: LayerKey, path: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    const validatedPath = ApiPathSchema.parse(path);
    return this.getClient(layer).post(validatedPath, data, config);
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
