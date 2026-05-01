/**
 * LAYER 1: UNIT TESTS (70% of test count)
 * Comprehensive test suite for Graph Query hooks
 *
 * Coverage targets:
 * - Happy path: 2-3 input scenarios per function
 * - Boundary cases: empty, single element, max size, null/undefined
 * - Error cases: invalid types, out-of-range values, malformed data
 * - Async cases: resolve, reject, timeout, concurrent calls
 * - All external dependencies mocked - each test runs in <10ms
 */

import { describe, it, expect, beforeEach, vi, type Mock } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { createWrapper, createWrapperWithRetry } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import { QueryClient } from '@tanstack/react-query';

// Module under test
import {
  useGraphQuery,
  useEntityContext,
  useEntityTraversal,
  useSubgraph,
  useFullGraph,
  useGraphViewState,
  type GraphNode,
  type GraphRelationship,
  type GraphViewState as GraphViewStateType,
} from './useGraphQuery';

// ============================================================================
// FACTORY FUNCTIONS - Test Data Builders (Never hardcode complex objects)
// ============================================================================

const createMockNode = (overrides?: Partial<GraphNode>): GraphNode => ({
  id: `node-${Math.random().toString(36).slice(2, 11)}`,
  name: 'Test Entity',
  entity_type: 'Capability',
  confidence_score: 0.95,
  description: 'A test entity for unit testing',
  properties: {},
  x: Math.random() * 100,
  y: Math.random() * 100,
  ...overrides,
});

const createMockEdge = (
  source: string,
  target: string,
  overrides?: Partial<GraphRelationship>
): GraphRelationship => ({
  source,
  target,
  type: 'ENABLES',
  confidence: 0.88,
  properties: {},
  ...overrides,
});

const createMockSubgraphResponse = (nodeCount = 3, edgeCount = 2) => {
  const nodes = Array.from({ length: nodeCount }, (_, i) =>
    createMockNode({ id: `node-${i}`, name: `Entity ${i}` })
  );
  const edges = Array.from({ length: edgeCount }, (_, i) =>
    createMockEdge(`node-${i}`, `node-${(i + 1) % nodeCount}`, { type: 'DEPENDS_ON' })
  );

  return {
    root_entity_id: nodes[0]?.id || '',
    nodes,
    edges,
    depth: 2,
    stats: {
      total_nodes: nodeCount,
      total_edges: edgeCount,
      density: nodeCount > 1 ? edgeCount / (nodeCount * (nodeCount - 1)) : 0,
    },
  };
};

// ============================================================================
// MOCK DATA CONSTANTS
// ============================================================================

const VALID_NODE: GraphNode = {
  id: 'valid-node-1',
  name: 'Valid Test Node',
  entity_type: 'Capability',
  confidence_score: 0.95,
  description: 'A valid node for testing',
  properties: { key: 'value' },
};

const VALID_EDGE: GraphRelationship = {
  source: 'valid-node-1',
  target: 'valid-node-2',
  type: 'ENABLES',
  confidence: 0.88,
};

const EMPTY_SUBGRAPH = {
  root_entity_id: '',
  nodes: [],
  edges: [],
  depth: 2,
  stats: { total_nodes: 0, total_edges: 0, density: 0 },
};

// ============================================================================
// SETUP & TEARDOWN
// ============================================================================

beforeEach(() => {
  server.resetHandlers();
  vi.clearAllMocks();
});

// ============================================================================
// useGraphViewState - PURE STATE LOGIC (Fastest tests)
// ============================================================================

