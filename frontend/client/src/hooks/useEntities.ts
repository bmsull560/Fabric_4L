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

export interface GraphEntity {
  id: string;
  name: string;
  entity_type: string;
  confidence_score: number;
  description?: string;
  properties?: Record<string, unknown>;
}

export interface EntityContextResponse {
  entity_id: string;
  center: GraphEntity;
  neighbors: GraphEntity[];
  relationships: Array<{
    source: string;
    target: string;
    type: string;
  }>;
  entity_count: number;
  relationship_count: number;
}

/**
 * Get entity by ID using the entity context endpoint.
 * Fetches the entity and its immediate neighborhood (1 hop).
 *
 * @param id - Entity ID to fetch
 * @returns Query result with entity details
 *
 * @example
 * const { data, isLoading } = useEntity('entity-123');
 * // data contains the entity with its properties
 */
export function useEntity(id: string | null) {
  return useQuery<Entity, Error>({
    queryKey: QK.entities.detail(id || ''),
    queryFn: async (): Promise<Entity> => {
      if (!id) throw new Error('No entity ID provided');

      const encodedId = encodeURIComponent(id);
      const response = await apiClient.get(
        'l3',
        `/entity/${encodedId}/context?hops=1`
      );

      const context = response.data as EntityContextResponse;
      if (!context?.center) {
        throw new Error('Entity not found');
      }

      const center = context.center;
      return {
        id: center.id || id,
        name: center.name || 'Unknown',
        type: mapEntityType(center.entity_type || ''),
        confidence: center.confidence_score ?? 0.8,
        description: center.description,
        properties: center.properties,
      };
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
