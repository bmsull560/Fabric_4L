import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import MockAdapter from 'axios-mock-adapter';

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';
// Use mocks if explicitly enabled, or default to true in test environment
const isTestEnv = typeof process !== 'undefined' && process.env?.VITEST === 'true';
const envMocks = import.meta.env.VITE_USE_MOCKS;
const USE_MOCKS = envMocks === 'true' || (envMocks === undefined && isTestEnv);
// Disable axios-mock-adapter in test environment - MSW handles mocking
const ENABLE_MOCKS = USE_MOCKS && !isTestEnv;

const LAYER_PREFIXES = {
  l1: import.meta.env.VITE_L1_PREFIX || '/ingest',
  l2: import.meta.env.VITE_L2_PREFIX || '/extract',
  l3: import.meta.env.VITE_L3_PREFIX || '/graph',
  l4: import.meta.env.VITE_L4_PREFIX || '/agents',
  l5: import.meta.env.VITE_L5_PREFIX || '/truths',
} as const;

type LayerKey = keyof typeof LAYER_PREFIXES;

class ApiClient {
  private clients: Map<LayerKey, AxiosInstance> = new Map();
  private mockAdapter: MockAdapter | null = null;
  private mockEnabled: boolean;

  constructor() {
    this.mockEnabled = ENABLE_MOCKS;
    this.initializeClients();
    if (this.mockEnabled) {
      this.setupMocks();
    }
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
          const tenantId = localStorage.getItem('tenantId') || 'default';
          config.headers['X-Tenant-ID'] = tenantId;
          return config;
        },
        (error) => Promise.reject(error)
      );

      client.interceptors.response.use(
        (response) => response,
        (error) => {
          if (error.response?.status === 401) {
            window.location.href = '/login';
          }
          return Promise.reject(error);
        }
      );

      this.clients.set(layer, client);
    });
  }

  private setupMocks() {
    const l4Client = this.clients.get('l4');
    const l2Client = this.clients.get('l2');

    if (l4Client) {
      const l4Mock = new MockAdapter(l4Client, { delayResponse: 500 });

      l4Mock.onGet('/workflows/active').reply(200, [
        { workflow_id: 'wf-1', workflow_type: 'market_analysis', status: 'running', progress_percentage: 65 },
        { workflow_id: 'wf-2', workflow_type: 'entity_extraction', status: 'pending', progress_percentage: 0 },
      ]);

      l4Mock.onPost('/workflows').reply(200, {
        workflow_id: 'wf-new',
        status: 'started',
      });
    }

    // L2 mocks for extraction job endpoints
    if (l2Client) {
      const l2Mock = new MockAdapter(l2Client, { delayResponse: 100 });

      // Match any job ID pattern with test-friendly data
      l2Mock.onGet(/\/jobs\/.+/).reply((config) => {
        const jobId = config.url?.split('/').pop() || 'unknown';
        return [200, {
          id: jobId,
          status: 'EXTRACTING',
          progress_percent_complete: 50,
          progress_pages_found: 10,
          progress_processed_pages: 5,
          progress_logs: [
            { timestamp: '2024-01-15T10:00:00Z', level: 'INFO', message: 'Starting extraction', status: 'OK' },
            { timestamp: '2024-01-15T10:05:00Z', level: 'INFO', message: 'Crawling pages', status: 'OK' },
          ],
          extracted_entities: [
            { type: 'Outcome', name: 'Revenue Growth' },
            { type: 'Capability', name: 'Analytics' },
          ],
          configuration: { url: 'https://example.com' },
          created_at: '2024-01-15T10:00:00Z',
          updated_at: '2024-01-15T10:05:00Z',
        }];
      });

      // Polling endpoint
      l2Mock.onGet(/\/jobs\/.+\/poll/).reply((config) => {
        const jobId = config.url?.split('/')[2] || 'unknown';
        return [200, {
          id: jobId,
          status: 'EXTRACTING',
          progress_percent_complete: 50,
          progress_logs: [],
          extracted_entities: [],
        }];
      });
    }
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

  async delete(layer: LayerKey, path: string, config?: AxiosRequestConfig) {
    return this.getClient(layer).delete(path, config);
  }

  isMockEnabled(): boolean {
    return this.mockEnabled;
  }
}

export const apiClient = new ApiClient();
export { LAYER_PREFIXES };
export type { LayerKey };
