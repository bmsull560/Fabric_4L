import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';
import {
  GraphQueryResponseSchema,
  EntityContextResponseSchema,
  EntityTraversalResponseSchema,
  safeParseResponse,
} from '@/lib/schemas';

export interface GraphNode {
  id: string;
  name: string;
  entity_type: string;
  confidence_score: number;
  description?: string;
  properties?: Record<string, unknown>;
}

export interface GraphRelationship {
  source: string;
  target: string;
  type: string;
  confidence?: number;
  properties?: Record<string, unknown>;
}

export interface ContextGraph {
  nodes: GraphNode[];
  relationships: GraphRelationship[];
}

export interface GraphQueryRequest {
  query: string;
  entity_type?: string;
  max_hops?: number;
  max_results?: number;
}

export interface GraphQueryResponse {
  query: string;
  entities: GraphNode[];
  relationships: GraphRelationship[];
  context_graph?: ContextGraph;
  confidence_score: number;
  sources?: string[];
  processing_time_ms: number;
}

export interface EntityContextResponse {
  entity_id: string;
  center: GraphNode;
  neighbors: GraphNode[];
  relationships: GraphRelationship[];
  entity_count: number;
  relationship_count: number;
}

export interface EntityTraversalRequest {
  entity_id: string;
  direction?: 'up' | 'down' | 'both';
}

export interface EntityTraversalResponse {
  start_entity_id: string;
  direction: string;
  paths: Array<{
    nodes: GraphNode[];
    relationships: GraphRelationship[];
    value_score?: number;
  }>;
  path_count: number;
}

/** Raw search result from hybrid search - may have varying field names */
export interface SearchResult {
  id?: string;
  entity_id?: string;
  name?: string;
  title?: string;
  entity_type?: string;
  type?: string;
  confidence_score?: number;
  confidence?: number;
  description?: string;
  properties?: Record<string, unknown>;
  data?: Record<string, unknown>;
}

/** Error type for graph API operations */
export interface GraphApiError {
  message: string;
  code?: string;
  statusCode?: number;
}

/**
 * Execute a GraphRAG query with multi-hop traversal.
 * POST /query/graph
 */
export function useGraphQuery() {
  const queryClient = useQueryClient();

  return useMutation<GraphQueryResponse, GraphApiError, GraphQueryRequest>({
    mutationFn: async (request): Promise<GraphQueryResponse> => {
      const response = await apiClient.post('l3', '/query/graph', {
        query: request.query,
        entity_type: request.entity_type,
        max_hops: request.max_hops ?? 2,
        max_results: request.max_results ?? 20,
      });

      // Runtime validation at trust boundary
      const validated = safeParseResponse(GraphQueryResponseSchema, response.data, 'POST /query/graph');
      if (!validated) {
        throw new Error('Invalid graph query response format');
      }
      return validated;
    },
    onSuccess: (data) => {
      // Cache the entities from the response for other queries
      data.entities?.forEach((entity) => {
        if (!entity.id) return; // Skip entities without IDs
        queryClient.setQueryData(QK.graph.context(entity.id, 0), {
          entity_id: entity.id,
          center: entity,
          neighbors: [],
          relationships: [],
          entity_count: 1,
          relationship_count: 0,
        });
      });
    },
    onError: (error) => {
      console.error('GraphRAG query failed:', error);
    },
  });
}

/**
 * Get neighborhood context around an entity.
 * Fetches connected entities and relationships within specified hop count.
 *
 * @param entityId - The entity ID to get context for (null disables the query)
 * @param hops - Number of relationship hops to traverse (default: 2)
 * @param relationshipTypes - Optional filter for specific relationship types
 * @returns Query result with neighbors, relationships, and center entity
 *
 * @example
 * const { data, isLoading } = useEntityContext('entity-123', 2, ['depends_on']);
 */
export function useEntityContext(
  entityId: string | null,
  hops: number = 2,
  relationshipTypes?: string[]
) {
  return useQuery({
    queryKey: QK.graph.context(entityId || '', hops),
    queryFn: async (): Promise<EntityContextResponse> => {
      if (!entityId) throw new Error('No entity ID provided');

      const params = new URLSearchParams();
      params.set('hops', hops.toString());
      if (relationshipTypes?.length) {
        relationshipTypes.forEach((type) => params.append('relationship_types', type));
      }

      const encodedId = encodeURIComponent(entityId);
      const response = await apiClient.get(
        'l3',
        `/entity/${encodedId}/context?${params.toString()}`
      );
      return response.data as EntityContextResponse;
    },
    enabled: !!entityId,
    staleTime: STALE_TIME.stats,
  });
}

/**
 * Traverse the value tree from an entity in specified direction.
 * Discovers paths through upstream (value drivers) or downstream (capabilities/use cases) relationships.
 *
 * @returns Mutation for traversing from an entity with direction control
 *
 * @example
 * const mutation = useEntityTraversal();
 * mutation.mutate({ entity_id: 'cap-123', direction: 'up' });
 */
export function useEntityTraversal() {
  return useMutation<EntityTraversalResponse, GraphApiError, EntityTraversalRequest>({
    mutationFn: async (request): Promise<EntityTraversalResponse> => {
      const response = await apiClient.post('l3', '/entity/traverse', {
        entity_id: request.entity_id,
        direction: request.direction ?? 'both',
      });
      return response.data as EntityTraversalResponse;
    },
    onError: (error) => {
      console.error('Entity traversal failed:', error);
    },
  });
}

/**
 * Convenience hook for fetching the full graph (all entities/relationships via empty query).
 * Uses hybrid search with empty query as a workaround until a dedicated /graph endpoint exists.
 *
 * @returns Query result with all nodes (relationships not yet populated - requires entity context queries)
 *
 * @example
 * const { data, isLoading } = useFullGraph();
 * // data.nodes contains all entities from the knowledge graph
 */
export function useFullGraph() {
  return useQuery({
    queryKey: [...QK.graph.all, 'full'],
    queryFn: async (): Promise<ContextGraph> => {
      // Use hybrid search to get all entities, then build a simple graph
      const response = await apiClient.post('l3', '/search/hybrid', {
        query: '',
        search_type: 'hybrid',
        top_k: 100,
      });

      const results: SearchResult[] = response.data?.results || [];
      const nodes: GraphNode[] = results
        .filter((r) => r.id || r.entity_id) // Skip entities without IDs
        .map((r, index) => ({
          id: r.id || r.entity_id || `entity-${index}`,
          name: r.name || r.title || 'Unknown',
          entity_type: r.entity_type || r.type || 'Unknown',
          confidence_score: r.confidence_score ?? r.confidence ?? 0.8,
          description: r.description,
          properties: r.properties || r.data,
        }));

      // For now, return nodes without relationships (would need entity context for each)
      return {
        nodes,
        relationships: [],
      };
    },
    staleTime: STALE_TIME.stats,
  });
}
