/**
 * API Types — Contract-Aligned Type Definitions
 *
 * These types are manually maintained to align with the OpenAPI specs.
 * All API responses should be validated against these types using Zod.
 */

// ============================================================================
// Common Types
// ============================================================================

export interface ApiError {
  message: string;
  code: string;
  trace_id?: string;
  details?: Record<string, unknown>;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_more: boolean;
}

// ============================================================================
// Layer 3: Knowledge Graph Types
// ============================================================================

export interface GraphNode {
  id: string;
  name: string;
  type: string;
  properties?: Record<string, unknown>;
  confidence_score?: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  relationship: string;
  properties?: Record<string, unknown>;
}

export interface SubgraphResponse {
  root_entity_id: string;
  nodes: GraphNode[];
  edges: GraphEdge[];
  depth: number;
  stats: {
    total_nodes: number;
    total_edges: number;
    density: number;
  };
}

export interface Entity {
  id: string;
  name: string;
  type: string;
  domain?: string;
  status: 'draft' | 'validated' | 'deprecated';
  properties: Record<string, unknown>;
  relationships?: Array<{
    target_id: string;
    relationship_type: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface EntityListResponse {
  results: Entity[];
  total: number;
  page: number;
}

// ============================================================================
// Value Trees & Formulas
// ============================================================================

export interface ValueTree {
  id: string;
  entity_id: string;
  root_node: ValueTreeNode;
  total_value: number;
  currency: string;
  confidence: number;
}

export interface ValueTreeNode {
  id: string;
  name: string;
  value: number;
  confidence: number;
  children?: ValueTreeNode[];
  formula_id?: string;
}

// Re-export from formula schema for convenience
export type { Formula, FormulaStatus, FormulaType, ApprovalRequest } from '@/lib/schemas/formula';
