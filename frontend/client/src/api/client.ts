import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import MockAdapter from 'axios-mock-adapter';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1';

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
    this.mockEnabled = USE_MOCKS;
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
    if (!l4Client) return;

    this.mockAdapter = new MockAdapter(l4Client, { delayResponse: 500 });

    this.mockAdapter.onGet('/workflows/active').reply(200, {
      workflows: [
        { id: 'wf-1', name: 'Market Analysis', status: 'running', progress: 65 },
        { id: 'wf-2', name: 'Entity Extraction', status: 'pending', progress: 0 },
      ],
    });

    this.mockAdapter.onPost('/workflows').reply(200, {
      workflow_id: 'wf-new',
      status: 'started',
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
