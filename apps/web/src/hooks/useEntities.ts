import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';
import { EntityListResponseSchema, validateOrThrow, validateObject } from '@/lib/validation/schemas';

/**
 * Canonical Entity interface from Layer 3 API
 * Matches the high-quality contract defined in /v1/entities endpoints
 */
export interface Entity {
  id: string;
  name: string;
  type: 'Capability' | 'UseCase' | 'Persona' | 'ValueDriver' | 'KPI';
  domain: string | null;
  status: 'validated' | 'pending' | 'draft' | 'deprecated';
  confidence: number;  // 0.0 to 1.0
  confidenceLabel: 'high' | 'medium' | 'low';
  description?: string;
  updatedAt: string;   // ISO 8601
  sourceName?: string;
  extractionJobId?: string;
  createdAt?: string;
  createdBy?: string;
  properties?: Record<string, unknown>;
}

/**
 * Entity filter parameters for server-backed filtering
 */
export interface EntityFilters {
  searchText?: string;
  entityTypes?: string[];
  domains?: string[];
  statuses?: ('validated' | 'pending' | 'draft' | 'deprecated')[];
  minConfidence?: number;  // 0.0 to 1.0
  maxConfidence?: number;  // 0.0 to 1.0
  limit?: number;
  offset?: number;
  sortBy?: 'name' | 'updated_at' | 'confidence' | 'entity_type' | 'status';
  sortOrder?: 'asc' | 'desc';
}

/**
 * Entity list response from canonical endpoint
 */
export interface EntityListResponse {
  results: Entity[];
  totalCount: number;
  filteredCount: number;
  limit: number;
  offset: number;
  hasMore: boolean;
  availableDomains: string[];
  availableSources: string[];
}

// Map backend entity types to frontend types
function mapEntityType(type: string): Entity['type'] {
  const typeMap: Record<string, Entity['type']> = {
    'Capability': 'Capability',
    'UseCase': 'UseCase',
    'Persona': 'Persona',
    'ValueDriver': 'ValueDriver',
    'KPI': 'KPI',
    'capability': 'Capability',
    'usecase': 'UseCase',
    'persona': 'Persona',
    'valuedriver': 'ValueDriver',
    'kpi': 'KPI',
  };
  return typeMap[type] || 'Capability';
}

/**
 * Map canonical API response to frontend Entity interface
 * Includes runtime validation for null-safety
 */
function mapApiEntity(apiEntity: unknown): Entity {
  const e = validateObject(apiEntity, 'Entity');

  // Required fields with fallbacks for safety
  const id = typeof e.id === 'string' ? e.id : '';
  const name = typeof e.name === 'string' ? e.name : 'Unknown';
  const entityType = typeof e.entity_type === 'string' ? e.entity_type : '';

  return {
    id,
    name,
    type: mapEntityType(entityType),
    domain: typeof e.domain === 'string' ? e.domain : null,
    status: (e.status as Entity['status']) || 'draft',
    confidence: typeof e.confidence === 'number' ? e.confidence : 0.0,
    confidenceLabel: (e.confidence_label as Entity['confidenceLabel']) || 'low',
    description: typeof e.description === 'string' ? e.description : undefined,
    updatedAt: typeof e.updated_at === 'string' ? e.updated_at : new Date().toISOString(),
    sourceName: typeof e.source_name === 'string' ? e.source_name : undefined,
    extractionJobId: typeof e.extraction_job_id === 'string' ? e.extraction_job_id : undefined,
    createdAt: typeof e.created_at === 'string' ? e.created_at : undefined,
    createdBy: typeof e.created_by === 'string' ? e.created_by : undefined,
  };
}

/**
 * Fetch entities with server-backed filtering using canonical endpoint
 * Layer 3 API: GET /v1/entities
 *
 * This uses the high-quality contract endpoint with explicit domain, status,
 * and confidence_label fields - no UI inference needed.
 */
