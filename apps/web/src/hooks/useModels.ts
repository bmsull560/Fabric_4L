/**
 * useModels — React Query hooks for value model management
 *
 * Provides CRUD operations for user-created value models.
 * Connected to Layer 3 /v1/models endpoints.
 *
 * Route: /library/models
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { BaseApiError, STALE_TIME, RETRY_CONFIG, withApiError } from './useApiShared';
import { createFeatureLogger } from '@/lib/telemetry';

const log = createFeatureLogger('useModels');

// ── Error class ──────────────────────────────────────────────────────────────

export class ModelApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'ModelApiError';
  }
}

// ── Backend Response Types (snake_case) ──────────────────────────────────────

interface BackendModelSummary {
  model_id: string;
  name: string;
  description: string;
  industry: string;
  tags: string[];
  status: 'draft' | 'active' | 'archived';
  folder: string;
  formula_count: number;
  entity_count: number;
  driver_count: number;
  created_at: string;
  updated_at: string;
  owner: string;
  is_shared: boolean;
}

interface BackendModelListResponse {
  models: BackendModelSummary[];
  total: number;
  offset: number;
  limit: number;
  filters_applied: Record<string, unknown>;
}

interface BackendFolderSummary {
  folder_id: string;
  name: string;
  count: number;
}

interface BackendFoldersResponse {
  folders: BackendFolderSummary[];
}

interface BackendCreateResponse {
  model_id: string;
  message: string;
}

// ── Frontend Types (camelCase) ───────────────────────────────────────────────

export type ModelStatus = 'draft' | 'active' | 'archived';

export interface ValueModel {
  id: string;
  name: string;
  description: string;
  industry: string;
  tags: string[];
  status: ModelStatus;
  folder: string;
  formulaCount: number;
  entityCount: number;
  driverCount: number;
  createdAt: string;
  updatedAt: string;
  owner: string;
  isShared: boolean;
}

export interface ModelFolder {
  id: string;
  name: string;
  count: number;
}

export interface ModelFilters {
  search?: string;
  folder?: string;
  industry?: string;
  status?: ModelStatus | 'all';
  sortBy?: 'name' | 'updatedAt' | 'createdAt';
  sortDir?: 'asc' | 'desc';
}

export interface CreateModelPayload {
  name: string;
  description: string;
  industry: string;
  tags?: string[];
}

// ── Transformers ───────────────────────────────────────────────────────────────

function transformModel(backend: BackendModelSummary): ValueModel {
  return {
    id: backend.model_id,
    name: backend.name,
    description: backend.description,
    industry: backend.industry,
    tags: backend.tags,
    status: backend.status,
    folder: backend.folder,
    formulaCount: backend.formula_count,
    entityCount: backend.entity_count,
    driverCount: backend.driver_count,
    createdAt: backend.created_at,
    updatedAt: backend.updated_at,
    owner: backend.owner,
    isShared: backend.is_shared,
  };
}

function transformFolder(backend: BackendFolderSummary): ModelFolder {
  return {
    id: backend.folder_id,
    name: backend.name,
    count: backend.count,
  };
}

// ── API Fetchers ─────────────────────────────────────────────────────────────

async function fetchModels(filters: ModelFilters): Promise<ValueModel[]> {
  const params = new URLSearchParams();
  
  if (filters.search) params.set('search', filters.search);
  if (filters.folder && filters.folder !== 'all') params.set('folder', filters.folder);
  if (filters.industry && filters.industry !== 'all') params.set('industry', filters.industry);
  if (filters.status && filters.status !== 'all') params.set('status', filters.status);
  
  // Map frontend sort field to backend format
  const sortByMap: Record<string, string> = {
    name: 'name',
    updatedAt: 'updated_at',
    createdAt: 'created_at',
  };
  params.set('sort_by', sortByMap[filters.sortBy || 'updatedAt']);
  params.set('sort_dir', filters.sortDir || 'desc');
  
  const response = await apiClient.get('l3', `/models?${params.toString()}`);
  const data = response.data as BackendModelListResponse;
  return data.models.map(transformModel);
}

async function fetchFolders(): Promise<ModelFolder[]> {
  const response = await apiClient.get('l3', '/models/folders');
  const data = response.data as BackendFoldersResponse;
  return data.folders.map(transformFolder);
}

// ── Hooks ────────────────────────────────────────────────────────────────────

/** Fetch value models with filtering, sorting, and search. */
export function useModels(filters: ModelFilters = {}) {
  return useQuery<ValueModel[], ModelApiError>({
    queryKey: QK.models.list(filters),
    queryFn: () => withApiError(fetchModels(filters), ModelApiError),
    staleTime: STALE_TIME.list,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/** Fetch folder sidebar data. */
export function useModelFolders() {
  return useQuery<ModelFolder[], ModelApiError>({
    queryKey: QK.models.folders(),
    queryFn: () => withApiError(fetchFolders(), ModelApiError),
    staleTime: STALE_TIME.reference,
    retry: RETRY_CONFIG.maxRetries,
    retryDelay: RETRY_CONFIG.retryDelay,
  });
}

/** Create a new value model. */
export function useCreateModel() {
  const queryClient = useQueryClient();

  return useMutation<{ modelId: string }, ModelApiError, CreateModelPayload>({
    mutationFn: async (payload) => {
      if (!payload.name.trim()) throw new ModelApiError('Model name is required');
      
      const response = await apiClient.post('l3', '/models', {
        name: payload.name.trim(),
        description: payload.description?.trim() || '',
        industry: payload.industry,
        tags: payload.tags || [],
      });
      
      const data = response.data as BackendCreateResponse;
      return { modelId: data.model_id };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QK.models.all });
      toast.success('Model created successfully', {
        description: `Model ID: ${data.modelId}`,
      });
    },
    onError: (error) => {
      log.error('useCreateModel mutation failed', { errorCode: error.message });
      toast.error('Failed to create model', {
        description: error.message,
      });
    },
  });
}

/** Delete a value model. */
export function useDeleteModel() {
  const queryClient = useQueryClient();

  return useMutation<{ modelId: string }, ModelApiError, string>({
    mutationFn: async (modelId) => {
      if (!modelId) throw new ModelApiError('Model ID is required');
      
      await apiClient.delete('l3', `/models/${modelId}`);
      return { modelId };
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: QK.models.all });
      toast.success('Model deleted', {
        description: `Model ${data.modelId} has been removed.`,
      });
    },
    onError: (error) => {
      log.error('useDeleteModel mutation failed', { errorCode: error.message });
      toast.error('Failed to delete model', {
        description: error.message,
      });
    },
  });
}
