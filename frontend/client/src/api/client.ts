import axios, { AxiosError, AxiosInstance, AxiosRequestConfig } from 'axios';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

const LAYER_PREFIXES = {
  l1: import.meta.env.VITE_L1_PREFIX || '/ingest',
  l2: import.meta.env.VITE_L2_PREFIX || '/extract',
  l3: import.meta.env.VITE_L3_PREFIX || '/graph',
  l4: import.meta.env.VITE_L4_PREFIX || '/agents',
  l5: import.meta.env.VITE_L5_PREFIX || '/truths',
  l6: import.meta.env.VITE_L6_PREFIX || '/benchmarks',
} as const;

type LayerKey = keyof typeof LAYER_PREFIXES;

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

class ApiClient {
  private clients: Map<LayerKey, AxiosInstance> = new Map();

  constructor() {
    this.initializeClients();
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

      client.interceptors.request.use(
        (config) => {
          // Add correlation ID for request tracing
          config.headers['X-Request-ID'] = generateRequestId();

          const tenantId = localStorage.getItem('tenantId') || 'default';
          config.headers['X-Tenant-ID'] = tenantId;

          const token = localStorage.getItem('accessToken');
          if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
          }

          return config;
        },
        (error) => Promise.reject(error)
      );

      client.interceptors.response.use(
        (response) => response,
        (error: AxiosError) => {
          // Type for standardized error response from backend
          interface ErrorResponse {
            message?: string;
            code?: string;
            trace_id?: string;
          }
          
          const errorData = error.response?.data as ErrorResponse | undefined;
          
          // Extract trace ID from response headers or body
          const traceId = (error.response?.headers['x-request-id'] as string | undefined) || 
                         errorData?.trace_id || 
                         null;

          if (error.response?.status === 401) {
            // Clear auth state and redirect to login
            localStorage.removeItem('accessToken');
            localStorage.removeItem('userInfo');
            localStorage.removeItem('tenantId');
            // Avoid infinite redirect loop: only redirect if not already on /login
            if (window.location.pathname !== '/login') {
              window.location.replace('/login');
            }
          }

          // Transform to ApiError with trace ID for ErrorBoundary
          const apiError = new ApiError(
            errorData?.message || error.message || 'API request failed',
            error.response?.status || 500,
            errorData?.code || 'INTERNAL_ERROR',
            traceId
          );

          return Promise.reject(apiError);
        }
      );

      this.clients.set(layer, client);
    });
  }

  getClient(layer: LayerKey): AxiosInstance {
    const client = this.clients.get(layer);
    if (!client) throw new Error(`API client for layer ${layer} not initialized`);
    return client;
  }

  async get(layer: LayerKey, path: string, config?: AxiosRequestConfig) {
    return this.getClient(layer).get(path, config);
  }

  async post(layer: LayerKey, path: string, data?: unknown, config?: AxiosRequestConfig) {
    return this.getClient(layer).post(path, data, config);
  }

  async put(layer: LayerKey, path: string, data?: unknown, config?: AxiosRequestConfig) {
    return this.getClient(layer).put(path, data, config);
  }

  async patch(layer: LayerKey, path: string, data?: unknown, config?: AxiosRequestConfig) {
    return this.getClient(layer).patch(path, data, config);
  }

  async delete(layer: LayerKey, path: string, config?: AxiosRequestConfig) {
    return this.getClient(layer).delete(path, config);
  }
}

export const apiClient = new ApiClient();
export { LAYER_PREFIXES };
export type { LayerKey };
