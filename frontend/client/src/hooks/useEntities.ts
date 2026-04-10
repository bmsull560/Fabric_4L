import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface Entity {
  id: string;
  name: string;
  type: 'Capability' | 'UseCase' | 'Persona' | 'ValueDriver' | 'KPI';
  confidence: number;
  description?: string;
  properties?: Record<string, unknown>;
  createdAt?: string;
}

const ENTITY_KEYS = {
  all: ['entities'] as const,
  list: () => [...ENTITY_KEYS.all, 'list'] as const,
  search: (query: string) => [...ENTITY_KEYS.all, 'search', query] as const,
  detail: (id: string) => [...ENTITY_KEYS.all, 'detail', id] as const,
};

/**
 * Search entities using hybrid search (BM25 + vector + graph)
 * Layer 3 API: POST /v1/search/hybrid
 */
export function useEntities() {
  return useQuery({
    queryKey: ENTITY_KEYS.list(),
    queryFn: async () => {
      // Use hybrid search with empty query to get all entities
      const response = await apiClient.post('l3', '/v1/search/hybrid', {
        query: '',
        search_type: 'hybrid',
        top_k: 50,
      });
      // Map search results to Entity format
      const results = response.data?.results || [];
      return results.map((r: any) => ({
        id: r.id || r.entity_id,
        name: r.name || r.title || 'Unknown',
        type: mapEntityType(r.entity_type || r.type),
        confidence: r.confidence_score || r.confidence || 0.8,
        description: r.description,
        properties: r.properties || r.data,
      })) as Entity[];
    },
    staleTime: 60 * 1000,
  });
}

export function useEntitySearch(query: string) {
  return useQuery({
    queryKey: ENTITY_KEYS.search(query),
    queryFn: async () => {
      const response = await apiClient.post('l3', '/v1/search/hybrid', {
        query: query.trim(),
        search_type: 'hybrid',
        top_k: 20,
      });
      const results = response.data?.results || [];
      return results.map((r: any) => ({
        id: r.id || r.entity_id,
        name: r.name || r.title || 'Unknown',
        type: mapEntityType(r.entity_type || r.type),
        confidence: r.confidence_score || r.confidence || 0.8,
        description: r.description,
        properties: r.properties || r.data,
      })) as Entity[];
    },
    enabled: query.trim().length > 0,
    staleTime: 30 * 1000,
  });
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
 * Get entity by ID
 * Note: Layer 3 doesn't have a direct GET /entities/{id}
 * We use GraphRAG query to get entity details
 */
export function useEntity(id: string | null) {
  return useQuery({
    queryKey: ENTITY_KEYS.detail(id || ''),
    queryFn: async () => {
      if (!id) throw new Error('No entity ID provided');
      // Use graph query to get entity details
      const response = await apiClient.post('l3', '/v1/query/graph', {
        query: `Find entity with ID ${id}`,
        max_hops: 1,
        max_results: 1,
      });
      const entities = response.data?.entities || [];
      if (entities.length === 0) throw new Error('Entity not found');
      const e = entities[0];
      return {
        id: e.id || id,
        name: e.name || e.title || 'Unknown',
        type: mapEntityType(e.entity_type || e.type),
        confidence: e.confidence_score || e.confidence || 0.8,
        description: e.description,
        properties: e.properties || e.data,
      } as Entity;
    },
    enabled: !!id,
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
      queryClient.invalidateQueries({ queryKey: ENTITY_KEYS.list() });
    },
  });
}
