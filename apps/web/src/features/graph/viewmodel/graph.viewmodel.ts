/**
 * graph.viewmodel.ts — Graph Visualization ViewModel
 *
 * Separates graph API/domain shape from visualization layout state.
 * Domain models (GraphNode, GraphEdge) contain business data only.
 * ViewModels add layout, selection, and rendering metadata.
 *
 * Rule: UI state does NOT mutate API-derived graph models.
 */

import type { GraphNode, GraphEdge } from '../domain/graph.model';

// ── ViewModel Types ──────────────────────────────────────────────────────────

export interface GraphNodeViewModel {
  /** Domain identifier (stable across re-renders) */
  id: string;
  /** Display label (may be truncated for rendering) */
  displayLabel: string;
  /** Entity type for styling */
  entityType: string;
  /** Visual category drives color/shape */
  visualCategory: string;
  /** X position in canvas coordinates */
  x: number;
  /** Y position in canvas coordinates */
  y: number;
  /** Render radius */
  r: number;
  /** Whether the node is currently selected */
  selected: boolean;
  /** Whether the node's children are collapsed */
  collapsed: boolean;
  /** Confidence drives opacity or border style */
  confidenceScore: number;
  /** Original domain model (read-only reference) */
  readonly source: GraphNode;
}

export interface GraphEdgeViewModel {
  /** Domain source ID */
  sourceId: string;
  /** Domain target ID */
  targetId: string;
  /** Relationship type for styling */
  relationshipType: string;
  /** Visual weight drives stroke width */
  visualWeight: number;
  /** Whether the edge is highlighted (e.g., on hover) */
  highlighted: boolean;
  /** Original domain model (read-only reference) */
  readonly source: GraphEdge;
}

export interface GraphViewModel {
  nodes: GraphNodeViewModel[];
  edges: GraphEdgeViewModel[];
  /** Canvas bounding box */
  bounds: {
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
  };
}

// ── Layout Configuration ─────────────────────────────────────────────────────

export const VIEWBOX_WIDTH = 640;
export const VIEWBOX_HEIGHT = 460;

export const NODE_SIZE_BY_TYPE: Record<string, number> = {
  capability: 20,
  usecase: 18,
  persona: 16,
};
export const DEFAULT_NODE_SIZE = 14;

export type LayoutAlgorithm = 'force' | 'circular' | 'hierarchical';

// ── Factory Functions ────────────────────────────────────────────────────────

function computeNodeRadius(entityType: string): number {
  return NODE_SIZE_BY_TYPE[entityType.toLowerCase()] ?? DEFAULT_NODE_SIZE;
}

function computeVisualCategory(entityType: string): string {
  return entityType.toLowerCase();
}

function calculateCircularLayout(nodes: GraphNode[]): Array<{ x: number; y: number }> {
  const centerX = VIEWBOX_WIDTH / 2;
  const centerY = VIEWBOX_HEIGHT / 2;
  const radius = Math.min(VIEWBOX_WIDTH, VIEWBOX_HEIGHT) * 0.35;

  return nodes.map((_, index) => {
    const angle = (index / nodes.length) * 2 * Math.PI;
    return {
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
    };
  });
}

function calculateHierarchicalLayout(nodes: GraphNode[]): Array<{ x: number; y: number }> {
  return nodes.map((_, index) => {
    const col = index % 4;
    const row = Math.floor(index / 4);
    return {
      x: 120 + col * 160,
      y: 80 + row * 120,
    };
  });
}

function calculateGridLayout(nodes: GraphNode[]): Array<{ x: number; y: number }> {
  return nodes.map((_, index) => {
    const col = index % 5;
    const row = Math.floor(index / 5);
    return {
      x: 100 + col * 120,
      y: 80 + row * 100,
    };
  });
}

// ── toGraphViewModel ─────────────────────────────────────────────────────────

export interface ToGraphViewModelOptions {
  layout?: LayoutAlgorithm;
  selectedNodeIds?: Set<string>;
  collapsedNodeIds?: Set<string>;
}

/**
 * Convert domain graph models into visualization view models.
 *
 * This function is pure: it does not mutate the input domain models.
 * All layout state is computed fresh on every call.
 */
export function toGraphViewModel(
  nodes: readonly GraphNode[],
  edges: readonly GraphEdge[],
  options: ToGraphViewModelOptions = {}
): GraphViewModel {
  const { layout = 'circular', selectedNodeIds = new Set(), collapsedNodeIds = new Set() } = options;

  // Calculate positions
  let positions: Array<{ x: number; y: number }>;
  switch (layout) {
    case 'circular':
      positions = calculateCircularLayout([...nodes]);
      break;
    case 'hierarchical':
      positions = calculateHierarchicalLayout([...nodes]);
      break;
    case 'force':
    default:
      positions = calculateGridLayout([...nodes]);
      break;
  }

  // Build node view models
  const nodeVms: GraphNodeViewModel[] = nodes.map((node, index) => {
    const pos = positions[index] ?? { x: VIEWBOX_WIDTH / 2, y: VIEWBOX_HEIGHT / 2 };
    return {
      id: node.id,
      displayLabel: truncateLabel(node.name, 24),
      entityType: node.entityType,
      visualCategory: computeVisualCategory(node.entityType),
      x: pos.x,
      y: pos.y,
      r: computeNodeRadius(node.entityType),
      selected: selectedNodeIds.has(node.id),
      collapsed: collapsedNodeIds.has(node.id),
      confidenceScore: node.confidenceScore,
      source: node,
    };
  });

  // Build edge view models
  const edgeVms: GraphEdgeViewModel[] = edges.map((edge) => ({
    sourceId: edge.sourceId,
    targetId: edge.targetId,
    relationshipType: edge.relationshipType,
    visualWeight: edge.weight,
    highlighted: false,
    source: edge,
  }));

  // Compute bounds
  const xs = nodeVms.map((n) => n.x);
  const ys = nodeVms.map((n) => n.y);
  const rs = nodeVms.map((n) => n.r);
  const maxR = rs.length > 0 ? Math.max(...rs) : 0;

  const bounds = {
    minX: xs.length > 0 ? Math.min(...xs) - maxR : 0,
    minY: ys.length > 0 ? Math.min(...ys) - maxR : 0,
    maxX: xs.length > 0 ? Math.max(...xs) + maxR : VIEWBOX_WIDTH,
    maxY: ys.length > 0 ? Math.max(...ys) + maxR : VIEWBOX_HEIGHT,
  };

  return { nodes: nodeVms, edges: edgeVms, bounds };
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function truncateLabel(label: string, maxLength: number): string {
  if (label.length <= maxLength) return label;
  return label.slice(0, maxLength - 1) + '…';
}

/**
 * Wrap text into lines with a maximum line length.
 * Used for SVG text labels that need to fit within node circles.
 */
export function wrapTextIntoLines(text: string, maxLineLength: number): string[] {
  const words = text.split(/\s+/);
  const lines: string[] = [];

  for (const word of words) {
    const currentLine = lines[lines.length - 1];
    const proposedLine = currentLine ? `${currentLine} ${word}` : word;

    if (!currentLine || proposedLine.length > maxLineLength) {
      lines.push(word);
    } else {
      lines[lines.length - 1] = proposedLine;
    }
  }

  return lines;
}
