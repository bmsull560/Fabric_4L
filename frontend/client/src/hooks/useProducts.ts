/**
 * useProducts — Product Portfolio hooks (L3 Knowledge Graph)
 *
 * Covers all /v1/products endpoints from the Data Intelligence Layer.
 * Follows Contract C (Hook Architecture) Tier 2 domain hook pattern.
 *
 * Backend: layer3-knowledge/src/api/routes/products.py
 * Endpoints: 12
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

// ── Types ──────────────────────────────────────────────────────────────────
// These will migrate to generated types once OpenAPI specs include DIL endpoints.

export interface Product {
  id: string;
  name: string;
  category: string;
  description?: string;
  target_personas: string[];
  capabilities: string[];
  features: ProductFeature[];
  created_at: string;
  updated_at: string;
}

export interface ProductFeature {
  id: string;
  name: string;
  description?: string;
  differentiator: boolean;
}

export interface CreateProductRequest {
  name: string;
  category: string;
  description?: string;
  target_personas?: string[];
}

export interface UpdateProductRequest {
  name?: string;
  category?: string;
  description?: string;
  target_personas?: string[];
}

export interface ProductListFilters {
  category?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface ProductListResponse {
  products: Product[];
  total: number;
}

export interface SignalMatch {
  signal_id: string;
  signal_text: string;
  product_id: string;
  product_name: string;
  matched_capabilities: string[];
  relevance_score: number;
}

export interface PortfolioSummary {
  total_products: number;
  total_features: number;
  total_capabilities: number;
  categories: Record<string, number>;
  avg_features_per_product: number;
}

export interface CapabilityCoverage {
  capability: string;
  product_count: number;
  products: string[];
  coverage_ratio: number;
}

export interface AddFeatureRequest {
  name: string;
  description?: string;
  differentiator?: boolean;
}

export interface AddCapabilityRequest {
  capability_name: string;
}

// ── Domain Error ───────────────────────────────────────────────────────────

export class ProductApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'ProductApiError';
  }
}

// ── Fetch Functions ────────────────────────────────────────────────────────

function buildProductParams(filters: ProductListFilters): string {
  const params = new URLSearchParams();
  if (filters.category) params.set('category', filters.category);
  if (filters.search) params.set('search', filters.search);
  if (filters.skip != null) params.set('skip', filters.skip.toString());
  if (filters.limit != null) params.set('limit', filters.limit.toString());
  const qs = params.toString();
  return qs ? `?${qs}` : '';
}

async function fetchProducts(filters: ProductListFilters): Promise<ProductListResponse> {
  const response = await apiClient.get('l3', `/v1/products${buildProductParams(filters)}`);
  return response.data as ProductListResponse;
}

async function fetchProduct(productId: string): Promise<Product> {
  const response = await apiClient.get('l3', `/v1/products/${productId}`);
  return response.data as Product;
}

async function fetchSignalMatching(accountId?: string): Promise<SignalMatch[]> {
  const qs = accountId ? `?account_id=${accountId}` : '';
  const response = await apiClient.get('l3', `/v1/products/matching/signals${qs}`);
  return response.data as SignalMatch[];
}

async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const response = await apiClient.get('l3', '/v1/products/analytics/summary');
  return response.data as PortfolioSummary;
}

async function fetchCapabilityCoverage(): Promise<CapabilityCoverage[]> {
  const response = await apiClient.get('l3', '/v1/products/analytics/coverage');
  return response.data as CapabilityCoverage[];
}

// ── Query Hooks ────────────────────────────────────────────────────────────

export function useProducts(filters: ProductListFilters = {}) {
  return useQuery<ProductListResponse, ProductApiError>({
    queryKey: QK.products.list(filters),
    queryFn: () => withApiError(fetchProducts(filters), ProductApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useProduct(productId: string | null) {
  return useQuery<Product, ProductApiError>({
    queryKey: QK.products.detail(productId || ''),
    queryFn: async () => {
      if (!productId) throw new ProductApiError('No product ID provided');
      return withApiError(fetchProduct(productId), ProductApiError);
    },
    enabled: !!productId,
    staleTime: STALE_TIME.detail,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useProductSignalMatching(accountId?: string) {
  return useQuery<SignalMatch[], ProductApiError>({
    queryKey: QK.products.signalMatching(accountId),
    queryFn: () => withApiError(fetchSignalMatching(accountId), ProductApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function usePortfolioSummary() {
  return useQuery<PortfolioSummary, ProductApiError>({
    queryKey: QK.products.summary(),
    queryFn: () => withApiError(fetchPortfolioSummary(), ProductApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

export function useCapabilityCoverage() {
  return useQuery<CapabilityCoverage[], ProductApiError>({
    queryKey: QK.products.coverage(),
    queryFn: () => withApiError(fetchCapabilityCoverage(), ProductApiError),
    staleTime: STALE_TIME.stats,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

// ── Mutation Hooks ─────────────────────────────────────────────────────────

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation<Product, ProductApiError, CreateProductRequest>({
    mutationFn: async (params) => {
      const response = await apiClient.post('l3', '/v1/products', params);
      return response.data as Product;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.products.all });
    },
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation<Product, ProductApiError, { productId: string; data: UpdateProductRequest }>({
    mutationFn: async ({ productId, data }) => {
      const response = await apiClient.patch('l3', `/v1/products/${productId}`, data);
      return response.data as Product;
    },
    onSuccess: (_data, { productId }) => {
      queryClient.invalidateQueries({ queryKey: QK.products.all });
      queryClient.invalidateQueries({ queryKey: QK.products.detail(productId) });
    },
  });
}

export function useDeleteProduct() {
  const queryClient = useQueryClient();
  return useMutation<void, ProductApiError, string>({
    mutationFn: async (productId) => {
      await apiClient.delete('l3', `/v1/products/${productId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.products.all });
    },
  });
}

export function useAddProductFeature() {
  const queryClient = useQueryClient();
  return useMutation<ProductFeature, ProductApiError, { productId: string; data: AddFeatureRequest }>({
    mutationFn: async ({ productId, data }) => {
      const response = await apiClient.post('l3', `/v1/products/${productId}/features`, data);
      return response.data as ProductFeature;
    },
    onSuccess: (_data, { productId }) => {
      queryClient.invalidateQueries({ queryKey: QK.products.detail(productId) });
      queryClient.invalidateQueries({ queryKey: QK.products.all });
    },
  });
}

export function useDeleteProductFeature() {
  const queryClient = useQueryClient();
  return useMutation<void, ProductApiError, { productId: string; featureId: string }>({
    mutationFn: async ({ productId, featureId }) => {
      await apiClient.delete('l3', `/v1/products/${productId}/features/${featureId}`);
    },
    onSuccess: (_data, { productId }) => {
      queryClient.invalidateQueries({ queryKey: QK.products.detail(productId) });
    },
  });
}

export function useAddProductCapability() {
  const queryClient = useQueryClient();
  return useMutation<{ capability_id: string }, ProductApiError, { productId: string; data: AddCapabilityRequest }>({
    mutationFn: async ({ productId, data }) => {
      const response = await apiClient.post('l3', `/v1/products/${productId}/capabilities`, data);
      return response.data as { capability_id: string };
    },
    onSuccess: (_data, { productId }) => {
      queryClient.invalidateQueries({ queryKey: QK.products.detail(productId) });
      queryClient.invalidateQueries({ queryKey: QK.products.all });
    },
  });
}

export function useDeleteProductCapability() {
  const queryClient = useQueryClient();
  return useMutation<void, ProductApiError, { productId: string; capabilityId: string }>({
    mutationFn: async ({ productId, capabilityId }) => {
      await apiClient.delete('l3', `/v1/products/${productId}/capabilities/${capabilityId}`);
    },
    onSuccess: (_data, { productId }) => {
      queryClient.invalidateQueries({ queryKey: QK.products.detail(productId) });
    },
  });
}
