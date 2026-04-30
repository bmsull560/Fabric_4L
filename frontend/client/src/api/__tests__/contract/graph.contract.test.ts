import { describe, it } from 'vitest';

/**
 * Contract tests: Knowledge Graph (L3)
 *
 * These tests assert frontend API expectations against the documented
 * backend contract. They may be skipped or marked todo until the contract
 * is fully ratified and stable.
 */

describe('Contract: Graph Query', () => {
  it.todo('should expose POST /query/graph');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching GraphQueryResponseSchema');
  it.todo('should include required fields: query, entities, relationships, confidence_score, processing_time_ms');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Entity Context', () => {
  it.todo('should expose GET /entity/{entity_id}/context?hops={n}');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching EntityContextResponseSchema');
  it.todo('should include required fields: entity_id, center, neighbors, relationships, entity_count, relationship_count');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Entity Traversal', () => {
  it.todo('should expose POST /entity/traverse');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching EntityTraversalResponseSchema');
  it.todo('should include required fields: start_entity_id, direction, paths, path_count');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Subgraph', () => {
  it.todo('should expose GET /subgraph?query=&center_entity_id=&depth=&limit=');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape matching SubgraphResponseSchema');
  it.todo('should include required fields: nodes, edges, stats');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});

describe('Contract: Entities', () => {
  it.todo('should expose GET /entities and GET /entities/{id}');
  it.todo('should accept X-Tenant-ID header');
  it.todo('should return shape with required fields: id, name, entity_type, confidence_score');
  it.todo('should support include_provenance and include_relationships query params on detail');
  it.todo('should return error envelope matching { message?, code?, trace_id? } on 4xx/5xx');
});