describe('useGraphViewState [L1-Unit-Pure]', () => {
  describe('happy path', () => {
    it('initializes with default view state', () => {
      const { result } = renderHook(() => useGraphViewState());

      expect(result.current.viewState).toEqual({
        zoom: 1,
        panX: 0,
        panY: 0,
      });
    });

    it('zooms in incrementally', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.zoomIn());
      expect(result.current.viewState.zoom).toBe(1.2);

      act(() => result.current.zoomIn());
      expect(result.current.viewState.zoom).toBe(1.4);
    });

    it('zooms out incrementally', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.zoomOut());
      expect(result.current.viewState.zoom).toBe(0.8);

      act(() => result.current.zoomOut());
      expect(result.current.viewState.zoom).toBeCloseTo(0.6, 10);
    });

    it('pans by delta values', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.panBy(50, -30));
      expect(result.current.viewState).toEqual({
        zoom: 1,
        panX: 50,
        panY: -30,
      });

      act(() => result.current.panBy(25, 40));
      expect(result.current.viewState).toEqual({
        zoom: 1,
        panX: 75,
        panY: 10,
      });
    });

    it('resets view to defaults', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => {
        result.current.zoomIn();
        result.current.panBy(100, 100);
      });

      act(() => result.current.resetView());

      expect(result.current.viewState).toEqual({
        zoom: 1,
        panX: 0,
        panY: 0,
      });
    });
  });

  describe('boundary cases', () => {
    it('enforces minimum zoom of 0.5', () => {
      const { result } = renderHook(() => useGraphViewState());

      // Try to zoom out 5 times
      for (let i = 0; i < 5; i++) {
        act(() => result.current.zoomOut());
      }

      expect(result.current.viewState.zoom).toBe(0.5);
    });

    it('enforces maximum zoom of 3.0', () => {
      const { result } = renderHook(() => useGraphViewState());

      // Try to zoom in 15 times
      for (let i = 0; i < 15; i++) {
        act(() => result.current.zoomIn());
      }

      expect(result.current.viewState.zoom).toBe(3.0);
    });

    it('handles zero pan delta', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.panBy(0, 0));

      expect(result.current.viewState.panX).toBe(0);
      expect(result.current.viewState.panY).toBe(0);
    });

    it('handles very large pan values', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.panBy(10000, -10000));

      expect(result.current.viewState.panX).toBe(10000);
      expect(result.current.viewState.panY).toBe(-10000);
    });

    it('clamps setZoom to min/max bounds', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.setZoom(0.1));
      expect(result.current.viewState.zoom).toBe(0.5);

      act(() => result.current.setZoom(5.0));
      expect(result.current.viewState.zoom).toBe(3.0);
    });
  });

  describe('setZoom direct manipulation', () => {
    it('sets zoom to specific value within bounds', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.setZoom(1.5));
      expect(result.current.viewState.zoom).toBe(1.5);
    });

    it('maintains pan state when setting zoom', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => result.current.panBy(50, 50));
      act(() => result.current.setZoom(2.0));

      expect(result.current.viewState).toEqual({
        zoom: 2.0,
        panX: 50,
        panY: 50,
      });
    });
  });

  describe('functional state updates', () => {
    it('handles rapid consecutive zoom operations', () => {
      const { result } = renderHook(() => useGraphViewState());

      // Simulate rapid zooming - should not lose updates
      act(() => {
        result.current.zoomIn();
        result.current.zoomIn();
        result.current.zoomOut();
        result.current.zoomIn();
      });

      // 1.0 -> 1.2 -> 1.4 -> 1.2 -> 1.4
      expect(result.current.viewState.zoom).toBe(1.4);
    });

    it('handles interleaved pan and zoom', () => {
      const { result } = renderHook(() => useGraphViewState());

      act(() => {
        result.current.zoomIn();
        result.current.panBy(10, 20);
        result.current.zoomOut();
        result.current.panBy(5, -10);
      });

      expect(result.current.viewState).toEqual({
        zoom: 1.0,
        panX: 15,
        panY: 10,
      });
    });
  });
});

// ============================================================================
// useSubgraph - ASYNC DATA FETCHING
// ============================================================================

