import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';
import { parseEntityResults, type ApiEntityResultDto } from '@/types/api';

export interface Entity {
  id: string;
  name: string;
  type: 'Capability' | 'UseCase' | 'Persona' | 'ValueDriver' | 'KPI';
  confidence: number;
  description?: string;
  properties?: Record<string, unknown>;
  createdAt?: string;
}


function mapEntityResult(result: ApiEntityResultDto): Entity {
  return {
    id: result.id || result.entity_id || 'unknown',
    name: result.name || result.title || 'Unknown',
    type: mapEntityType(result.entity_type || result.type || ''),
    confidence: result.confidence_score ?? result.confidence ?? 0.8,
    description: result.description,
    properties: result.properties || result.data,
  };
}

/**
 * Search entities using hybrid search (BM25 + vector + graph)
 * Layer 3 API: POST /search/hybrid
 */
export function useEntities() {
  return useQuery({
    queryKey: QK.entities.list(),
    queryFn: async () => {
      // Use hybrid search with empty query to get all entities
      const response = await apiClient.post('l3', '/search/hybrid', {
        query: '',
        search_type: 'hybrid',
        top_k: 50,
      });
      const results = parseEntityResults(response.data?.results);
      return results.map(mapEntityResult);
    },
    staleTime: STALE_TIME.stats,
  });
}

export function useEntitySearch(query: string) {
  return useQuery({
    queryKey: QK.entities.search(query),
    queryFn: async () => {
      const response = await apiClient.post('l3', '/search/hybrid', {
        query: query.trim(),
        search_type: 'hybrid',
        top_k: 20,
      });
      const results = parseEntityResults(response.data?.results);
      return results.map(mapEntityResult);
    },
    enabled: query.trim().length > 0,
    staleTime: STALE_TIME.poll,
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
    queryKey: QK.entities.detail(id || ''),
    queryFn: async () => {
      if (!id) throw new Error('No entity ID provided');
      // Use graph query to get entity details
      const response = await apiClient.post('l3', '/query/graph', {
        query: `Find entity with ID ${id}`,
        max_hops: 1,
        max_results: 1,
      });
      const entities = parseEntityResults(response.data?.entities);
      if (entities.length === 0) throw new Error('Entity not found');
      const e = entities[0];
      return {
        id: e.id || e.entity_id || id,
        name: e.name || e.title || 'Unknown',
        type: mapEntityType(e.entity_type || e.type || ''),
        confidence: e.confidence_score ?? e.confidence ?? 0.8,
        description: e.description,
        properties: e.properties || e.data,
      };
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
      queryClient.invalidateQueries({ queryKey: QK.entities.list() });
    },
  });
}
