/**
 * Screen 7 — Knowledge Graph Explorer
 * Design: Refined Enterprise SaaS
 */
import { useState, useMemo, useCallback } from "react";
import { Loader2, AlertCircle, RefreshCw, Search } from "lucide-react";
import { PageHeader, Btn, Toolbar, SearchInput, GraphLegend, SectionCard, Tabs } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import { useFullGraph, useEntityContext, useGraphQuery, type GraphNode, type GraphRelationship } from "@/hooks/useGraphQuery";

// Layout constants
const CANVAS_WIDTH = 640;
const CANVAS_HEIGHT = 460;
const LAYOUT_RADIUS_RATIO = 0.35;
const MAX_LABEL_LINE_LENGTH = 12;

// Graph layout aliases (for backward compatibility in calculateLayout)
const GRAPH_WIDTH = CANVAS_WIDTH;
const GRAPH_HEIGHT = CANVAS_HEIGHT;
const GRAPH_RADIUS_RATIO = LAYOUT_RADIUS_RATIO;

// Node sizing configuration
const NODE_SIZES: Record<string, number> = {
  capability: 20,
  usecase: 18,
  persona: 16,
};
const DEFAULT_NODE_SIZE = 14;

// Default values
const DEFAULT_CONFIDENCE = 0.8;

const NODE_COLORS: Record<string, { fill: string; stroke: string; text: string; badgeBg: string; badgeText: string; badgeBorder: string; dotColor: string }> = {
  capability:   { fill: "#ede9fe", stroke: "#c4b5fd", text: "#4c1d95", badgeBg: "bg-violet-100", badgeText: "text-violet-800", badgeBorder: "border-violet-200", dotColor: "bg-violet-400" },
  usecase:      { fill: "#cffafe", stroke: "#67e8f9", text: "#164e63", badgeBg: "bg-cyan-100", badgeText: "text-cyan-800", badgeBorder: "border-cyan-200", dotColor: "bg-cyan-400" },
  persona:      { fill: "#fef3c7", stroke: "#fcd34d", text: "#78350f", badgeBg: "bg-amber-100", badgeText: "text-amber-800", badgeBorder: "border-amber-200", dotColor: "bg-amber-400" },
  valuedriver:  { fill: "#d1fae5", stroke: "#6ee7b7", text: "#065f46", badgeBg: "bg-emerald-100", badgeText: "text-emerald-800", badgeBorder: "border-emerald-200", dotColor: "bg-emerald-400" },
};

/** Get color style configuration for an entity type */
function getEntityTypeStyle(entityType: string | undefined) {
  const type = (entityType || 'Unknown').toLowerCase();
  return NODE_COLORS[type] || NODE_COLORS['Capability'];
}

/** Get node radius based on entity type importance */
function getNodeRadius(entityType: string | undefined): number {
  const type = (entityType || '').toLowerCase();
  return NODE_SIZES[type] || DEFAULT_NODE_SIZE;
}

