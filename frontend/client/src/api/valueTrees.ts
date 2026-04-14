/**
 * Value Trees API Client
 * 
 * Provides typed methods for Layer 3 Value Tree endpoints:
 * - GET /v1/value-trees/{entity_id} - Get complete value tree
 * - GET /v1/value-trees/{entity_id}/paths - Get all paths to value drivers
 */

import { apiClient } from './client';

export interface ValueTreeNode {
  id: string;
  label: string;
  type: string; // 'Capability' | 'UseCase' | 'Persona' | 'ValueDriver'
  layer: number; // 1-4
  confidence: number;
  properties: Record<string, unknown>;
}

export interface ValueTreeEdge {
  source: string;
  target: string;
  type: string; // 'ENABLES' | 'BENEFITS' | 'DRIVES'
  weight: number;
}

export interface ValueTreeStats {
  total_nodes: number;
  total_edges: number;
  by_layer: Record<string, number>;
  max_depth: number;
}

export interface ValueTreeResponse {
  root_entity_id: string;
  direction: 'upward' | 'downward';
  nodes: ValueTreeNode[];
  edges: ValueTreeEdge[];
  paths: Array<{
    length: number;
    nodes: string[];
  }>;
  stats: ValueTreeStats;
}

export interface ValueTreePath {
  nodes: Array<{
    id: string;
    name: string;
    type: string;
  }>;
  length: number;
}

/**
 * Fetch complete value tree starting from an entity
 * 
 * @param entityId - Root entity ID to start traversal
 * @param direction - 'upward' (Cap→Driver) or 'downward' (Driver→Cap)
 * @param maxDepth - Maximum traversal depth (1-4)
 */
export async function getValueTree(
  entityId: string,
  direction: 'upward' | 'downward' = 'upward',
  maxDepth: number = 4
): Promise<ValueTreeResponse> {
  const params = new URLSearchParams();
  params.set('direction', direction);
  params.set('max_depth', String(Math.max(1, Math.min(maxDepth, 4))));

  const response = await apiClient.get(
    'l3', 
    `/value-trees/${encodeURIComponent(entityId)}?${params.toString()}`
  );
  
  if (!response.data) {
    throw new Error('Empty response from value tree API');
  }

  return response.data as ValueTreeResponse;
}

/**
 * Fetch all paths from entity to value drivers (upward) or capabilities (downward)
 * 
 * @param entityId - Starting entity ID
 * @param direction - 'upward' or 'downward'
 * @param maxDepth - Maximum path length
 */
export async function getValueTreePaths(
  entityId: string,
  direction: 'upward' | 'downward' = 'upward',
  maxDepth: number = 4
): Promise<ValueTreePath[]> {
  const params = new URLSearchParams();
  params.set('direction', direction);
  params.set('max_depth', String(Math.max(1, Math.min(maxDepth, 4))));

  const response = await apiClient.get(
    'l3',
    `/value-trees/${encodeURIComponent(entityId)}/paths?${params.toString()}`
  );

  if (!response.data) {
    throw new Error('Empty response from value tree paths API');
  }

  return response.data as ValueTreePath[];
}