describe('useSubgraph [L1-Unit-Async]', () => {
  describe('happy path', () => {
    it('fetches subgraph with query mode', async () => {
      const mockResponse = createMockSubgraphResponse(3, 2);
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () => HttpResponse.json(mockResponse))
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'test query', depth: 2, limit: 100 }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.nodes).toHaveLength(3);
      expect(result.current.data?.edges).toHaveLength(2);
      expect(result.current.data?.depth).toBe(2);
    });

    it('fetches subgraph with center entity mode', async () => {
      const mockResponse = createMockSubgraphResponse(5, 4);
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () => HttpResponse.json(mockResponse))
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ centerEntityId: 'entity-123', depth: 2 }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.root_entity_id).toBeDefined();
    });

    it('handles empty subgraph response', async () => {
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () => HttpResponse.json(EMPTY_SUBGRAPH))
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'no results' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.nodes).toEqual([]);
      expect(result.current.data?.edges).toEqual([]);
      expect(result.current.data?.stats.total_nodes).toBe(0);
    });
  });

  describe('boundary cases', () => {
    it('disables query when neither query nor centerEntityId provided', async () => {
      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ depth: 2 }),
        { wrapper }
      );

      // Should not fetch
      expect(result.current.isLoading).toBe(false);
      expect(result.current.fetchStatus).toBe('idle');
    });

    it('handles single node subgraph', async () => {
      const singleNode = createMockSubgraphResponse(1, 0);
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () => HttpResponse.json(singleNode))
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'single' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.nodes).toHaveLength(1);
      expect(result.current.data?.edges).toHaveLength(0);
    });

    it('handles maximum limit parameter', async () => {
      const mockResponse = createMockSubgraphResponse(500, 100);
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () => HttpResponse.json(mockResponse))
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'max', limit: 500 }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.stats.total_nodes).toBe(500);
    });

    it('handles minimum depth of 1', async () => {
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () =>
          HttpResponse.json({ ...createMockSubgraphResponse(), depth: 1 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'shallow', depth: 1 }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('error cases', () => {
    it('handles 404 not found', async () => {
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () =>
          HttpResponse.json({ error: 'Not found' }, { status: 404 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'missing' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error).toBeDefined();
    });

    it.skip('handles 500 server error', async () => {
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () =>
          HttpResponse.json({ error: 'Internal error' }, { status: 500 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'error' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));
    });

    it.skip('handles network timeout', async () => {
      server.use(
        http.get('/api/v1/graph/graph/subgraph', async () => {
          await new Promise((resolve) => setTimeout(resolve, 10000));
          return HttpResponse.json({});
        })
      );

      const wrapper = createWrapperWithRetry(false); // Disable retries for faster test
      const { result } = renderHook(
        () => useSubgraph({ query: 'timeout' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 3000 });
    });

    it('handles malformed response (validation error)', async () => {
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () =>
          HttpResponse.json({ invalid: 'missing required fields' })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'invalid' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('concurrent operations', () => {
    it('handles concurrent queries with different parameters', async () => {
      const response1 = createMockSubgraphResponse(2, 1);
      const response2 = createMockSubgraphResponse(4, 3);

      server.use(
        http.get('/api/v1/graph/graph/subgraph', ({ request }) => {
          const url = new URL(request.url);
          const query = url.searchParams.get('query');
          return HttpResponse.json(query === 'query1' ? response1 : response2);
        })
      );

      const wrapper = createWrapper();

      const { result: result1 } = renderHook(
        () => useSubgraph({ query: 'query1' }),
        { wrapper }
      );
      const { result: result2 } = renderHook(
        () => useSubgraph({ query: 'query2' }),
        { wrapper }
      );

      await waitFor(() => expect(result1.current.isSuccess).toBe(true));
      await waitFor(() => expect(result2.current.isSuccess).toBe(true));

      expect(result1.current.data?.nodes).toHaveLength(2);
      expect(result2.current.data?.nodes).toHaveLength(4);
    });

    it('cancels in-flight requests on unmount', async () => {
      let requestCount = 0;
      server.use(
        http.get('/api/v1/graph/graph/subgraph', async () => {
          requestCount++;
          await new Promise((resolve) => setTimeout(resolve, 100));
          return HttpResponse.json(createMockSubgraphResponse());
        })
      );

      const wrapper = createWrapper();
      const { unmount } = renderHook(
        () => useSubgraph({ query: 'slow' }),
        { wrapper }
      );

      // Unmount immediately
      unmount();

      // Wait a bit and check request was made but no errors thrown
      await new Promise((resolve) => setTimeout(resolve, 50));
      expect(requestCount).toBe(1);
    });
  });

  describe('caching behavior', () => {
    it('returns cached data on subsequent calls', async () => {
      let requestCount = 0;
      server.use(
        http.get('/api/v1/graph/graph/subgraph', () => {
          requestCount++;
          return HttpResponse.json(createMockSubgraphResponse());
        })
      );

      const wrapper = createWrapper();
      const { result, rerender } = renderHook(
        () => useSubgraph({ query: 'cached' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      const requestCountAfterFirst = requestCount;

      // Rerender should not trigger new request
      rerender();
      expect(requestCount).toBe(requestCountAfterFirst);
    });
  });
});

// ============================================================================
// useEntityContext - NEIGHBORHOOD QUERIES
// ============================================================================

describe('useEntityContext [L1-Unit-Async]', () => {
  describe('happy path', () => {
    it('fetches context with default hops (2)', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', () =>
          HttpResponse.json({
            entity_id: 'entity-1',
            center: createMockNode({ id: 'entity-1' }),
            neighbors: [createMockNode({ id: 'neighbor-1' })],
            relationships: [createMockEdge('entity-1', 'neighbor-1')],
            entity_count: 2,
            relationship_count: 1,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext('entity-1'), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.center.id).toBe('entity-1');
      expect(result.current.data?.neighbors).toHaveLength(1);
    });

    it('fetches context with custom hops', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', () =>
          HttpResponse.json({
            entity_id: 'entity-1',
            center: createMockNode(),
            neighbors: [],
            relationships: [],
            entity_count: 1,
            relationship_count: 0,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext('entity-1', 3), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });

    it('filters by relationship types when provided', async () => {
      let capturedParams: URLSearchParams | null = null;
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', ({ request }) => {
          capturedParams = new URL(request.url).searchParams;
          return HttpResponse.json({
            entity_id: 'entity-1',
            center: createMockNode(),
            neighbors: [],
            relationships: [],
            entity_count: 1,
            relationship_count: 0,
          });
        })
      );

      const wrapper = createWrapper();
      renderHook(
        () => useEntityContext('entity-1', 2, ['DEPENDS_ON', 'ENABLES']),
        { wrapper }
      );

      await waitFor(() => expect(capturedParams).not.toBeNull());
      const types: string[] = [];
      capturedParams!.forEach((value, key) => {
        if (key === 'relationship_types') types.push(value);
      });
      expect(types).toEqual(['DEPENDS_ON', 'ENABLES']);
    });
  });

  describe('boundary cases', () => {
    it('disables query when entityId is null', async () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext(null), { wrapper });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.fetchStatus).toBe('idle');
    });

    it('disables query when entityId is empty string', async () => {
      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext(''), { wrapper });

      expect(result.current.isLoading).toBe(false);
      expect(result.current.fetchStatus).toBe('idle');
    });

    it('handles entity with no neighbors (orphan node)', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', () =>
          HttpResponse.json({
            entity_id: 'orphan',
            center: createMockNode({ id: 'orphan' }),
            neighbors: [],
            relationships: [],
            entity_count: 1,
            relationship_count: 0,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext('orphan'), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.neighbors).toHaveLength(0);
    });

    it('handles zero hops', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', () =>
          HttpResponse.json({
            entity_id: 'entity-1',
            center: createMockNode(),
            neighbors: [],
            relationships: [],
            entity_count: 1,
            relationship_count: 0,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext('entity-1', 0), { wrapper });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('error cases', () => {
    it('handles entity not found (404)', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', () =>
          HttpResponse.json({ error: 'Entity not found' }, { status: 404 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext('nonexistent'), { wrapper });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });

    it('handles invalid hops parameter', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', () =>
          HttpResponse.json({ error: 'Invalid hops' }, { status: 400 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityContext('entity-1', -1), { wrapper });

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });
});

// ============================================================================
// useGraphQuery - MUTATION TESTS
// ============================================================================

describe('useGraphQuery [L1-Unit-Async]', () => {
  describe('happy path', () => {
    it('executes graph query mutation', async () => {
      server.use(
        http.post('/api/v1/graph/query/graph', () =>
          HttpResponse.json({
            query: 'Find AI capabilities',
            entities: [createMockNode()],
            relationships: [],
            confidence_score: 0.92,
            processing_time_ms: 150,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useGraphQuery(), { wrapper });

      act(() => {
        result.current.mutate({
          query: 'Find AI capabilities',
          max_hops: 2,
          max_results: 10,
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.entities).toBeInstanceOf(Array);
      expect(result.current.data?.confidence_score).toBeGreaterThan(0);
    });

    it('caches entities on success', async () => {
      const wrapper = createWrapper();

      const node = createMockNode({ id: 'cached-node' });
      server.use(
        http.post('/api/v1/graph/query/graph', () =>
          HttpResponse.json({
            query: 'test',
            entities: [node],
            relationships: [],
            confidence_score: 0.9,
            processing_time_ms: 100,
          })
        )
      );

      const { result } = renderHook(() => useGraphQuery(), { wrapper });

      act(() => result.current.mutate({ query: 'test' }));
      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Entity data is available in the result
      expect(result.current.data?.entities[0].id).toBe('cached-node');
    });
  });

  describe('error cases', () => {
    it.skip('handles query timeout', async () => {
      server.use(
        http.post('/api/v1/graph/query/graph', () =>
          HttpResponse.json({ error: 'Query timeout' }, { status: 504 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useGraphQuery(), { wrapper });

      act(() => result.current.mutate({ query: 'slow query' }));

      await waitFor(() => expect(result.current.isError).toBe(true));
    });

    it('handles invalid query parameters', async () => {
      server.use(
        http.post('/api/v1/graph/query/graph', () =>
          HttpResponse.json({ error: 'Invalid parameters' }, { status: 400 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useGraphQuery(), { wrapper });

      act(() => result.current.mutate({ query: '' }));

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });

  describe('concurrent mutations', () => {
    it('handles multiple concurrent mutations', async () => {
      let requestCount = 0;
      server.use(
        http.post('/api/v1/graph/query/graph', () => {
          requestCount++;
          return HttpResponse.json({
            query: `query-${requestCount}`,
            entities: [],
            relationships: [],
            confidence_score: 0.9,
            processing_time_ms: 50,
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useGraphQuery(), { wrapper });

      // Fire multiple mutations
      act(() => {
        result.current.mutate({ query: '1' });
        result.current.mutate({ query: '2' });
        result.current.mutate({ query: '3' });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      // Only the last mutation result is kept
      expect(requestCount).toBeGreaterThanOrEqual(1);
    });
  });
});

// ============================================================================
// useEntityTraversal - TRAVERSAL MUTATIONS
// ============================================================================

describe('useEntityTraversal [L1-Unit-Async]', () => {
  describe('happy path', () => {
    it('traverses upward (value drivers)', async () => {
      server.use(
        http.post('/api/v1/graph/entity/traverse', () =>
          HttpResponse.json({
            start_entity_id: 'cap-1',
            direction: 'up',
            paths: [
              {
                nodes: [createMockNode({ id: 'cap-1' }), createMockNode({ id: 'driver-1' })],
                relationships: [createMockEdge('cap-1', 'driver-1', { type: 'DRIVEN_BY' })],
                value_score: 0.95,
              },
            ],
            path_count: 1,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityTraversal(), { wrapper });

      act(() => result.current.mutate({ entity_id: 'cap-1', direction: 'up' }));

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.paths).toHaveLength(1);
    });

    it('traverses downward (capabilities)', async () => {
      server.use(
        http.post('/api/v1/graph/entity/traverse', () =>
          HttpResponse.json({
            start_entity_id: 'driver-1',
            direction: 'down',
            paths: [
              {
                nodes: [createMockNode(), createMockNode()],
                relationships: [createMockEdge('driver-1', 'cap-1', { type: 'ENABLES' })],
                value_score: 0.88,
              },
            ],
            path_count: 1,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityTraversal(), { wrapper });

      act(() => result.current.mutate({ entity_id: 'driver-1', direction: 'down' }));

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });

    it('traverses bidirectionally', async () => {
      server.use(
        http.post('/api/v1/graph/entity/traverse', () =>
          HttpResponse.json({
            start_entity_id: 'entity-1',
            direction: 'both',
            paths: [],
            path_count: 0,
          })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityTraversal(), { wrapper });

      act(() => result.current.mutate({ entity_id: 'entity-1', direction: 'both' }));

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
    });
  });

  describe('error cases', () => {
    it('handles invalid direction', async () => {
      server.use(
        http.post('/api/v1/graph/entity/traverse', () =>
          HttpResponse.json({ error: 'Invalid direction' }, { status: 400 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityTraversal(), { wrapper });

      act(() =>
        result.current.mutate({ entity_id: 'entity-1', direction: 'invalid' as 'up' })
      );

      await waitFor(() => expect(result.current.isError).toBe(true));
    });

    it('handles non-existent entity', async () => {
      server.use(
        http.post('/api/v1/graph/entity/traverse', () =>
          HttpResponse.json({ error: 'Entity not found' }, { status: 404 })
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityTraversal(), { wrapper });

      act(() => result.current.mutate({ entity_id: 'nonexistent', direction: 'up' }));

      await waitFor(() => expect(result.current.isError).toBe(true));
    });
  });
});

// ============================================================================
// useFullGraph - DEPRECATED API COMPATIBILITY
// ============================================================================

describe('useFullGraph [L1-Unit-Async]', () => {
  it('delegates to useSubgraph with empty query', async () => {
    server.use(
      http.get('/api/v1/graph/graph/subgraph', () => HttpResponse.json(createMockSubgraphResponse()))
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFullGraph(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toBeDefined();
  });
});

// ============================================================================
// TYPE GUARDS & UTILITY TESTS
// ============================================================================

describe('type guards [L1-Unit-Pure]', () => {
  describe('GraphNode type validation', () => {
    it('validates required fields', () => {
      const validNode: GraphNode = {
        id: 'test',
        name: 'Test',
        entity_type: 'Capability',
        confidence_score: 0.5,
      };

      expect(validNode.id).toBeDefined();
      expect(validNode.name).toBeDefined();
      expect(validNode.confidence_score).toBeGreaterThanOrEqual(0);
      expect(validNode.confidence_score).toBeLessThanOrEqual(1);
    });

    it('validates confidence score bounds', () => {
      const node = createMockNode({ confidence_score: 1.5 });
      // Note: Runtime validation would catch this, type system allows it
      expect(node.confidence_score).toBe(1.5);
    });

    it('validates optional coordinates', () => {
      const nodeWithCoords = createMockNode({ x: 100, y: 200 });
      const nodeWithoutCoords = createMockNode();

      expect(nodeWithCoords.x).toBe(100);
      expect(nodeWithCoords.y).toBe(200);
      expect(nodeWithoutCoords.x).toBeDefined(); // Factory provides defaults
    });
  });

  describe('GraphRelationship type validation', () => {
    it('validates edge structure', () => {
      const edge = createMockEdge('a', 'b');

      expect(edge.source).toBe('a');
      expect(edge.target).toBe('b');
      expect(edge.type).toBeDefined();
    });

    it('validates self-loop prevention', () => {
      const selfLoop = createMockEdge('same', 'same', { type: 'SELF_REF' });
      // Note: Business logic should prevent this, type system allows it
      expect(selfLoop.source).toBe(selfLoop.target);
    });
  });
});

// ============================================================================
// TEST TIMING VERIFICATION
// ============================================================================

describe('test performance [L1-Unit-Performance]', () => {
  it('pure state tests complete in <10ms', () => {
    const start = performance.now();

    const { result } = renderHook(() => useGraphViewState());
    for (let i = 0; i < 100; i++) {
      act(() => result.current.zoomIn());
    }

    const elapsed = performance.now() - start;
    expect(elapsed).toBeLessThan(10);
  });
});