/** Entity type badge component */
function EntityTypeBadge({ entityType }: { entityType: string | undefined }) {
  const style = getEntityTypeStyle(entityType);
  const label = entityType ? entityType.charAt(0).toUpperCase() + entityType.slice(1) : 'Unknown';
  return (
    <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${style.badgeBg} ${style.badgeText} ${style.badgeBorder}`}>
      {label}
    </div>
  );
}

type GraphEdge = GraphRelationship;

interface PositionedNode extends GraphNode {
  x: number;
  y: number;
  r: number;
}

function countNodeTypes(nodes: GraphNode[]): Record<string, number> {
  return nodes.reduce((acc, node) => {
    const type = node.entity_type || 'Unknown';
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
}

export default function GraphExplorer() {
  const [selected, setSelected] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("Graph Explorer");
  const [queryText, setQueryText] = useState("");
  const [searchError, setSearchError] = useState<string | null>(null);

  // Full graph query for initial load
  const { data: fullGraph, isLoading: fullGraphLoading, error: fullGraphError, refetch: refetchFullGraph } = useFullGraph();

  // Entity context query when a node is selected
  const { data: entityContext, isLoading: contextLoading } = useEntityContext(selected, 2);

  // GraphRAG query mutation for search
  const graphQuery = useGraphQuery();

  // Memoize graph data to prevent recalculation on every render
  const graphData = useMemo(() => {
    if (selected && entityContext) {
      return {
        nodes: [entityContext.center, ...entityContext.neighbors],
        edges: entityContext.relationships.map(r => ({
          source: r.source,
          target: r.target,
          type: r.type,
        })),
        stats: {
          total_nodes: entityContext.entity_count,
          total_edges: entityContext.relationship_count,
          node_types: countNodeTypes([entityContext.center, ...entityContext.neighbors]),
          communities: 0,
          density: 0,
        },
      };
    }
    return {
      nodes: fullGraph?.nodes || [],
      edges: fullGraph?.relationships || [],
      stats: {
        total_nodes: fullGraph?.nodes?.length || 0,
        total_edges: fullGraph?.relationships?.length || 0,
        node_types: countNodeTypes(fullGraph?.nodes || []),
        communities: 0,
        density: 0,
      },
    };
  }, [selected, entityContext, fullGraph]);

  const isLoading = fullGraphLoading || contextLoading || graphQuery.isPending;
  const error = fullGraphError?.message || graphQuery.error?.message || searchError;

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelected(prev => nodeId === prev ? null : nodeId);
  }, []);

  const handleSearch = async () => {
    if (!queryText.trim()) return;
    setSearchError(null);
    try {
      await graphQuery.mutateAsync({
        query: queryText,
        max_hops: 2,
        max_results: 20,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setSearchError(message);
    }
  };

  const selectedNodeData = graphData.nodes.find(n => n.id === selected);

  const handleReset = () => {
    setSelected(null);
    refetchFullGraph();
  };

  return (
    <div className="p-6">
      <PageHeader
        breadcrumbs={["Knowledge Graph", "Graph Explorer"]}
        title="Graph Explorer"
        subtitle="Explore the enterprise knowledge graph with advanced visualization."
        actions={<Btn variant="ghost">Export</Btn>}
      />

      <Tabs
        tabs={["Graph Explorer", "Query Builder", "Communities", "Metrics"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      <Toolbar>
        <SearchInput
          placeholder="Search graph…"
          value={queryText}
          onChange={(e) => setQueryText(e.target.value)}
        />
        <Btn variant="ghost" onClick={handleSearch} disabled={!queryText.trim() || graphQuery.isPending}>
          {graphQuery.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
          Search
        </Btn>
        <Btn variant="ghost">Layout: Force ▾</Btn>
        <Btn variant="ghost">Filters ▾</Btn>
        <Btn variant="ghost">Community View</Btn>
        <Btn variant="ghost">Metrics</Btn>
      </Toolbar>

      <div className="flex gap-4">
        {/* Graph canvas */}
        <div className="flex-1 bg-white border border-neutral-200 rounded-lg shadow-sm overflow-hidden">
          {isLoading && (
            <div className="p-6" style={{ minHeight: 380 }}>
              {/* Skeleton loader for graph visualization */}
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <Skeleton className="h-4 w-32" />
                  <Skeleton className="h-4 w-24" />
                </div>
                <div className="relative" style={{ height: 320 }}>
                  {/* Skeleton nodes arranged in a circle pattern */}
                  <Skeleton className="absolute h-12 w-12 rounded-full" style={{ top: '20%', left: '30%' }} />
                  <Skeleton className="absolute h-10 w-10 rounded-full" style={{ top: '40%', left: '50%' }} />
                  <Skeleton className="absolute h-8 w-8 rounded-full" style={{ top: '60%', left: '25%' }} />
                  <Skeleton className="absolute h-10 w-10 rounded-full" style={{ top: '30%', left: '70%' }} />
                  <Skeleton className="absolute h-8 w-8 rounded-full" style={{ top: '70%', left: '60%' }} />
                  <Skeleton className="absolute h-6 w-6 rounded-full" style={{ top: '50%', left: '80%' }} />
                  {/* Skeleton connection lines */}
                  <Skeleton className="absolute h-0.5 w-24" style={{ top: '35%', left: '35%', transform: 'rotate(25deg)' }} />
                  <Skeleton className="absolute h-0.5 w-20" style={{ top: '55%', left: '35%', transform: 'rotate(-30deg)' }} />
                  <Skeleton className="absolute h-0.5 w-16" style={{ top: '40%', left: '55%', transform: 'rotate(45deg)' }} />
                  <Skeleton className="absolute h-0.5 w-28" style={{ top: '55%', left: '50%', transform: 'rotate(-10deg)' }} />
                </div>
                <div className="flex items-center justify-center gap-2 text-neutral-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Loading knowledge graph...</span>
                </div>
              </div>
            </div>
          )}

          {error && !isLoading && (
            <div className="flex items-center justify-center" style={{ minHeight: 380 }}>
              <div className="flex flex-col items-center gap-3 text-neutral-500">
                <AlertCircle className="w-8 h-8 text-red-500" />
                <span className="text-sm text-red-600">{error}</span>
                <Btn variant="outline" onClick={() => refetchFullGraph()} className="text-xs">
                  <RefreshCw className="w-3 h-3 mr-1" /> Retry
                </Btn>
              </div>
            </div>
          )}

          {!isLoading && !error && graphData.nodes.length === 0 && (
            <div className="flex items-center justify-center" style={{ minHeight: 380 }}>
              <div className="flex flex-col items-center gap-3 text-neutral-500">
                <span className="text-sm">No graph data available</span>
                <span className="text-xs text-neutral-400">Try ingesting some content first</span>
              </div>
            </div>
          )}

          {!isLoading && !error && graphData.nodes.length > 0 && (
            <GraphVisualization
              nodes={graphData.nodes}
              edges={graphData.edges}
              selected={selected}
              onNodeClick={handleNodeClick}
            />
          )}

          {/* Legend */}
          <div className="px-4 py-3 border-t border-neutral-100">
            <GraphLegend/>
          </div>
        </div>

        {/* Right panel */}
        <div className="w-[220px] shrink-0 space-y-3">
          {/* Selected node */}
          <SectionCard title="Selected Node">
            {selectedNodeData ? (
              <div className="space-y-2">
                <div className="text-[13px] font-bold text-neutral-900">{selectedNodeData.name}</div>
                <EntityTypeBadge entityType={selectedNodeData.entity_type} />
                <div className="text-[11px] text-neutral-500">
                  Confidence: {Math.round((selectedNodeData.confidence_score || DEFAULT_CONFIDENCE) * 100)}%
                </div>
                <div className="flex flex-col gap-1.5 mt-2">
                  <Btn variant="ghost" className="text-[11px] justify-center" onClick={() => setSelected(selectedNodeData.id)}>
                    View Selected
                  </Btn>
                  <Btn variant="outline" className="text-[11px] justify-center" onClick={handleReset}>
                    Reset View
                  </Btn>
                </div>
              </div>
            ) : (
              <div className="text-[12px] text-neutral-400">Click a node to select</div>
            )}
          </SectionCard>

          {/* Stats */}
          <SectionCard title="Graph Statistics">
            <div className="space-y-2">
              {[
                { label: "Nodes",       value: graphData.stats?.total_nodes ?? graphData.nodes.length },
                { label: "Edges",       value: graphData.stats?.total_edges ?? graphData.edges.length },
                { label: "Communities", value: graphData.stats?.communities ?? 0 },
                { label: "Density",     value: graphData.stats?.density?.toFixed(2) ?? "0.00" },
              ].map(s => (
                <div key={s.label} className="flex justify-between text-[12px]">
                  <span className="text-neutral-500">{s.label}</span>
                  <span className="font-bold text-neutral-800">
                    {typeof s.value === 'number' ? s.value.toLocaleString() : s.value}
                  </span>
                </div>
              ))}
              <div className="border-t border-neutral-100 pt-2 mt-1 space-y-1">
                {Object.entries(graphData.stats?.node_types || {}).map(([nodeType, nodeCount]) => {
                  const style = getEntityTypeStyle(nodeType);
                  return (
                    <div key={nodeType} className="flex items-center gap-2 text-[11px]">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${style.dotColor}`}/>
                      <span className="text-neutral-500 flex-1">{nodeType}</span>
                      <span className="font-semibold text-neutral-700">{Number(nodeCount).toLocaleString()}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

/** Wrap text into lines with a maximum line length */
function wrapTextIntoLines(text: string, maxLineLength: number): string[] {
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

/** Calculate circular layout for graph nodes */
function calculateLayout(nodes: GraphNode[], edges: GraphEdge[]): PositionedNode[] {
  if (!nodes.length) return [];

  const centerX = GRAPH_WIDTH / 2;
  const centerY = GRAPH_HEIGHT / 2;

  return nodes.map((node, index) => {
    const angle = (index / nodes.length) * 2 * Math.PI;
    const radius = Math.min(GRAPH_WIDTH, GRAPH_HEIGHT) * GRAPH_RADIUS_RATIO;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      r: getNodeRadius(node.entity_type),
    };
  });
}

interface GraphVisualizationProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  selected: string | null;
  onNodeClick: (nodeId: string) => void;
}

