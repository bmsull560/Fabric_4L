/**
 * useGraphQuery Hook Tests
 *
 * Tests for Knowledge Graph query hooks including:
 * - useGraphQuery: GraphRAG mutation for complex queries
 * - useEntityContext: Neighborhood context queries
 * - useEntityTraversal: Value tree traversal
 * - useFullGraph: Full graph retrieval
 */
import { describe, it, expect, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import {
  useGraphQuery,
  useEntityContext,
  useEntityTraversal,
  useFullGraph,
} from './useGraphQuery';

beforeEach(() => {
  server.resetHandlers();
});

// Shared mock data factory for GraphNode consistency
const createMockNode = (id: string, name: string, entity_type: string, confidence_score: number) => ({
  id, name, entity_type, confidence_score
});

describe('useGraphQuery', () => {
  it('executes graph query successfully', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useGraphQuery(), { wrapper });

    // Execute the mutation
    result.current.mutate({ query: 'Find capabilities', max_hops: 2 });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBeDefined();
    expect(result.current.data?.entities).toBeDefined();
    expect(result.current.data?.confidence_score).toBeGreaterThan(0);
  });

  it('handles query errors', async () => {
    // Override handler for this test
    server.use(
      http.post('/api/v1/graph/query/graph', () => {
        return HttpResponse.json({ error: 'Query timeout' }, { status: 504 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useGraphQuery(), { wrapper });

    result.current.mutate({ query: 'Timeout query' });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBeDefined();
    });
  });

  it('caches entities from response', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useGraphQuery(), { wrapper });

    result.current.mutate({ query: 'Cache test', max_results: 5 });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Data should be available and structured correctly
    expect(result.current.data?.entities).toBeInstanceOf(Array);
  });
});

describe('useEntityContext', () => {
  it('fetches entity context with default hops', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useEntityContext('entity-1'), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.center).toBeDefined();
    expect(result.current.data?.neighbors).toBeInstanceOf(Array);
    expect(result.current.data?.relationships).toBeInstanceOf(Array);
  });

  it('fetches entity context with custom hops', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useEntityContext('entity-1', 3), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.entity_count).toBeGreaterThan(0);
  });

  it('disables query when entityId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useEntityContext(null), { wrapper });

    // Should not be loading or fetching
    expect(result.current.isLoading).toBe(false);
    expect(result.current.fetchStatus).toBe('idle');
  });

  it('handles entity not found', async () => {
    // Override handler for this test
    server.use(
      http.get('/api/v1/graph/entity/:entityId/context', () => {
        return HttpResponse.json({ error: 'Entity not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useEntityContext('non-existent'), { wrapper });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBeDefined();
    });
  });
});

describe('useEntityTraversal', () => {
  it('traverses value tree', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useEntityTraversal(), { wrapper });

    result.current.mutate({ entity_id: 'entity-1', direction: 'down' });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.paths).toBeInstanceOf(Array);
    expect(result.current.data?.path_count).toBeGreaterThanOrEqual(0);
  });

  it('handles traversal errors', async () => {
    // Override handler for this test
    server.use(
      http.post('/api/v1/graph/entity/traverse', () => {
        return HttpResponse.json({ error: 'Invalid direction' }, { status: 400 });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useEntityTraversal(), { wrapper });

    result.current.mutate({ entity_id: 'bad-entity', direction: 'invalid' as 'up' });

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
      expect(result.current.error).toBeDefined();
    });
  });
});

describe('useFullGraph', () => {
  it('fetches full graph data', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(() => useFullGraph(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.nodes).toBeInstanceOf(Array);
    expect(result.current.data?.edges).toBeInstanceOf(Array);
  });

  it('returns coherent subgraph with nodes and edges', async () => {
    // Override handler for this test
    server.use(
      http.get('/api/v1/graph/subgraph', () => {
        return HttpResponse.json({
          root_entity_id: '',
          nodes: [
            createMockNode('ent-1', 'Entity One', 'Capability', 0.95),
            createMockNode('ent-2', 'Entity Two', 'UseCase', 0.88),
          ],
          edges: [
            { source: 'ent-1', target: 'ent-2', type: 'ENABLES' },
          ],
          depth: 2,
          stats: { total_nodes: 2, total_edges: 1, density: 0.5 },
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFullGraph(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Should return coherent graph with both nodes AND edges
    expect(result.current.data?.nodes).toHaveLength(2);
    expect(result.current.data?.edges).toHaveLength(1);
    expect(result.current.data?.edges[0].source).toBe('ent-1');
    expect(result.current.data?.edges[0].target).toBe('ent-2');
  });

  it('handles empty subgraph', async () => {
    // Override handler for this test
    server.use(
      http.get('/api/v1/graph/subgraph', () => {
        return HttpResponse.json({
          root_entity_id: '',
          nodes: [],
          edges: [],
          depth: 2,
          stats: { total_nodes: 0, total_edges: 0, density: 0 },
        });
      })
    );

    const wrapper = createWrapper();
    const { result } = renderHook(() => useFullGraph(), { wrapper });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data?.nodes).toHaveLength(0);
    expect(result.current.data?.edges).toHaveLength(0);
  });
});
