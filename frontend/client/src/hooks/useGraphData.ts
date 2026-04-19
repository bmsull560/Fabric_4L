/**
 * Hook for transforming graph data from various sources into unified format.
 * Handles merging subgraph data, entity context, and search results.
 */

import { useMemo } from "react";
import type { GraphNode, GraphRelationship } from "./useGraphQuery";
import { calculateLayout, countNodeTypes } from "@/lib/graph-utils";

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphRelationship[];
  stats: {
    total_nodes: number;
    total_edges: number;
    node_types: Record<string, number>;
    communities: number;
    density: number;
  };
}

export interface UseGraphDataOptions {
  /** Coherent subgraph from backend */
  subgraph?: {
    nodes: GraphNode[];
    edges: GraphRelationship[];
    stats?: {
      total_nodes?: number;
      total_edges?: number;
      density?: number;
    };
  } | null;
  /** Entity context when a node is selected */
  entityContext?: {
    center: GraphNode;
    neighbors: GraphNode[];
    relationships: GraphRelationship[];
    entity_count: number;
    relationship_count: number;
  } | null;
  /** Search results to display */
  searchResults?: {
    entities: GraphNode[];
    relationships: GraphRelationship[];
  } | null;
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
 *
 * @param options - Data sources and configuration
 * @returns Unified graph data with calculated layout and statistics
 *
 * @example
 * const { data: graphData, isEmpty, nodeTypeCounts } = useGraphData({
 *   subgraph: subgraphData,
 *   entityContext: selectedNode ? contextData : null,
 *   searchResults: searchQuery ? searchData : null,
 *   layout: "circular",
 * });
 */
export function useGraphData(options: UseGraphDataOptions): {
  data: GraphData;
  isEmpty: boolean;
  nodeTypeCounts: Record<string, number>;
} {
  const { subgraph, entityContext, searchResults, layout = "circular" } = options;

  return useMemo(() => {
    // Priority: searchResults > entityContext > subgraph
    let nodes: GraphNode[] = [];
    let edges: GraphRelationship[] = [];
    let stats: GraphData["stats"] = {
      total_nodes: 0,
      total_edges: 0,
      node_types: {},
      communities: 0,
      density: 0,
    };

    if (searchResults?.entities?.length) {
      // Use search results
      nodes = searchResults.entities;
      edges = searchResults.relationships || [];
      stats = {
        total_nodes: nodes.length,
        total_edges: edges.length,
        node_types: countNodeTypes(nodes),
        communities: 0,
        density: 0,
      };
    } else if (entityContext) {
      // Use entity context for detailed neighborhood view
      nodes = [entityContext.center, ...entityContext.neighbors];
      edges = entityContext.relationships;
      stats = {
        total_nodes: entityContext.entity_count,
        total_edges: entityContext.relationship_count,
        node_types: countNodeTypes(nodes),
        communities: 0,
        density: 0,
      };
    } else if (subgraph) {
      // Use coherent subgraph from backend
      nodes = subgraph.nodes || [];
      edges = subgraph.edges || [];
      stats = {
        total_nodes: subgraph.stats?.total_nodes ?? nodes.length,
        total_edges: subgraph.stats?.total_edges ?? edges.length,
        node_types: countNodeTypes(nodes),
        communities: 0,
        density: subgraph.stats?.density || 0,
      };
    }

    // Apply layout positioning to nodes that don't have coordinates
    const positionedNodes = applyLayoutToNodes(nodes, layout);

    const isEmpty = positionedNodes.length === 0;

    return {
      data: {
        nodes: positionedNodes,
        edges,
        stats,
      },
      isEmpty,
      nodeTypeCounts: stats.node_types,
    };
  }, [subgraph, entityContext, searchResults, layout]);
}

/**
 * Apply layout to nodes, preserving existing coordinates.
 */
function applyLayoutToNodes(
  nodes: GraphNode[],
  layout: "force" | "circular" | "hierarchical"
): GraphNode[] {
  // Separate nodes with and without positions
  const positioned = nodes.filter(
    (n) => typeof n.x === "number" && typeof n.y === "number"
  );
  const unpositioned = nodes.filter(
    (n) => typeof n.x !== "number" || typeof n.y !== "number"
  );

  // Apply layout only to unpositioned nodes
  const laidOut = calculateLayout(unpositioned, layout);

  // Merge back together (positioned nodes keep their coordinates)
  return [...positioned, ...laidOut];
}
