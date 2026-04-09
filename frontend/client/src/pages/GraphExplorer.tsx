/**
 * Screen 7 — Knowledge Graph Explorer
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { PageHeader, Btn, Toolbar, SearchInput, GraphLegend, SectionCard, Tabs } from "@/components/WfPrimitives";

// Node positions for SVG force-directed-style layout
const NODES = [
  { id: "vd1",  label: "Revenue\nEnhancement",    type: "valuedriver", x: 340, y: 80,  r: 28 },
  { id: "per1", label: "Sales Dir.",              type: "persona",     x: 180, y: 180, r: 22 },
  { id: "per2", label: "CFO",                     type: "persona",     x: 480, y: 180, r: 22 },
  { id: "uc1",  label: "Pipeline\nForecast",      type: "usecase",     x: 120, y: 290, r: 22 },
  { id: "uc2",  label: "Touchless AP",            type: "usecase",     x: 420, y: 290, r: 22 },
  { id: "uc3",  label: "Demand\nForecast",        type: "usecase",     x: 560, y: 290, r: 22 },
  { id: "uc4",  label: "Churn\nReduction",        type: "usecase",     x: 280, y: 290, r: 22 },
  { id: "cap1", label: "CRM\nIntegr.",            type: "capability",  x: 60,  y: 400, r: 18 },
  { id: "cap2", label: "Predictive\nAnalytics",   type: "capability",  x: 180, y: 400, r: 20 },
  { id: "cap3", label: "ERP\nIntegr.",            type: "capability",  x: 380, y: 400, r: 18 },
  { id: "cap4", label: "Real-Time\nIngestion",    type: "capability",  x: 520, y: 400, r: 18 },
  { id: "cap5", label: "Data\nIngestion",         type: "capability",  x: 280, y: 400, r: 18 },
  { id: "cap6", label: "Invoice\nParsing",        type: "capability",  x: 460, y: 400, r: 18 },
];

const EDGES = [
  ["vd1","per1"],["vd1","per2"],
  ["per1","uc1"],["per1","uc4"],
  ["per2","uc2"],["per2","uc3"],
  ["uc1","cap1"],["uc1","cap2"],["uc1","cap5"],
  ["uc2","cap3"],["uc2","cap6"],
  ["uc3","cap4"],
  ["uc4","cap2"],["uc4","cap5"],
];

const NODE_COLORS: Record<string, { fill: string; stroke: string; text: string }> = {
  valuedriver: { fill: "#d1fae5", stroke: "#6ee7b7", text: "#065f46" },
  persona:     { fill: "#fef3c7", stroke: "#fcd34d", text: "#78350f" },
  usecase:     { fill: "#cffafe", stroke: "#67e8f9", text: "#164e63" },
  capability:  { fill: "#ede9fe", stroke: "#c4b5fd", text: "#4c1d95" },
};

export default function GraphExplorer() {
  const [selected, setSelected] = useState("cap2");
  const [activeTab, setActiveTab] = useState("Graph Explorer");

  const selectedNode = NODES.find(n => n.id === selected);

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
          <svg viewBox="0 0 640 460" className="w-full" style={{ minHeight: 380 }}>
            {/* Grid */}
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#f3f4f6" strokeWidth="1"/>
              </pattern>
            </defs>
            <rect width="640" height="460" fill="url(#grid)"/>

            {/* Edges */}
            {EDGES.map(([a, b], i) => {
              const na = NODES.find(n => n.id === a)!;
              const nb = NODES.find(n => n.id === b)!;
              return (
                <line
                  key={i}
                  x1={na.x} y1={na.y} x2={nb.x} y2={nb.y}
                  stroke="#d1d5db" strokeWidth="1.5"
                />
              );
            })}

            {/* Nodes */}
            {NODES.map(node => {
              const c = NODE_COLORS[node.type];
              const isSelected = node.id === selected;
              const lines = node.label.split("\n");
              return (
                <g key={node.id} onClick={() => setSelected(node.id)} style={{ cursor: "pointer" }}>
                  <circle
                    cx={node.x} cy={node.y} r={node.r}
                    fill={c.fill}
                    stroke={isSelected ? "#1d4ed8" : c.stroke}
                    strokeWidth={isSelected ? 2.5 : 1.5}
                  />
                  {lines.map((line, li) => (
                    <text
                      key={li}
                      x={node.x} y={node.y + (li - (lines.length - 1) / 2) * 11 + 1}
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

          {/* Legend */}
          <div className="px-4 py-3 border-t border-neutral-100">
            <GraphLegend/>
          </div>
        </div>

        {/* Right panel */}
        <div className="w-[220px] shrink-0 space-y-3">
          {/* Selected node */}
          <SectionCard title="Selected Node">
            {selectedNode ? (
              <div className="space-y-2">
                <div className="text-[13px] font-bold text-neutral-900">{selectedNode.label.replace("\n", " ")}</div>
                <div className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                  selectedNode.type === "capability" ? "bg-violet-100 text-violet-800 border-violet-200" :
                  selectedNode.type === "usecase"    ? "bg-cyan-100 text-cyan-800 border-cyan-200" :
                  selectedNode.type === "persona"    ? "bg-amber-100 text-amber-800 border-amber-200" :
                  "bg-emerald-100 text-emerald-800 border-emerald-200"
                }`}>
                  {selectedNode.type.charAt(0).toUpperCase() + selectedNode.type.slice(1)}
                </div>
                <div className="flex flex-col gap-1.5 mt-2">
                  <Btn variant="primary" className="text-[11px] justify-center">View Details</Btn>
                  <Btn variant="ghost" className="text-[11px] justify-center">Expand Neighbors</Btn>
                  <Btn variant="ghost" className="text-[11px] justify-center">Find Path</Btn>
                  <Btn variant="outline" className="text-[11px] justify-center">Hide</Btn>
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
                { label: "Nodes",       value: "8,532" },
                { label: "Edges",       value: "24,156" },
                { label: "Communities", value: "47" },
                { label: "Density",     value: "0.03" },
              ].map(s => (
                <div key={s.label} className="flex justify-between text-[12px]">
                  <span className="text-neutral-500">{s.label}</span>
                  <span className="font-bold text-neutral-800">{s.value}</span>
                </div>
              ))}
              <div className="border-t border-neutral-100 pt-2 mt-1 space-y-1">
                {[
                  { label: "Capabilities", value: "2,847", color: "bg-violet-400" },
                  { label: "Use Cases",    value: "1,923", color: "bg-cyan-400" },
                  { label: "Personas",     value: "1,456", color: "bg-amber-400" },
                  { label: "Value Drivers",value: "892",   color: "bg-emerald-400" },
                ].map(s => (
                  <div key={s.label} className="flex items-center gap-2 text-[11px]">
                    <div className={`w-2 h-2 rounded-full shrink-0 ${s.color}`}/>
                    <span className="text-neutral-500 flex-1">{s.label}</span>
                    <span className="font-semibold text-neutral-700">{s.value}</span>
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