function GraphVisualization({ nodes, edges, selected, onNodeClick }: GraphVisualizationProps) {
  const positionedNodes = calculateLayout(nodes, edges);
  const nodeMap = new Map(positionedNodes.map(n => [n.id, n]));

  return (
    <svg viewBox="0 0 640 460" className="w-full" style={{ minHeight: 380 }}>
      {/* Grid */}
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
        </pattern>
      </defs>
      <rect width="640" height="460" fill="url(#grid)"/>

      {/* Edges */}
      {edges.map((edge, i) => {
        const source = nodeMap.get(edge.source);
        const target = nodeMap.get(edge.target);
        if (!source || !target || source.x === undefined || source.y === undefined || target.x === undefined || target.y === undefined) {
          return null;
        }
        return (
          <line
            key={i}
            x1={source.x} y1={source.y} x2={target.x} y2={target.y}
            stroke="#d1d5db" strokeWidth="1.5"
          />
        );
      })}

      {/* Nodes */}
      {positionedNodes.map(node => {
        const c = getEntityTypeStyle(node.entity_type);
        const isSelected = node.id === selected;
        const lines = wrapTextIntoLines(node.name, MAX_LABEL_LINE_LENGTH);
        const lineOffsetBase = (lines.length - 1) / 2;

        return (
          <g key={node.id} onClick={() => onNodeClick(node.id)} style={{ cursor: "pointer" }}>
            <circle
              cx={node.x} cy={node.y} r={node.r}
              fill={c.fill}
              stroke={isSelected ? "#1d4ed8" : c.stroke}
              strokeWidth={isSelected ? 2.5 : 1.5}
            />
            {lines.map((line, lineIndex) => (
              <text
                key={lineIndex}
                x={node.x}
                y={node.y + (lineIndex - lineOffsetBase) * 11 + 1}
                textAnchor="middle"
                dominantBaseline="middle"
                fontSize="8"
                fontFamily="Inter, sans-serif"
                fontWeight="600"
                fill={c.text}
              >
                {line}
              </text>
            ))}
          </g>
        );
      })}
    </svg>
  );
}
