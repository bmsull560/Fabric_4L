import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { createLogger } from '@/lib/telemetry';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';
import {
  GraphQueryResponseSchema,
  EntityContextResponseSchema,
  EntityTraversalResponseSchema,
  safeParseResponse,
} from '@/lib/schemas';
import {
  SubgraphResponseSchema,
  validateOrThrow,
} from '@/lib/validation/schemas';

const log = createLogger('useGraphQuery');

export interface GraphNode {
  id: string;
  name: string;
  entity_type: string;
  confidence_score: number;
  description?: string;
  properties?: Record<string, unknown>;
  /** Optional layout coordinates (added by calculateLayout) */
  x?: number;
  y?: number;
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
      log.error('GraphRAG query failed', { error: error instanceof Error ? error.message : error });
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

      // Runtime validation with Zod
      const validated = safeParseResponse(EntityContextResponseSchema, response.data, `GET /entity/${entityId}/context`);
      if (!validated) {
        throw new Error('Invalid entity context response format');
      }
      return validated;
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

      // Runtime validation with Zod
      const validated = safeParseResponse(EntityTraversalResponseSchema, response.data, 'POST /entity/traverse');
      if (!validated) {
        throw new Error('Invalid entity traversal response format');
      }
      return validated;
    },
    onError: (error) => {
      log.error('Entity traversal failed', { error: error instanceof Error ? error.message : error });
    },
  });
}

export interface SubgraphResponse {
  root_entity_id: string;
  nodes: GraphNode[];
  edges: GraphRelationship[];
  depth: number;
  stats: {
    total_nodes: number;
    total_edges: number;
    density: number;
  };
}

/**
 * Fetch a coherent subgraph from the backend.
 *
 * ## Contract Guarantees
 * - **Coherent**: All edges connect nodes in the response (no orphan edges)
 * - **Deterministic**: Same query returns identical graph structure (same dataset)
 * - **Bounded**: Respects depth (1-3) and limit (1-500) parameters
 * - **Complete**: Returns empty arrays, never null/undefined
 *
 * ## Modes
 * - **Query mode** (`query`): Searches for matching entities, returns 1-hop subgraph
 * - **Center mode** (`centerEntityId`): Expands N hops from specific entity
 *
 * ## Response Structure
 * ```typescript
 * {
 *   root_entity_id: string;      // Empty for query mode
 *   nodes: GraphNode[];          // All nodes in subgraph
 *   edges: GraphRelationship[];  // All edges between returned nodes
 *   depth: number;               // Actual traversal depth used
 *   stats: {
 *     total_nodes: number;       // Node count
 *     total_edges: number;       // Edge count
 *     density: number;           // Graph density (0.0-1.0)
 *   }
 * }
 * ```
 *
 * ## Example
 * ```typescript
 * // Query mode - search for entities
 * const { data, isLoading } = useSubgraph({
 *   query: "AI processing",
 *   depth: 2,
 *   limit: 100
 * });
 *
 * // Center mode - expand from specific entity
 * const { data } = useSubgraph({
 *   centerEntityId: "cap-123",
 *   depth: 2
 * });
 * ```
 *
 * ## Performance
 * - Single API call (no N+1 queries)
 * - Response time ~100-300ms typical
 * - Frontend is pure renderer (no client-side assembly)
 *
 * @param options.query - Search string for query mode
 * @param options.centerEntityId - Entity ID for center expansion mode
 * @param options.depth - Traversal depth 1-3 (default: 2)
 * @param options.limit - Max nodes 1-500 (default: 100)
 * @returns Subgraph with coherent nodes, edges, and statistics
 */
export function useSubgraph(options: {
  query?: string;
  centerEntityId?: string;
  depth?: number;
  limit?: number;
}) {
  const { query, centerEntityId, depth = 2, limit = 100 } = options;

  return useQuery({
    queryKey: QK.graph.subgraph(query, centerEntityId, depth, limit),
    queryFn: async (): Promise<SubgraphResponse> => {
      // Build query params
      const params = new URLSearchParams();
      if (query) params.set('query', query);
      if (centerEntityId) params.set('center_entity_id', centerEntityId);
      params.set('depth', depth.toString());
      params.set('limit', limit.toString());

      const response = await apiClient.get('l3', `/subgraph?${params.toString()}`);

      // Validate response with Zod schema
      const validated = validateOrThrow(SubgraphResponseSchema, response.data, 'SubgraphResponse');

      return validated;
    },
    enabled: query !== undefined || !!centerEntityId,
    staleTime: STALE_TIME.stats,
  });
}

/**
 * @deprecated Use useSubgraph instead for coherent graph data.
 * Kept for backward compatibility during transition.
 */
export function useFullGraph() {
  return useSubgraph({ query: '', depth: 2, limit: 100 });
}

/** Zoom and pan state for graph visualization */
export interface GraphViewState {
  zoom: number;
  panX: number;
  panY: number;
}

const DEFAULT_VIEW_STATE: GraphViewState = {
  zoom: 1,
  panX: 0,
  panY: 0,
};

const MIN_ZOOM = 0.5;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.2;

/**
 * Hook for managing graph zoom and pan state.
 * Provides controls for zooming, panning, and resetting the view.
 *
 * @example
 * const { viewState, zoomIn, zoomOut, resetView, panBy } = useGraphViewState();
 */
export function useGraphViewState() {
  const [viewState, setViewState] = React.useState<GraphViewState>(DEFAULT_VIEW_STATE);

  const zoomIn = React.useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      zoom: Math.min(prev.zoom + ZOOM_STEP, MAX_ZOOM),
    }));
  }, []);

  const zoomOut = React.useCallback(() => {
    setViewState((prev) => ({
      ...prev,
      zoom: Math.max(prev.zoom - ZOOM_STEP, MIN_ZOOM),
    }));
  }, []);

  const resetView = React.useCallback(() => {
    setViewState(DEFAULT_VIEW_STATE);
  }, []);

  const panBy = React.useCallback((dx: number, dy: number) => {
    setViewState((prev) => ({
      ...prev,
      panX: prev.panX + dx,
      panY: prev.panY + dy,
    }));
  }, []);

  const setZoom = React.useCallback((zoom: number) => {
    setViewState((prev) => ({
      ...prev,
      zoom: Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, zoom)),
    }));
  }, []);

  return {
    viewState,
    zoomIn,
    zoomOut,
    resetView,
    panBy,
    setZoom,
  };
}
