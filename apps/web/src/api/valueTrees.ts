/**
 * Value Trees API Client
 *
 * Provides typed methods for Layer 3 Value Tree endpoints:
 * - GET /v1/value-trees/{entity_id} - Get complete value tree
 * - GET /v1/value-trees/{entity_id}/paths - Get all paths to value drivers
 */

import { apiClient } from './client';
import {
  ValueTreeResponseSchema,
  ValueTreePathListSchema,
  CreateValueTreeRequestSchema,
  ImportValueTreeRequestSchema,
  parseResponseOrThrow,
} from '@/lib/schemas';

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

export interface CreateValueTreeRequest {
  entity_id: string;
  direction?: 'upward' | 'downward';
  initialize_root?: boolean;
}

export interface ImportValueTreeRequest {
  entity_id: string;
  tree: ValueTreeResponse;
}

/**
 * Fetch complete value tree starting from an entity
 * 
 * @param entityId - Root entity ID to start traversal
 * @param direction - 'upward' (Cap→Driver) or 'downward' (Driver→Cap)
 * @param maxDepth - Maximum traversal depth (1-4)
 */
// Constants for API constraints
const MAX_DEPTH_LIMIT = 4;
const MIN_DEPTH_LIMIT = 1;
const DEFAULT_DEPTH = 4;

export async function getValueTree(
  entityId: string,
  direction: 'upward' | 'downward' = 'upward',
  maxDepth: number = DEFAULT_DEPTH
): Promise<ValueTreeResponse> {
  const params = new URLSearchParams();
  params.set('direction', direction);
  params.set('max_depth', String(Math.max(MIN_DEPTH_LIMIT, Math.min(maxDepth, MAX_DEPTH_LIMIT))));

  const response = await apiClient.get(
    'l3',
    `/value-trees/${encodeURIComponent(entityId)}?${params.toString()}`
  );

  if (!response.data) {
    throw new Error('Empty response from value tree API');
  }

  // Runtime validation with Zod - catches API contract drift early
  return parseResponseOrThrow(
    ValueTreeResponseSchema,
    response.data,
    `GET /value-trees/${entityId}`
  );
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
  maxDepth: number = DEFAULT_DEPTH
): Promise<ValueTreePath[]> {
  const params = new URLSearchParams();
  params.set('direction', direction);
  params.set('max_depth', String(Math.max(MIN_DEPTH_LIMIT, Math.min(maxDepth, MAX_DEPTH_LIMIT))));

  const response = await apiClient.get(
    'l3',
    `/value-trees/${encodeURIComponent(entityId)}/paths?${params.toString()}`
  );

  if (!response.data) {
    throw new Error('Empty response from value tree paths API');
  }

  // Runtime validation with Zod - catches API contract drift early
  return parseResponseOrThrow(
    ValueTreePathListSchema,
    response.data,
    `GET /value-trees/${entityId}/paths`
  );
}

export async function createValueTree(payload: CreateValueTreeRequest): Promise<ValueTreeResponse> {
  const validatedPayload = CreateValueTreeRequestSchema.parse(payload);
  const response = await apiClient.post('l3', '/value-trees', validatedPayload);
  if (!response.data) {
    throw new Error('Empty response from create value tree API');
  }
  return parseResponseOrThrow(ValueTreeResponseSchema, response.data, 'POST /value-trees');
}

export async function importValueTree(payload: ImportValueTreeRequest): Promise<ValueTreeResponse> {
  const validatedPayload = ImportValueTreeRequestSchema.parse(payload);
  const response = await apiClient.post('l3', '/value-trees/import', validatedPayload);
  if (!response.data) {
    throw new Error('Empty response from import value tree API');
  }
  return parseResponseOrThrow(ValueTreeResponseSchema, response.data, 'POST /value-trees/import');
}
