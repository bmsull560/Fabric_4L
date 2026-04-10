/**
 * Screen 7 — Knowledge Graph Explorer
 * Design: Refined Enterprise SaaS
 */
import { useEffect, useState } from "react";
import { Loader2, AlertCircle, RefreshCw } from "lucide-react";
import { PageHeader, Btn, Toolbar, SearchInput, GraphLegend, SectionCard, Tabs } from "@/components/WfPrimitives";
import { useGraphStore, GraphNode, GraphEdge } from "@/stores/graphStore";

const NODE_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  Capability:   { fill: "#ede9fe", stroke: "#c4b5fd", text: "#4c1d95" },
  UseCase:      { fill: "#cffafe", stroke: "#67e8f9", text: "#164e63" },
  Persona:      { fill: "#fef3c7", stroke: "#fcd34d", text: "#78350f" },
  ValueDriver:  { fill: "#d1fae5", stroke: "#6ee7b7", text: "#065f46" },
  // Fallback mappings for lowercase types
  capability:   { fill: "#ede9fe", stroke: "#c4b5fd", text: "#4c1d95" },
  usecase:      { fill: "#cffafe", stroke: "#67e8f9", text: "#164e63" },
  persona:      { fill: "#fef3c7", stroke: "#fcd34d", text: "#78350f" },
  valuedriver:  { fill: "#d1fae5", stroke: "#6ee7b7", text: "#065f46" },
};

export default function GraphExplorer() {
  const [selected, setSelected] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState("Graph Explorer");
  const { graphData, isLoading, error, fetchGraph, selectedNode, selectNode } = useGraphStore();

  useEffect(() => {
    fetchGraph();
  }, [fetchGraph]);

  const handleNodeClick = (nodeId: string) => {
    setSelected(nodeId);
    const node = graphData.nodes.find(n => n.id === nodeId);
    selectNode(node || null);
  };

  const selectedNodeData = graphData.nodes.find(n => n.id === selected);

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
        <SearchInput placeholder="Search graph…"/>
        <Btn variant="ghost">Query Builder</Btn>
        <Btn variant="ghost">Layout: Force ▾</Btn>
        <Btn variant="ghost">Filters ▾</Btn>
        <Btn variant="ghost">Community View</Btn>
        <Btn variant="ghost">Metrics</Btn>
      </Toolbar>

      <div className="flex gap-4">
        {/* Graph canvas */}
        <div className="flex-1 bg-white border border-neutral-200 rounded-lg shadow-sm overflow-hidden">
          {isLoading && (
            <div className="flex items-center justify-center" style={{ minHeight: 380 }}>
              <div className="flex flex-col items-center gap-3 text-neutral-500">
                <Loader2 className="w-8 h-8 animate-spin" />
                <span className="text-sm">Loading knowledge graph...</span>
              </div>
            </div>
          )}

          {error && !isLoading && (
            <div className="flex items-center justify-center" style={{ minHeight: 380 }}>
              <div className="flex flex-col items-center gap-3 text-neutral-500">
                <AlertCircle className="w-8 h-8 text-red-500" />
                <span className="text-sm text-red-600">{error}</span>
                <Btn variant="outline" onClick={() => fetchGraph()} className="text-xs">
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
                <div className="text-[13px] font-bold text-neutral-900">{selectedNodeData.label}</div>
                <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                  selectedNodeData.type === "Capability" || selectedNodeData.type === "capability" ? "bg-violet-100 text-violet-800 border-violet-200" :
                  selectedNodeData.type === "UseCase" || selectedNodeData.type === "usecase"    ? "bg-cyan-100 text-cyan-800 border-cyan-200" :
                  selectedNodeData.type === "Persona" || selectedNodeData.type === "persona"    ? "bg-amber-100 text-amber-800 border-amber-200" :
                  "bg-emerald-100 text-emerald-800 border-emerald-200"
                }`}>
                  {selectedNodeData.type.charAt(0).toUpperCase() + selectedNodeData.type.slice(1)}
                </div>
                <div className="text-[11px] text-neutral-500">
                  Confidence: {Math.round((selectedNodeData.confidence || 0.8) * 100)}%
                </div>
                <div className="flex flex-col gap-1.5 mt-2">
                  <Btn variant="ghost" className="text-[11px] justify-center" onClick={() => fetchGraph(selectedNodeData.id)}>
                    View Subgraph
                  </Btn>
                  <Btn variant="outline" className="text-[11px] justify-center" onClick={() => fetchGraph()}>
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
                {Object.entries(graphData.stats?.node_types || {}).map(([type, count]) => (
                  <div key={type} className="flex items-center gap-2 text-[11px]">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${
                      type === 'Capability' || type === 'capability' ? 'bg-violet-400' :
                      type === 'UseCase' || type === 'usecase' ? 'bg-cyan-400' :
                      type === 'Persona' || type === 'persona' ? 'bg-amber-400' :
                      'bg-emerald-400'
                    }`}/>
                    <span className="text-neutral-500 flex-1">{type}</span>
                    <span className="font-semibold text-neutral-700">{count.toLocaleString()}</span>
                  </div>
                ))}
              </div>
            </div>
          </SectionCard>
        </div>
      </div>
    </div>
  );
}

// Simple force-directed layout for nodes without positions
function calculateLayout(nodes: GraphNode[], edges: GraphEdge[]) {
  const width = 640;
  const height = 460;
  const centerX = width / 2;
  const centerY = height / 2;

  // If nodes already have positions, use them
  const positionedNodes = nodes.map((node, index) => {
    if (node.x !== undefined && node.y !== undefined) {
      return { ...node, x: node.x, y: node.y };
    }

    // Simple circular layout for nodes without positions
    const angle = (index / nodes.length) * 2 * Math.PI;
    const radius = Math.min(width, height) * 0.35;
    return {
      ...node,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      r: node.type === 'Capability' || node.type === 'capability' ? 20 :
          node.type === 'UseCase' || node.type === 'usecase' ? 18 :
          node.type === 'Persona' || node.type === 'persona' ? 16 : 14
    };
  });

  return positionedNodes;
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
        const c = NODE_COLORS[node.type] || NODE_COLORS['Capability'];
        const isSelected = node.id === selected;
        const words = node.label.split(/\s+/);
        const lines: string[] = [];
        for (const word of words) {
          const lastLine = lines[lines.length - 1];
          if (!lastLine || (lastLine + ' ' + word).length > 12) {
            lines.push(word);
          } else {
            lines[lines.length - 1] = lastLine + ' ' + word;
          }
        }

        if (node.x === undefined || node.y === undefined) return null;

        return (
          <g key={node.id} onClick={() => onNodeClick(node.id)} style={{ cursor: "pointer" }}>
            <circle
              cx={node.x} cy={node.y} r={node.r || 18}
              fill={c.fill}
              stroke={isSelected ? "#1d4ed8" : c.stroke}
              strokeWidth={isSelected ? 2.5 : 1.5}
            />
            {lines.map((line: string, li: number) => (
              <text
                key={li}
                x={node.x} y={(node.y || 0) + (li - (lines.length - 1) / 2) * 11 + 1}
                textAnchor="middle" dominantBaseline="middle"
                fontSize="8" fontFamily="Inter, sans-serif" fontWeight="600"
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
