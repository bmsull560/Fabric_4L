/**
 * Screen 7 — Knowledge Graph Explorer
 * Design: Refined Enterprise SaaS
 */
import { useState, useMemo, useCallback } from "react";
import { Loader2, AlertCircle, RefreshCw, Search, ZoomIn, ZoomOut, RotateCcw, MousePointer2, Move } from "lucide-react";
import { PageHeader, Btn, SearchInput, GraphLegend, SectionCard, Tabs } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import { useSubgraph, useEntityContext, useGraphQuery, useGraphViewState, type GraphNode, type GraphRelationship, type SubgraphResponse } from "@/hooks/useGraphQuery";
import { getEntityColors } from "@/lib/entity-colors";

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

/** Get color style configuration for an entity type */
function getEntityTypeStyle(entityType: string | undefined) {
  const colors = getEntityColors(entityType || 'unknown');
  return {
    fill: colors.fill,
    stroke: colors.stroke,
    text: colors.text.replace('text-', '').replace(/-\d+/, ''), // Convert to hex reference
    badgeBg: colors.bg,
    badgeText: colors.text,
    badgeBorder: colors.border,
    dotColor: colors.dot,
  };
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

  // Subgraph query for coherent graph data (replaces useFullGraph sampling)
  const { data: subgraph, isLoading: subgraphLoading, error: subgraphError, refetch: refetchSubgraph } = useSubgraph({
    query: '', // Empty query returns default subgraph
    depth: 2,
    limit: 100,
  });

  // Entity context query when a node is selected
  const { data: entityContext, isLoading: contextLoading } = useEntityContext(selected, 2);

  // GraphRAG query mutation for search
  const graphQuery = useGraphQuery();

  // Zoom and pan state management
  const { viewState, zoomIn, zoomOut, resetView, panBy } = useGraphViewState();

  // Drag state for panning
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  // Memoize graph data from coherent subgraph response
  const graphData = useMemo(() => {
    if (selected && entityContext) {
      // Use entity context when a node is selected for detailed neighborhood view
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
    // Use coherent subgraph from backend (no client-side sampling)
    return {
      nodes: subgraph?.nodes || [],
      edges: subgraph?.edges || [],
      stats: {
        total_nodes: subgraph?.stats?.total_nodes ?? subgraph?.nodes?.length ?? 0,
        total_edges: subgraph?.stats?.total_edges ?? subgraph?.edges?.length ?? 0,
        node_types: countNodeTypes(subgraph?.nodes || []),
        communities: 0,
        density: subgraph?.stats?.density || 0,
      },
    };
  }, [selected, entityContext, subgraph]);

  const isLoading = subgraphLoading || contextLoading || graphQuery.isPending;
  const error = subgraphError?.message || graphQuery.error?.message || searchError;

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
    resetView();
    refetchSubgraph();
  };

  // Mouse event handlers for panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) { // Left click only
      setIsDragging(true);
      setDragStart({ x: e.clientX - viewState.panX, y: e.clientY - viewState.panY });
    }
  }, [viewState.panX, viewState.panY]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging) {
      panBy(e.clientX - dragStart.x, e.clientY - dragStart.y);
    }
  }, [isDragging, dragStart, panBy]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  return (
    <div className="p-6">
      <PageHeader
        breadcrumbs={[{ label: "Knowledge Graph" }, { label: "Graph Explorer" }]}
        title="Graph Explorer"
        subtitle="Visualize and navigate the knowledge graph"
        actions={
          <div className="flex items-center gap-2">
            <Btn variant="ghost" onClick={handleSearch} disabled={!queryText.trim() || graphQuery.isPending}>
              {graphQuery.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
              Search
            </Btn>
            <Btn variant="ghost">Export</Btn>
            <Btn variant="primary">Focus Selection</Btn>
          </div>
        }
      />

      <Tabs
        tabs={["Graph Explorer", "Query Builder", "Communities", "Metrics"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      {/* 3-Panel Layout: Control | Canvas | Inspector */}
      <div className="flex gap-4 h-[calc(100vh-280px)] min-h-[500px]">
        {/* Left Control Panel */}
        <div className="w-[200px] shrink-0 space-y-3">
          <SectionCard title="Control Panel" className="h-fit">
            <div className="space-y-3">
              <SearchInput
                placeholder="Search entities..."
                value={queryText}
                onChange={(e) => setQueryText(e.target.value)}
              />

              {/* Zoom Controls */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Zoom</div>
                <div className="flex gap-2">
                  <Btn variant="ghost" className="flex-1 text-[11px]" onClick={zoomIn}>
                    <ZoomIn className="w-3 h-3 mr-1" /> In
                  </Btn>
                  <Btn variant="ghost" className="flex-1 text-[11px]" onClick={zoomOut}>
                    <ZoomOut className="w-3 h-3 mr-1" /> Out
                  </Btn>
                </div>
                <div className="text-[10px] text-muted-foreground/70 text-center">
                  {Math.round(viewState.zoom * 100)}%
                </div>
              </div>

              {/* View Controls */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">View</div>
                <Btn variant="ghost" className="w-full text-[11px] justify-center" onClick={resetView}>
                  <RotateCcw className="w-3 h-3 mr-1" /> Reset View
                </Btn>
              </div>

              {/* Layout Controls */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Layout</div>
                <Btn variant="ghost" className="w-full text-[11px] justify-center">
                  Force Directed
                </Btn>
                <Btn variant="ghost" className="w-full text-[11px] justify-center">
                  Circular
                </Btn>
                <Btn variant="ghost" className="w-full text-[11px] justify-center">
                  Hierarchical
                </Btn>
              </div>

              {/* Filter Controls */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Filters</div>
                <Btn variant="ghost" className="w-full text-[11px] justify-center">
                  Entity Types ▾
                </Btn>
                <Btn variant="ghost" className="w-full text-[11px] justify-center">
                  Confidence ▾
                </Btn>
              </div>
            </div>
          </SectionCard>

          <SectionCard title="Legend" className="h-fit">
            <GraphLegend />
          </SectionCard>
        </div>

        {/* Graph Canvas */}
        <div className="flex-1 bg-card border border-border rounded-lg shadow-sm overflow-hidden relative">
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
                <div className="flex items-center justify-center gap-2 text-muted-foreground">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span className="text-sm">Loading knowledge graph...</span>
                </div>
              </div>
            </div>
          )}

          {error && !isLoading && (
            <div className="flex items-center justify-center" style={{ minHeight: 380 }}>
              <div className="flex flex-col items-center gap-3 text-muted-foreground">
                <AlertCircle className="w-8 h-8 text-red-500" />
                <span className="text-sm text-destructive">{error}</span>
                <Btn variant="outline" onClick={() => refetchSubgraph()} className="text-xs">
                  <RefreshCw className="w-3 h-3 mr-1" /> Retry
                </Btn>
              </div>
            </div>
          )}

          {!isLoading && !error && graphData.nodes.length === 0 && (
            <div className="flex items-center justify-center" style={{ minHeight: 380 }}>
              <div className="flex flex-col items-center gap-3 text-muted-foreground text-center px-8">
                <span className="text-sm font-medium">No matching entities found</span>
                <span className="text-xs text-muted-foreground/60 max-w-[200px]">
                  Try adjusting your search query or filters to see more results
                </span>
              </div>
            </div>
          )}

          {/* Pan/Drag hint overlay */}
          {!isLoading && !error && graphData.nodes.length > 0 && (
            <div className="absolute top-3 left-3 z-10 flex items-center gap-2 bg-card/90 backdrop-blur-sm px-3 py-1.5 rounded-md border border-border shadow-sm">
              <Move className="w-3 h-3 text-muted-foreground" />
              <span className="text-[11px] text-muted-foreground">Drag to pan</span>
            </div>
          )}

          {/* Truncation indicator */}
          {!isLoading && !error && graphData.nodes.length >= 100 && (
            <div className="absolute bottom-3 left-3 z-10 flex items-center gap-1.5 bg-warning/10 backdrop-blur-sm px-3 py-1.5 rounded-md border border-warning/20 shadow-sm">
              <AlertCircle className="w-3 h-3 text-warning" />
              <span className="text-[11px] text-warning-foreground">
                Showing 100 nodes. Refine search to see more.
              </span>
            </div>
          )}

          {!isLoading && !error && graphData.nodes.length > 0 && (
            <GraphVisualization
              nodes={graphData.nodes}
              edges={graphData.edges}
              selected={selected}
              onNodeClick={handleNodeClick}
              viewState={viewState}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              isDragging={isDragging}
            />
          )}
        </div>

        {/* Right Inspector Panel */}
        <div className="w-[250px] shrink-0 space-y-3">
          <SectionCard title="Inspector Panel">
            {selectedNodeData ? (
              <div className="space-y-3">
                {/* Entity Name */}
                <div className="text-[14px] font-bold text-foreground leading-tight">
                  {selectedNodeData.name}
                </div>

                {/* Entity Type Badge */}
                <EntityTypeBadge entityType={selectedNodeData.entity_type} />

                {/* Description */}
                {selectedNodeData.description && (
                  <div className="text-[11px] text-muted-foreground leading-relaxed border-l-2 border-border pl-2">
                    {selectedNodeData.description}
                  </div>
                )}

                {/* Properties */}
                <div className="space-y-1.5">
                  <div className="text-[10px] font-semibold text-muted-foreground/60 uppercase tracking-wider">Properties</div>
                  <div className="text-[11px] text-muted-foreground">
                    <span className="text-muted-foreground/60">Confidence:</span>{' '}
                    <span className="font-medium">{Math.round((selectedNodeData.confidence_score || DEFAULT_CONFIDENCE) * 100)}%</span>
                  </div>
                  <div className="text-[11px] text-muted-foreground">
                    <span className="text-muted-foreground/60">ID:</span>{' '}
                    <span className="font-mono text-[10px]">{selectedNodeData.id.slice(0, 16)}...</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-1.5 pt-2 border-t border-border/50">
                  <Btn variant="ghost" className="text-[11px] justify-center" onClick={() => setSelected(selectedNodeData.id)}>
                    <MousePointer2 className="w-3 h-3 mr-1" /> Focus
                  </Btn>
                  <Btn variant="outline" className="text-[11px] justify-center" onClick={handleReset}>
                    <RotateCcw className="w-3 h-3 mr-1" /> Reset View
                  </Btn>
                </div>
              </div>
            ) : (
              <div className="space-y-2">
                <div className="text-[12px] text-muted-foreground/60 text-center py-4">
                  <MousePointer2 className="w-5 h-5 mx-auto mb-2 text-muted-foreground/40" />
                  Click a node to view details
                </div>
              </div>
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
                  <span className="text-muted-foreground">{s.label}</span>
                  <span className="font-bold text-foreground">
                    {typeof s.value === 'number' ? s.value.toLocaleString() : s.value}
                  </span>
                </div>
              ))}
              <div className="border-t border-border/50 pt-2 mt-1 space-y-1">
                {Object.entries(graphData.stats?.node_types || {}).map(([nodeType, nodeCount]) => {
                  const style = getEntityTypeStyle(nodeType);
                  return (
                    <div key={nodeType} className="flex items-center gap-2 text-[11px]">
                      <div className={`w-2 h-2 rounded-full shrink-0 ${style.dotColor}`}/>
                      <span className="text-muted-foreground flex-1">{nodeType}</span>
                      <span className="font-semibold text-foreground">{Number(nodeCount).toLocaleString()}</span>
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
  viewState: { zoom: number; panX: number; panY: number };
  onMouseDown: (e: React.MouseEvent) => void;
  onMouseMove: (e: React.MouseEvent) => void;
  onMouseUp: () => void;
  isDragging: boolean;
}

function GraphVisualization({
  nodes,
  edges,
  selected,
  onNodeClick,
  viewState,
  onMouseDown,
  onMouseMove,
  onMouseUp,
  isDragging
}: GraphVisualizationProps) {
  const positionedNodes = useMemo(() => calculateLayout(nodes, edges), [nodes, edges]);
  const nodeMap = useMemo(() => new Map(positionedNodes.map(n => [n.id, n])), [positionedNodes]);

  // Calculate transform for zoom and pan
  const transform = `translate(${viewState.panX}, ${viewState.panY}) scale(${viewState.zoom})`;

  return (
    <svg
      viewBox="0 0 640 460"
      className={`w-full h-full ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
      style={{ minHeight: 380 }}
      onMouseDown={onMouseDown}
      onMouseMove={onMouseMove}
      onMouseUp={onMouseUp}
      onMouseLeave={onMouseUp}
    >
      {/* Grid */}
      <defs>
        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
        </pattern>
      </defs>
      <rect width="640" height="460" fill="url(#grid)"/>

      {/* Graph content with zoom/pan transform */}
      <g transform={transform}>
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
            <g
              key={node.id}
              onClick={(e) => {
                e.stopPropagation();
                onNodeClick(node.id);
              }}
              style={{ cursor: "pointer" }}
            >
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
      </g>
    </svg>
  );
}
