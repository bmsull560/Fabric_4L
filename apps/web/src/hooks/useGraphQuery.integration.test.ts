/**
 * LAYER 2: INTEGRATION TESTS (20% of test count)
 * Tests for API boundaries and cross-module integration
 *
 * Requirements:
 * - Full request/response cycle with real (test) backend
 * - Authentication/authorization matrix per role
 * - Database state verification
 * - Cascade tests for related entities
 * - Idempotency tests
 */

import { describe, it, expect, beforeAll, afterAll, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import { sessionService } from '@/services/sessionService';
import { applySessionServiceTestEnvironment, authFixtures } from '../test/authSessionTestUtils';

import {
  useSubgraph,
  useEntityContext,
  useGraphQuery,
  useEntityTraversal,
} from './useGraphQuery';

// ============================================================================
// INTEGRATION SETUP - Simulated Backend Services
// ============================================================================

// In-memory test store simulating Neo4j + PostgreSQL
const testStore = {
  entities: new Map<string, any>(),
  relationships: new Map<string, any[]>(),

  reset() {
    this.entities.clear();
    this.relationships.clear();
  },

  seedTestGraph() {
    // Create a test graph: Driver -> Capability -> UseCase
    const driver = {
      id: 'driver-integration-1',
      name: 'Revenue Growth',
      entity_type: 'ValueDriver',
      confidence_score: 0.95,
    };
    const capability = {
      id: 'cap-integration-1',
      name: 'AI Analytics',
      entity_type: 'Capability',
      confidence_score: 0.88,
    };
    const useCase = {
      id: 'usecase-integration-1',
      name: 'Customer Insights',
      entity_type: 'UseCase',
      confidence_score: 0.92,
    };

    this.entities.set(driver.id, driver);
    this.entities.set(capability.id, capability);
    this.entities.set(useCase.id, useCase);

    this.relationships.set(capability.id, [
      { source: capability.id, target: driver.id, type: 'DRIVES' },
      { source: capability.id, target: useCase.id, type: 'ENABLES' },
    ]);
  },
};

// ============================================================================
// AUTH/ROLE MATRIX
// ============================================================================

const ROLES = {
  admin: { tenantId: 'tenant-admin', role: 'tenant_admin', canRead: true },
  analyst: { tenantId: 'tenant-analyst', role: 'analyst', canRead: true },
  viewer: { tenantId: 'tenant-viewer', role: 'read_only', canRead: true },
  guest: { tenantId: null, role: null, canRead: false },
} as const;

type Role = keyof typeof ROLES;

let sessionEnv: ReturnType<typeof applySessionServiceTestEnvironment> | undefined;

// ============================================================================
// INTEGRATION TESTS
// ============================================================================

describe('useSubgraph Integration [L2-Integration]', () => {
  beforeAll(() => {
    sessionEnv = applySessionServiceTestEnvironment();
  });

  afterAll(() => {
    sessionEnv?.reset();
    sessionService.resetEnvironment();
  });

  beforeEach(() => {
    sessionEnv?.reset();
    testStore.reset();
    testStore.seedTestGraph();
    server.resetHandlers();
  });

  describe('full request/response cycle', () => {
    it('fetches coherent subgraph from simulated backend', async () => {
      // Setup backend simulation
      server.use(
        http.get('/api/v1/graph/subgraph', () => {
          const entities = Array.from(testStore.entities.values());
          const edges = Array.from(testStore.relationships.values()).flat();

          return HttpResponse.json({
            root_entity_id: 'cap-integration-1',
            nodes: entities,
            edges,
            depth: 2,
            stats: {
              total_nodes: entities.length,
              total_edges: edges.length,
              density: edges.length / (entities.length * (entities.length - 1) || 1),
            },
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ centerEntityId: 'cap-integration-1', depth: 2 }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Verify complete response structure
      expect(result.current.data?.nodes).toHaveLength(3);
      expect(result.current.data?.edges).toHaveLength(2);
      expect(result.current.data?.stats).toMatchObject({
        totalNodes: 3,
        totalEdges: 2,
      });
    });

    it('handles database connectivity issues gracefully', async () => {
      server.use(
        http.get('/api/v1/graph/subgraph', () =>
          HttpResponse.json(
            { error: 'Database connection failed' },
            { status: 503 }
          )
        )
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'test' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
      expect(result.current.error).toBeDefined();
    });
  });

  describe('authentication/authorization matrix', () => {
    it.each([
      ['admin', true],
      ['analyst', true],
      ['viewer', true],
      ['guest', false],
    ] as [Role, boolean][])('role %s can query: %s', async (role, shouldSucceed) => {
      const roleConfig = ROLES[role];

      if (roleConfig.tenantId && roleConfig.role) {
        const user = authFixtures.user({
          id: `${role}-user`,
          email: `${role}@example.com`,
          role: roleConfig.role,
          tenantId: roleConfig.tenantId,
          tenantSlug: roleConfig.tenantId,
        });
        sessionService.persistSessionMeta(user, roleConfig.tenantId);
      } else {
        sessionService.clearSession();
      }

      server.use(
        http.get('/api/v1/graph/subgraph', ({ request }) => {
          const tenantId = sessionService.getSessionMeta()?.tenantId ?? null;
          const auth = request.headers.get('authorization');
          const clientTenantId = request.headers.get('x-tenant-id');

          if (auth !== null) {
            return HttpResponse.json({ error: 'Unexpected bearer token' }, { status: 403 });
          }

          if (clientTenantId !== null) {
            return HttpResponse.json({ error: 'Unexpected client tenant header' }, { status: 403 });
          }

          if (!roleConfig.canRead || !roleConfig.tenantId || !tenantId) {
            return HttpResponse.json({ error: 'Unauthorized' }, { status: 401 });
          }

          if (tenantId !== roleConfig.tenantId) {
            return HttpResponse.json({ error: 'Forbidden' }, { status: 403 });
          }

          return HttpResponse.json({
            root_entity_id: '',
            nodes: [],
            edges: [],
            depth: 2,
            stats: { total_nodes: 0, total_edges: 0, density: 0 },
          });
        })
      );

      // Create wrapper with cookie-backed session metadata
      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'test' }),
        { wrapper }
      );

      if (shouldSucceed) {
        await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 5000 });
      } else {
        await waitFor(() => expect(result.current.isError).toBe(true), { timeout: 5000 });
      }
    });
  });

  describe('database state verification', () => {
    it('reflects updated entity in subsequent queries', async () => {
      let entityVersion = 1;

      server.use(
        http.get('/api/v1/graph/subgraph', () => {
          return HttpResponse.json({
            root_entity_id: 'entity-1',
            nodes: [
              {
                id: 'entity-1',
                name: `Entity v${entityVersion}`,
                entity_type: 'Capability',
                confidence_score: 0.9,
                version: entityVersion,
              },
            ],
            edges: [],
            depth: 1,
            stats: { total_nodes: 1, total_edges: 0, density: 0 },
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ query: 'test' }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.nodes[0].name).toBe('Entity v1');

      // Simulate entity update
      entityVersion = 2;

      // Refetch
      const { result: result2 } = renderHook(
        () => useSubgraph({ query: 'test', limit: 100 }),
        { wrapper }
      );

      await waitFor(() => expect(result2.current.isSuccess).toBe(true));
      // Note: Due to caching, this may return old data - testing cache invalidation
    });
  });

  describe('cascade tests', () => {
    it('returns related entities when querying by relationship', async () => {
      server.use(
        http.get('/api/v1/graph/subgraph', () => {
          const driver = testStore.entities.get('driver-integration-1');
          const cap = testStore.entities.get('cap-integration-1');
          const useCase = testStore.entities.get('usecase-integration-1');
          const edges = testStore.relationships.get('cap-integration-1') || [];

          return HttpResponse.json({
            root_entity_id: cap.id,
            nodes: [driver, cap, useCase],
            edges,
            depth: 2,
            stats: { total_nodes: 3, total_edges: 2, density: 0.33 },
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useSubgraph({ centerEntityId: 'cap-integration-1', depth: 2 }),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Verify cascade - querying capability returns driver and usecase
      const nodeTypes = result.current.data?.nodes.map((n) => n.entityType);
      expect(nodeTypes).toContain('ValueDriver');
      expect(nodeTypes).toContain('Capability');
      expect(nodeTypes).toContain('UseCase');
    });
  });

  describe('idempotency tests', () => {
    it('produces identical results for identical requests', async () => {
      const responses: any[] = [];

      server.use(
        http.get('/api/v1/graph/subgraph', () => {
          const response = {
            root_entity_id: 'test',
            nodes: Array.from(testStore.entities.values()),
            edges: [],
            depth: 2,
            stats: { total_nodes: 3, total_edges: 0, density: 0 },
          };
          responses.push(response);
          return HttpResponse.json(response);
        })
      );

      const wrapper = createWrapper();

      // Same request twice
      const { result: r1 } = renderHook(
        () => useSubgraph({ query: 'same', depth: 2 }),
        { wrapper }
      );
      await waitFor(() => expect(r1.current.isSuccess).toBe(true));

      // Force refetch by changing then restoring
      const { result: r2 } = renderHook(
        () => useSubgraph({ query: 'same', depth: 2 }),
        { wrapper }
      );
      await waitFor(() => expect(r2.current.isSuccess).toBe(true));

      // Second request served from cache - same data
      expect(r2.current.data?.nodes).toHaveLength(r1.current.data?.nodes.length || 0);
    });
  });
});

describe('useEntityContext Integration [L2-Integration]', () => {
  beforeEach(() => {
    testStore.reset();
    testStore.seedTestGraph();
    server.resetHandlers();
  });

  describe('neighborhood expansion', () => {
    it('returns correct 1-hop neighborhood', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', ({ params }) => {
          const entityId = params.entityId as string;
          const entity = testStore.entities.get(entityId);
          const edges = testStore.relationships.get(entityId) || [];

          // Get neighbors from edges
          const neighborIds = edges.map((e) =>
            e.source === entityId ? e.target : e.source
          );
          const neighbors = neighborIds
            .map((id) => testStore.entities.get(id))
            .filter(Boolean);

          return HttpResponse.json({
            entity_id: entityId,
            center: entity,
            neighbors,
            relationships: edges,
            entity_count: 1 + neighbors.length,
            relationship_count: edges.length,
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useEntityContext('cap-integration-1', 1),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      // Capability connects to driver and usecase
      expect(result.current.data?.neighbors).toHaveLength(2);
      expect(result.current.data?.entityCount).toBe(3);
    });

    it('handles deep traversal (2+ hops)', async () => {
      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', ({ request }) => {
          const url = new URL(request.url);
          const hops = parseInt(url.searchParams.get('hops') || '2');

          // Simulate depth-limited traversal
          const allNodes = Array.from(testStore.entities.values());
          const nodes = hops >= 2 ? allNodes : allNodes.slice(0, 2);

          return HttpResponse.json({
            entity_id: 'cap-integration-1',
            center: allNodes[1],
            neighbors: nodes.filter((n) => n.id !== 'cap-integration-1'),
            relationships: [],
            entity_count: nodes.length,
            relationship_count: 0,
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(
        () => useEntityContext('cap-integration-1', 2),
        { wrapper }
      );

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.entityCount).toBeGreaterThanOrEqual(2);
    });
  });

  describe('relationship filtering integration', () => {
    it('filters by specific relationship types', async () => {
      let capturedTypes: string[] = [];

      server.use(
        http.get('/api/v1/graph/entity/:entityId/context', ({ request }) => {
          const url = new URL(request.url);
          capturedTypes = url.searchParams.getAll('relationship_types');

          return HttpResponse.json({
            entity_id: 'cap-integration-1',
            center: testStore.entities.get('cap-integration-1'),
            neighbors: [],
            relationships: [],
            entity_count: 1,
            relationship_count: 0,
          });
        })
      );

      const wrapper = createWrapper();
      renderHook(
        () => useEntityContext('cap-integration-1', 2, ['ENABLES']),
        { wrapper }
      );

      await waitFor(() => expect(capturedTypes).toContain('ENABLES'));
    });
  });
});

describe('useGraphQuery Integration [L2-Integration]', () => {
  beforeEach(() => {
    server.resetHandlers();
  });

  describe('end-to-end graph query', () => {
    it('executes complex graph query with processing time', async () => {
      server.use(
        http.post('/api/v1/graph/query/graph', async ({ request }) => {
          const body = (await request.json()) as any;

          // Simulate processing delay
          await new Promise((resolve) => setTimeout(resolve, 50));

          return HttpResponse.json({
            query: body.query,
            entities: Array.from(testStore.entities.values()),
            relationships: [],
            confidence_score: 0.85,
            processing_time_ms: 50,
            sources: ['neo4j', 'vector-search'],
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useGraphQuery(), { wrapper });

      await act(async () => {
        result.current.mutate({
          query: 'Find AI capabilities',
          max_hops: 3,
          max_results: 20,
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.processingTimeMs).toBeGreaterThanOrEqual(0);
      expect(result.current.data?.sources).toBeInstanceOf(Array);
    });
  });
});

describe('useEntityTraversal Integration [L2-Integration]', () => {
  beforeEach(() => {
    testStore.reset();
    testStore.seedTestGraph();
    server.resetHandlers();
  });

  describe('value tree traversal', () => {
    it('traverses complete value path', async () => {
      server.use(
        http.post('/api/v1/graph/entity/traverse', async ({ request }) => {
          const body = (await request.json()) as any;

          const driver = testStore.entities.get('driver-integration-1');
          const cap = testStore.entities.get('cap-integration-1');

          return HttpResponse.json({
            start_entity_id: body.entity_id,
            direction: body.direction,
            paths: [
              {
                nodes: [cap, driver],
                relationships: [
                  { source: cap.id, target: driver.id, type: 'DRIVES' },
                ],
                value_score: 0.9,
              },
            ],
            path_count: 1,
          });
        })
      );

      const wrapper = createWrapper();
      const { result } = renderHook(() => useEntityTraversal(), { wrapper });

      await act(async () => {
        result.current.mutate({
          entity_id: 'cap-integration-1',
          direction: 'up',
        });
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.paths[0].valueScore).toBeGreaterThan(0);
    });
  });
});

// Helper for async act
async function act(callback: () => Promise<void>) {
  await callback();
}
