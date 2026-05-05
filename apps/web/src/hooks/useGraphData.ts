/**
 * Hook for transforming graph data from various sources into unified format.
 * Handles merging subgraph data, entity context, and search results.
 */

import { useMemo } from "react";
import type { GraphNode, GraphEdge, GraphSubgraph, GraphQueryResult, EntityContext } from "@/features/graph/domain/graph.model";
import { calculateLayout, countNodeTypes, type PositionedNode } from "@/lib/graph-utils";

export interface GraphData {
  nodes: PositionedNode[];
  edges: GraphEdge[];
  stats: {
    totalNodes: number;
    totalEdges: number;
    nodeTypes: Record<string, number>;
    communities: number;
    density: number;
  };
}

export interface UseGraphDataOptions {
  /** Coherent subgraph from backend */
  subgraph?: GraphSubgraph | null;
  /** Entity context when a node is selected */
  entityContext?: EntityContext | null;
  /** Search results to display */
  searchResults?: { entities: GraphNode[]; relationships: GraphEdge[] } | null;
  /** Layout algorithm for positioning nodes */
  layout?: "force" | "circular" | "hierarchical";
}

/**
 * Transform raw graph data from various sources into unified format.
 *
 * Priority of data sources:
 * 1. searchResults (if provided)
 * 2. entityContext (if a node is selected)
 * 3. subgraph (default view)
 */
export function useGraphData(options: UseGraphDataOptions): {
  data: GraphData;
  isEmpty: boolean;
  nodeTypeCounts: Record<string, number>;
} {
  const { subgraph, entityContext, searchResults, layout = "circular" } = options;

  return useMemo(() => {
    let nodes: GraphNode[] = [];
    let edges: GraphEdge[] = [];
    let stats: GraphData["stats"] = {
      totalNodes: 0,
      totalEdges: 0,
      nodeTypes: {},
      communities: 0,
      density: 0,
    };

    if (searchResults?.entities?.length) {
      nodes = searchResults.entities;
      edges = searchResults.relationships || [];
      stats = {
        totalNodes: nodes.length,
        totalEdges: edges.length,
        nodeTypes: countNodeTypes(nodes),
        communities: 0,
        density: 0,
      };
    } else if (entityContext) {
      nodes = [entityContext.center, ...entityContext.neighbors];
      edges = entityContext.relationships;
      stats = {
        totalNodes: entityContext.entityCount,
        totalEdges: entityContext.relationshipCount,
        nodeTypes: countNodeTypes(nodes),
        communities: 0,
        density: 0,
      };
    } else if (subgraph) {
      nodes = subgraph.nodes || [];
      edges = subgraph.edges || [];
      stats = {
        totalNodes: subgraph.stats?.totalNodes ?? nodes.length,
        totalEdges: subgraph.stats?.totalEdges ?? edges.length,
        nodeTypes: countNodeTypes(nodes),
        communities: subgraph.stats?.communities ?? 0,
        density: subgraph.stats?.density || 0,
      };
    }

    // Apply layout calculation
    const positionedNodes = calculateLayout(nodes, layout);

    return {
      data: {
        nodes: positionedNodes,
        edges,
        stats,
      },
      isEmpty: nodes.length === 0,
      nodeTypeCounts: stats.nodeTypes,
    };
  }, [subgraph, entityContext, searchResults, layout]);
}