export function useEntities(filters?: EntityFilters) {
  return useQuery({
    queryKey: QK.entities.list(),
    queryFn: async (): Promise<EntityListResponse> => {
      // Build query params from filters
      const params = new URLSearchParams();
      if (filters?.searchText) params.append('search_text', filters.searchText);
      if (filters?.entityTypes?.length) {
        filters.entityTypes.forEach(t => params.append('entity_types', t));
      }
      if (filters?.domains?.length) {
        filters.domains.forEach(d => params.append('domains', d));
      }
      if (filters?.statuses?.length) {
        filters.statuses.forEach(s => params.append('statuses', s));
      }
      if (filters?.minConfidence !== undefined) {
        params.append('min_confidence', filters.minConfidence.toString());
      }
      if (filters?.maxConfidence !== undefined) {
        params.append('max_confidence', filters.maxConfidence.toString());
      }
      params.append('limit', (filters?.limit ?? 25).toString());
      params.append('offset', (filters?.offset ?? 0).toString());
      params.append('sort_by', filters?.sortBy ?? 'updated_at');
      params.append('sort_order', filters?.sortOrder ?? 'desc');

      const response = await apiClient.get('l3', `/entities?${params.toString()}`);
      const data = validateOrThrow(EntityListResponseSchema, response.data, 'EntityListResponse');

      return {
        results: data.results.map(mapApiEntity),
        totalCount: data.total_count,
        filteredCount: data.filtered_count,
        limit: data.limit,
        offset: data.offset,
        hasMore: data.has_more,
        availableDomains: data.available_domains,
        availableSources: data.available_sources,
      };
    },
    staleTime: STALE_TIME.stats,
  });
}

/**
 * Search entities by text using canonical endpoint
 * Layer 3 API: GET /v1/entities?search_text={query}
 */
export function useEntitySearch(query: string) {
  return useQuery({
    queryKey: QK.entities.search(query),
    queryFn: async (): Promise<EntityListResponse> => {
      const params = new URLSearchParams({
        search_text: query.trim(),
        limit: '25',
        sort_by: 'confidence',
        sort_order: 'desc',
      });

      const response = await apiClient.get('l3', `/entities?${params.toString()}`);
      const data = validateOrThrow(EntityListResponseSchema, response.data, 'EntityListResponse');

      return {
        results: data.results.map(mapApiEntity),
        totalCount: data.total_count,
        filteredCount: data.filtered_count,
        limit: data.limit,
        offset: data.offset,
        hasMore: data.has_more,
        availableDomains: data.available_domains,
        availableSources: data.available_sources,
      };
    },
    enabled: query.trim().length > 0,
    staleTime: STALE_TIME.poll,
  });
}

/**
 * Get available filter options (domains, sources) for entity browser
 * Uses the canonical endpoint with a minimal query
 */
export function useEntityFilterOptions() {
  return useQuery({
    queryKey: ['entityFilterOptions'],
    queryFn: async () => {
      const response = await apiClient.get('l3', '/entities?limit=1');
      return {
        availableDomains: response.data.available_domains as string[],
        availableSources: response.data.available_sources as string[],
      };
    },
    staleTime: STALE_TIME.activity,
  });
}

/**
 * Get entity detail by ID using canonical endpoint
 * Layer 3 API: GET /v1/entities/{entity_id}
 *
 * Returns the canonical EntityDetail shape with all fields from EntitySummary
 * plus extended data: relationships, provenance, validation state.
 *
 * @param id - Entity ID to fetch
 * @returns Query result with full entity details
 *
 * @example
 * const { data, isLoading } = useEntity('entity-123');
 * // data contains the entity with domain, status, confidence_label, etc.
 */
export function useEntity(id: string | null) {
  return useQuery<Entity, Error>({
    queryKey: QK.entities.detail(id || ''),
    queryFn: async (): Promise<Entity> => {
      if (!id) throw new Error('No entity ID provided');

      const encodedId = encodeURIComponent(id);
      const response = await apiClient.get(
        'l3',
        `/entities/${encodedId}?include_provenance=true&include_relationships=true`
      );

      const data = response.data;
      if (!data) {
        throw new Error('Entity not found');
      }

      return mapApiEntity(data);
    },
    enabled: !!id,
    staleTime: STALE_TIME.detail,
  });
}

/**
 * Create entity - uses Neo4j directly
 * Note: This is a placeholder as Layer 3 doesn't expose entity creation
 */
export function useCreateEntity() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (entity: Omit<Entity, 'id' | 'createdAt'>) => {
      // Placeholder - would need to call extraction layer or Neo4j directly
      console.warn('Entity creation not implemented in Layer 3 API');
      throw new Error('Entity creation not supported');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QK.entities.list() });
    },
  });
}
