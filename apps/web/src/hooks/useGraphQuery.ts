/**
 * useGraphQuery.ts — Data Source Management Hooks for L3 Graph API
 *
 * Provides React Query hooks for graph operations:
 *   - GraphRAG query (POST /v1/query/graph)
 *   - Entity context (GET /v1/entity/{id}/context)
 *   - Entity traversal (POST /v1/entity/traverse)
 *   - Subgraph fetch (GET /v1/graph/subgraph)
 *
 * All hooks perform runtime Zod validation at the trust boundary,
 * then map validated DTOs into domain models before returning.
 *
 * Sprint 5 Migration: Hooks now return domain models from
 * @/features/graph/domain/graph.model instead of raw DTO shapes.
 */

import * as React from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { createLogger } from '@/lib/telemetry';
import { QK } from './queryKeys';
import { STALE_TIME, withApiError, BaseApiError } from './useApiShared';
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
import type {
  GraphNode,
  GraphEdge,
  GraphQueryResult,
  EntityContext,
  GraphTraversalResult,
  GraphSubgraph,
} from '@/features/graph/domain/graph.model';
import {
  mapGraphQueryResponseDtoToDomain,
  mapEntityContextResponseDtoToDomain,
  mapSubgraphResponseDtoToDomain,
} from '@/features/graph/domain/graph.mapper';

const log = createLogger('useGraphQuery');

// ── Request Types ────────────────────────────────────────────────────────────

export interface GraphQueryRequest {
  query: string;
  entity_type?: string;
  max_hops?: number;
  max_results?: number;
}

export interface EntityTraversalRequest {
  entity_id: string;
  direction?: 'up' | 'down' | 'both';
}

export interface SubgraphRequest {
  query?: string;
  centerEntityId?: string;
  depth?: number;
  limit?: number;
}

// ── Error Type ───────────────────────────────────────────────────────────────

export class GraphApiError extends BaseApiError {
  constructor(message: string, statusCode?: number, responseData?: unknown) {
    super(message, statusCode, responseData);
    this.name = 'GraphApiError';
  }
}

// ── Hooks ────────────────────────────────────────────────────────────────────

/**
 * Execute a GraphRAG query with multi-hop traversal.
 * POST /v1/query/graph
 */
export function useGraphQuery() {
  const queryClient = useQueryClient();

  return useMutation<GraphQueryResult, GraphApiError, GraphQueryRequest>({
    mutationFn: async (request): Promise<GraphQueryResult> => {
      const response = await apiClient.post('l3', '/query/graph', {
        query: request.query,
        entity_type: request.entity_type,
        max_hops: request.max_hops ?? 2,
        max_results: request.max_results ?? 20,
      });

      const validated = safeParseResponse(GraphQueryResponseSchema, response.data, 'POST /query/graph');
      if (!validated) {
        throw new GraphApiError('Invalid graph query response format');
      }
      return mapGraphQueryResponseDtoToDomain(validated);
    },
    onSuccess: (data) => {
      data.entities?.forEach((entity) => {
        if (!entity.id) return;
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
 * GET /v1/entity/{entity_id}/context
 */
export function useEntityContext(
  entityId: string | null,
  hops: number = 2,
  relationshipTypes?: string[]
) {
  return useQuery({
    queryKey: QK.graph.context(entityId || '', hops),
    queryFn: async (): Promise<EntityContext> => {
      if (!entityId) throw new Error('No entity ID provided');

      const params = new URLSearchParams();
      params.set('hops', hops.toString());
      if (relationshipTypes?.length) {
        relationshipTypes.forEach((type) => params.append('relationship_types', type));
      }

      const encodedId = encodeURIComponent(entityId);
      const response = await apiClient.get('l3', `/entity/${encodedId}/context?${params.toString()}`);

      const validated = safeParseResponse(
        EntityContextResponseSchema,
        response.data,
        `GET /entity/${entityId}/context`
      );
      if (!validated) {
        throw new Error('Invalid entity context response format');
      }
      return mapEntityContextResponseDtoToDomain(validated);
    },
    enabled: !!entityId,
    staleTime: STALE_TIME.stats,
  });
}

/**
 * Traverse the value tree from an entity in specified direction.
 * POST /v1/entity/traverse
 */
export function useEntityTraversal() {
  return useMutation<GraphTraversalResult, GraphApiError, EntityTraversalRequest>({
    mutationFn: async (request): Promise<GraphTraversalResult> => {
      const response = await apiClient.post('l3', '/entity/traverse', {
        entity_id: request.entity_id,
        direction: request.direction ?? 'both',
      });

      const validated = safeParseResponse(
        EntityTraversalResponseSchema,
        response.data,
        'POST /entity/traverse'
      );
      if (!validated) {
        throw new GraphApiError('Invalid entity traversal response format');
      }

      // Map to domain model
      return {
        startEntityId: validated.start_entity_id,
        direction: validated.direction,
        paths: validated.paths.map((path) => ({
          nodes: path.nodes.map((n) => ({
            id: n.id,
            name: n.name,
            entityType: n.entity_type,
            confidenceScore: n.confidence_score,
            description: n.description,
            properties: n.properties,
          })),
          edges: path.relationships.map((e) => ({
            sourceId: e.source,
            targetId: e.target,
            relationshipType: e.type,
            weight: e.confidence ?? 1.0,
            properties: e.properties,
          })),
          valueScore: path.value_score,
        })),
        pathCount: validated.path_count,
      };
    },
    onError: (error) => {
      log.error('Entity traversal failed', { error: error instanceof Error ? error.message : error });
    },
  });
}

/**
 * Fetch a coherent subgraph from the backend.
 * GET /v1/graph/subgraph
 */
export function useSubgraph(options: SubgraphRequest) {
  const { query, centerEntityId, depth = 2, limit = 100 } = options;

  return useQuery({
    queryKey: QK.graph.subgraph(query, centerEntityId, depth, limit),
    queryFn: async (): Promise<GraphSubgraph> => {
      const params = new URLSearchParams();
      if (query) params.set('query', query);
      if (centerEntityId) params.set('center_entity_id', centerEntityId);
      params.set('depth', depth.toString());
      params.set('limit', limit.toString());

      const response = await apiClient.get('l3', `/subgraph?${params.toString()}`);

      const validated = validateOrThrow(SubgraphResponseSchema, response.data, 'SubgraphResponse');
      return mapSubgraphResponseDtoToDomain(validated);
    },
    enabled: query !== undefined || !!centerEntityId,
    staleTime: STALE_TIME.stats,
  });
}

/**
 * @deprecated Use useSubgraph instead for coherent graph data.
 */
export function useFullGraph() {
  return useSubgraph({ query: '', depth: 2, limit: 100 });
}

// ── Re-export Domain Types for Convenience ───────────────────────────────────

export type { GraphNode, GraphEdge, GraphQueryResult, EntityContext, GraphSubgraph } from '@/features/graph/domain/graph.model';

// ── View State (kept here for backward compat) ───────────────────────────────

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
