/**
 * Value Trees React Query Hooks
 * 
 * Server state management for value tree data:
 * - useValueTree: Fetch complete tree for an entity
 * - useValueTreePaths: Fetch all paths to value drivers
 * 
 * All hooks handle loading, error, and caching automatically.
 */

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useCallback } from 'react';
import {
  getValueTree,
  getValueTreePaths,
  type ValueTreeResponse,
  type ValueTreePath,
} from '@/api/valueTrees';
import { QK } from './queryKeys';
import { STALE_TIME } from './useApiShared';

// Query key factory for value trees
const VALUE_TREE_KEYS = {
  all: () => ['value-trees'] as const,
  tree: (entityId: string, direction: string, maxDepth: number) => 
    [...VALUE_TREE_KEYS.all(), 'tree', entityId, direction, maxDepth] as const,
  paths: (entityId: string, direction: string, maxDepth: number) => 
    [...VALUE_TREE_KEYS.all(), 'paths', entityId, direction, maxDepth] as const,
};

// Cache configuration
const GC_TIME_TEN_MINUTES = 1000 * 60 * 10; // 10 minutes

export interface UseValueTreeOptions {
  direction?: 'upward' | 'downward';
  maxDepth?: number;
  enabled?: boolean;
}

/**
 * Fetch complete value tree starting from an entity
 * 
 * @param entityId - Root entity ID (null/undefined to disable)
 * @param options - Direction, depth, and enabled flag
 * 
 * @example
 * ```tsx
 * const { data: tree, isLoading } = useValueTree('cap-123', { 
 *   direction: 'upward', 
 *   maxDepth: 4 
 * });
 * ```
 */
export function useValueTree(
  entityId: string | null | undefined,
  options: UseValueTreeOptions = {}
) {
  const { 
    direction = 'upward', 
    maxDepth = 4, 
    enabled = true 
  } = options;

  return useQuery<ValueTreeResponse, Error>({
    queryKey: entityId 
      ? VALUE_TREE_KEYS.tree(entityId, direction, maxDepth)
      : VALUE_TREE_KEYS.all(),
    queryFn: async () => {
      if (!entityId) {
        throw new Error('Entity ID is required to fetch value tree');
      }
      return getValueTree(entityId, direction, maxDepth);
    },
    enabled: enabled && Boolean(entityId),
    staleTime: STALE_TIME.reference,
    gcTime: GC_TIME_TEN_MINUTES,
  });
}

/**
 * Fetch all paths from entity to value drivers (upward) or capabilities (downward)
 * 
 * @param entityId - Starting entity ID (null/undefined to disable)
 * @param options - Direction, depth, and enabled flag
 * 
 * @example
 * ```tsx
 * const { data: paths } = useValueTreePaths('cap-123', { direction: 'upward' });
 * ```
 */
export function useValueTreePaths(
  entityId: string | null | undefined,
  options: UseValueTreeOptions = {}
) {
  const { 
    direction = 'upward', 
    maxDepth = 4, 
    enabled = true 
  } = options;

  return useQuery<ValueTreePath[], Error>({
    queryKey: entityId
      ? VALUE_TREE_KEYS.paths(entityId, direction, maxDepth)
      : VALUE_TREE_KEYS.all(),
    queryFn: async () => {
      if (!entityId) {
        throw new Error('Entity ID is required to fetch value tree paths');
      }
      return getValueTreePaths(entityId, direction, maxDepth);
    },
    enabled: enabled && Boolean(entityId),
    staleTime: STALE_TIME.reference,
  });
}

/**
 * Hook for manual value tree cache management
 * 
 * @example
 * ```tsx
 * const { invalidateTree, setTreeData } = useValueTreeCache();
 * 
 * // Invalidate cache after mutation
 * invalidateTree('cap-123');
 * ```
 */
export function useValueTreeCache() {
  const queryClient = useQueryClient();

  const invalidateTree = useCallback(
    (_entityId?: string) => {
      // Invalidate all value tree queries (entity-specific or global)
      queryClient.invalidateQueries({
        queryKey: VALUE_TREE_KEYS.all(),
      });
    },
    [queryClient]
  );

  const setTreeData = useCallback(
    (entityId: string, direction: string, maxDepth: number, data: ValueTreeResponse) => {
      queryClient.setQueryData(
        VALUE_TREE_KEYS.tree(entityId, direction, maxDepth),
        data
      );
    },
    [queryClient]
  );

  return { invalidateTree, setTreeData };
}

// Re-export types for convenience
export type { ValueTreeResponse, ValueTreePath };
