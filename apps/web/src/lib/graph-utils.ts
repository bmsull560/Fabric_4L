/**
 * Graph utility functions for layout calculations, text wrapping, and entity styling.
 * Pure functions with no React dependencies.
 */

import type { GraphNode, GraphRelationship } from "@/hooks/useGraphQuery";

// SVG viewBox dimensions — chosen to fit ~20 nodes comfortably
// at default zoom while maintaining readable labels
export const VIEWBOX_WIDTH = 640;
export const VIEWBOX_HEIGHT = 460;

// Node sizing configuration
export const NODE_SIZES: Record<string, number> = {
  capability: 20,
  usecase: 18,
  persona: 16,
};
export const DEFAULT_NODE_SIZE = 14;

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

/**
 * Calculate node positions for a given layout algorithm.
 * @param nodes — nodes to position
 * @param layout — layout algorithm name
 * @returns Array of positioned nodes with x, y coordinates
 */
export function calculateLayout(
  nodes: GraphNode[],
  layout: "force" | "circular" | "hierarchical" = "circular"
): Array<GraphNode & { x: number; y: number; r: number }> {
  if (!nodes.length) return [];

  const centerX = VIEWBOX_WIDTH / 2;
  const centerY = VIEWBOX_HEIGHT / 2;
  const radius = Math.min(VIEWBOX_WIDTH, VIEWBOX_HEIGHT) * 0.35;

  return nodes.map((node, index) => {
    let x = centerX;
    let y = centerY;

    switch (layout) {
      case "circular": {
        const angle = (index / nodes.length) * 2 * Math.PI;
        x = centerX + radius * Math.cos(angle);
        y = centerY + radius * Math.sin(angle);
        break;
      }
      case "hierarchical": {
        const col = index % 4;
        const row = Math.floor(index / 4);
        x = 120 + col * 160;
        y = 80 + row * 120;
        break;
      }
      case "force":
      default: {
        const col = index % 5;
        const row = Math.floor(index / 5);
        x = 100 + col * 130;
        y = 80 + row * 100;
        break;
      }
    }

    return {
      ...node,
      x,
      y,
      r: getNodeRadius(node.entity_type),
    };
  });
}

/**
 * Get node radius based on entity type importance
 */
export function getNodeRadius(entityType: string | undefined): number {
  const type = (entityType || "").toLowerCase();
  return NODE_SIZES[type] || DEFAULT_NODE_SIZE;
}

/**
 * Count nodes by their type field.
 */
export function countNodeTypes<T extends { entity_type?: string }>(
  nodes: T[]
): Record<string, number> {
  return nodes.reduce((acc, node) => {
    const type = node.entity_type || "Unknown";
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
}

/**
 * Get hex color values for an entity type.
 * Used for SVG rendering.
 */
export function getEntityHexColors(type: string): {
  fill: string;
  stroke: string;
  text: string;
} {
  const colorMap: Record<string, { fill: string; stroke: string; text: string }> = {
    capability: { fill: "#ede9fe", stroke: "#c4b5fd", text: "#5b21b6" },
    usecase: { fill: "#cffafe", stroke: "#67e8f9", text: "#164e63" },
    persona: { fill: "#fef3c7", stroke: "#fcd34d", text: "#92400e" },
    valuedriver: { fill: "#d1fae5", stroke: "#6ee7b7", text: "#065f46" },
    pack: { fill: "#dbeafe", stroke: "#93c5fd", text: "#1e40af" },
    account: { fill: "#f1f5f9", stroke: "#94a3b8", text: "#475569" },
    formula: { fill: "#e0e7ff", stroke: "#a5b4fc", text: "#3730a3" },
    job: { fill: "#ffedd5", stroke: "#fdba74", text: "#7c2d12" },
    workflow: { fill: "#ffe4e6", stroke: "#fda4af", text: "#9f1239" },
  };

  return colorMap[type.toLowerCase()] || colorMap.account;
}

/**
 * Get Tailwind badge classes for an entity type.
 * Used for HTML/CSS rendering (not SVG).
 */
export function getEntityBadgeClasses(type: string): { bg: string; text: string; dot: string } {
  const map: Record<string, { bg: string; text: string; dot: string }> = {
    capability: { bg: "bg-violet-100", text: "text-violet-800", dot: "bg-violet-500" },
    usecase: { bg: "bg-cyan-100", text: "text-cyan-800", dot: "bg-cyan-500" },
    persona: { bg: "bg-amber-100", text: "text-amber-800", dot: "bg-amber-500" },
    valuedriver: { bg: "bg-emerald-100", text: "text-emerald-800", dot: "bg-emerald-500" },
    pack: { bg: "bg-blue-100", text: "text-blue-800", dot: "bg-blue-500" },
    account: { bg: "bg-slate-100", text: "text-slate-800", dot: "bg-slate-500" },
    formula: { bg: "bg-indigo-100", text: "text-indigo-800", dot: "bg-indigo-500" },
    job: { bg: "bg-orange-100", text: "text-orange-800", dot: "bg-orange-500" },
    workflow: { bg: "bg-rose-100", text: "text-rose-800", dot: "bg-rose-500" },
  };

  return map[type.toLowerCase()] || map.account;
}
