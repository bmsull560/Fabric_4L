/**
 * graph.model.ts — Frontend graph domain models
 *
 * These are the canonical types used by graph-consuming UI components.
 * They are intentionally separate from:
 *   - OpenAPI DTOs (snake_case, backend field names)
 *   - Visualization view models (x/y/layout state)
 *
 * All graph hooks and components should consume these domain models,
 * not raw DTOs.
 */

// ── Core Domain Types ────────────────────────────────────────────────────────

export interface GraphNode {
  id: string;
  name: string;
  entityType: string;
  confidenceScore: number;
  description?: string;
  properties?: Record<string, unknown>;
}

export interface GraphEdge {
  sourceId: string;
  targetId: string;
  relationshipType: string;
  weight: number;
  properties?: Record<string, unknown>;
}

export interface GraphSubgraph {
  rootEntityId: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  depth: number;
  stats: GraphStats;
}

export interface GraphStats {
  totalNodes: number;
  totalEdges: number;
  nodeTypes: Record<string, number>;
  communities: number;
  density: number;
}

export interface GraphQueryResult {
  query: string;
  entities: GraphNode[];
  relationships: GraphEdge[];
  contextGraph?: { nodes: GraphNode[]; edges: GraphEdge[] };
  confidenceScore: number;
  sources?: string[];
  processingTimeMs?: number;
  answer?: string;
}

export interface EntityContext {
  entityId: string;
  center: GraphNode;
  neighbors: GraphNode[];
  relationships: GraphEdge[];
  entityCount: number;
  relationshipCount: number;
}

// ── Graph Traversal Types ────────────────────────────────────────────────────

export interface GraphTraversalPath {
  nodes: GraphNode[];
  edges: GraphEdge[];
  valueScore?: number;
}

export interface GraphTraversalResult {
  startEntityId: string;
  direction: 'up' | 'down' | 'both';
  paths: GraphTraversalPath[];
  pathCount: number;
}

// ── Union type for any graph data source ─────────────────────────────────────

export type GraphDataSource =
  | { kind: 'subgraph'; data: GraphSubgraph }
  | { kind: 'query'; data: GraphQueryResult }
  | { kind: 'context'; data: EntityContext }
  | { kind: 'traversal'; data: GraphTraversalResult };
