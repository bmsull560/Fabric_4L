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
import { apiGet, apiPost, apiPatch, apiDelete } from '@/api/typedClient';
import type { l3 } from '@/api/generated';
import {
  parseCapabilityCoverageList,
  parseCapabilityMutationResponse,
  parseFeatureMutationResponse,
  parsePortfolioSummary,
  parseProduct,
  parseProductListResponse,
  parseSignalMatchList,
  type CapabilityCoverage,
  type CapabilityMutationResponse,
  type FeatureMutationResponse,
  type PortfolioSummary,
  type Product,
  type ProductFeature,
  type ProductListResponse,
  type SignalMatch,
} from '@/lib/schemas/products';
import { QK } from './queryKeys';
import { withApiError, BaseApiError, STALE_TIME, RETRY_CONFIG } from './useApiShared';

export type {
  CapabilityCoverage,
  PortfolioSummary,
  Product,
  ProductCapability,
  ProductFeature,
  ProductListResponse,
  SignalMatch,
} from '@/lib/schemas/products';

export interface CreateProductRequest {
  name: string;
  description: string;
  category?: string | null;
  sku?: string | null;
  pricing_model?: string | null;
  target_personas?: string[];
  industries?: string[];
  metadata?: Record<string, unknown>;
}

export interface UpdateProductRequest {
  name?: string | null;
  description?: string | null;
  category?: string | null;
  sku?: string | null;
  pricing_model?: string | null;
  target_personas?: string[] | null;
  industries?: string[] | null;
}

export interface ProductListFilters {
  category?: string;
  search?: string;
  skip?: number;
  limit?: number;
}

export interface AddFeatureRequest {
  name: string;
  description: string;
  feature_type?: string;
  maturity?: string;
  metadata?: Record<string, unknown>;
}

export interface AddCapabilityRequest {
  capability_id: string;
  strength?: number;
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
  const response = await apiGet<l3.components['schemas']['ProductListResponse']>('l3', `/v1/products${buildProductParams(filters)}`);
  return parseProductListResponse(response.data);
}

async function fetchProduct(productId: string): Promise<Product> {
  const response = await apiGet<l3.components['schemas']['ProductResponse']>('l3', `/v1/products/${productId}`);
  return parseProduct(response.data);
}

async function fetchSignalMatching(accountId?: string): Promise<SignalMatch[]> {
  const params = new URLSearchParams();
  if (accountId) params.set('account_id', accountId);
  const qs = params.toString();
  const response = await apiGet<l3.components['schemas']['SignalMatchResponse'][]>('l3', `/v1/products/matching/signals${qs ? `?${qs}` : ''}`);
  return parseSignalMatchList(response.data);
}

async function fetchPortfolioSummary(): Promise<PortfolioSummary> {
  const response = await apiGet<l3.components['schemas']['PortfolioSummaryResponse']>('l3', '/v1/products/analytics/summary');
  return parsePortfolioSummary(response.data);
}

async function fetchCapabilityCoverage(): Promise<CapabilityCoverage[]> {
  const response = await apiGet<l3.components['schemas']['CapabilityCoverageItem'][]>('l3', '/v1/products/analytics/coverage');
  return parseCapabilityCoverageList(response.data);
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
      const response = await apiPost<Record<string, unknown>>('l3', '/v1/products', params);
      return parseProduct(response.data);
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
      const response = await apiPatch<Record<string, unknown>>('l3', `/v1/products/${productId}`, data);
      return parseProduct(response.data);
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
      await apiDelete<unknown>('l3', `/v1/products/${productId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.products.all });
    },
  });
}

export function useAddProductFeature() {
  const queryClient = useQueryClient();
  return useMutation<FeatureMutationResponse, ProductApiError, { productId: string; data: AddFeatureRequest }>({
    mutationFn: async ({ productId, data }) => {
      const response = await apiPost<Record<string, unknown>>('l3', `/v1/products/${productId}/features`, data);
      return parseFeatureMutationResponse(response.data);
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
      await apiDelete<unknown>('l3', `/v1/products/${productId}/features/${featureId}`);
    },
    onSuccess: (_data, { productId }) => {
      queryClient.invalidateQueries({ queryKey: QK.products.detail(productId) });
    },
  });
}

export function useAddProductCapability() {
  const queryClient = useQueryClient();
  return useMutation<CapabilityMutationResponse, ProductApiError, { productId: string; data: AddCapabilityRequest }>({
    mutationFn: async ({ productId, data }) => {
      const response = await apiPost<Record<string, unknown>>('l3', `/v1/products/${productId}/capabilities`, data);
      return parseCapabilityMutationResponse(response.data);
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
      await apiDelete<unknown>('l3', `/v1/products/${productId}/capabilities/${capabilityId}`);
    },
    onSuccess: (_data, { productId }) => {
      queryClient.invalidateQueries({ queryKey: QK.products.detail(productId) });
    },
  });
}
