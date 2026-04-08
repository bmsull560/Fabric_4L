/**
 * Screen 5 — Value Trees: Tree Explorer
 * Design: Refined Enterprise SaaS
 */
import { useState } from "react";
import { ChevronDown, ChevronRight, Plus, Upload, Download } from "lucide-react";
import { PageHeader, Btn, Toolbar, Tabs } from "@/components/WfPrimitives";
import { EntityBadge } from "@/components/WfPrimitives";
import type { EntityType } from "@/components/WfPrimitives";

interface TreeNode {
  label: string;
  type: EntityType;
  children?: TreeNode[];
}

const TREE: TreeNode = {
  label: "Revenue Enhancement", type: "valuedriver",
  children: [
    {
      label: "Sales Director", type: "persona",
      children: [
        {
          label: "Automated Pipeline Forecasting", type: "usecase",
          children: [
            { label: "CRM Integration",     type: "capability" },
            { label: "Predictive Analytics", type: "capability" },
            { label: "Data Ingestion",       type: "capability" },
          ],
        },
      ],
    },
    {
      label: "CFO", type: "persona",
      children: [
        {
          label: "Touchless Accounts Payable", type: "usecase",
          children: [
            { label: "Automated Invoice Parsing", type: "capability" },
            { label: "ERP Integration",           type: "capability" },
          ],
        },
      ],
    },
    {
      label: "Cost Reduction", type: "valuedriver",
      children: [
        { label: "IT Operations Manager", type: "persona" },
      ],
    },
  ],
};

const TYPE_COLORS: Record<EntityType, string> = {
  valuedriver: "bg-emerald-50 border-emerald-200 text-emerald-900",
  persona:     "bg-amber-50  border-amber-200  text-amber-900",
  usecase:     "bg-cyan-50   border-cyan-200   text-cyan-900",
  capability:  "bg-violet-50 border-violet-200 text-violet-900",
};

function TreeNodeView({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div className="flex flex-col items-center">
      <div
        className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg border text-[11px] font-semibold cursor-pointer select-none min-w-[120px] max-w-[140px] text-center ${TYPE_COLORS[node.type]}`}
        onClick={() => setOpen(o => !o)}
      >
        <EntityBadge type={node.type}/>
        <span className="leading-tight">{node.label}</span>
        {hasChildren && (
          <span className="text-[9px] opacity-50">{open ? "▲" : "▼"}</span>
        )}
      </div>
      {hasChildren && open && (
        <div className="flex flex-col items-center">
          <div className="w-px h-4 bg-neutral-300"/>
          <div className="flex gap-4 items-start">
            {node.children!.map((child, i) => (
              <div key={i} className="flex flex-col items-center">
                <div className="w-px h-4 bg-neutral-300"/>
                <TreeNodeView node={child} depth={depth + 1}/>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function OutlineNode({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 2);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <div
        className="flex items-center gap-1.5 py-1 text-[12px] hover:bg-neutral-100 rounded px-1 cursor-pointer"
        style={{ paddingLeft: `${depth * 16 + 4}px` }}
        onClick={() => setOpen(o => !o)}
      >
        {hasChildren ? (
          open ? <ChevronDown size={11} className="text-neutral-400"/> : <ChevronRight size={11} className="text-neutral-400"/>
        ) : (
          <span className="w-[11px] text-neutral-300 text-[10px]">─</span>
        )}
        <EntityBadge type={node.type}/>
        <span className="text-neutral-700">{node.label}</span>
      </div>
      {hasChildren && open && node.children!.map((child, i) => (
        <OutlineNode key={i} node={child} depth={depth + 1}/>
      ))}
    </div>
  );
}

export default function ValueTreeExplorer() {
  const [activeTab, setActiveTab] = useState("Tree Explorer");
  const [view, setView] = useState<"visual"|"outline">("visual");

  return (
    <div className="p-6">
      <PageHeader
        breadcrumbs={["Value Trees", "Tree Explorer"]}
        title="Tree Explorer"
        subtitle="Visualize and edit normalized value hierarchies."
        actions={
          <>
            <Btn variant="ghost">Select Tree ▾</Btn>
            <Btn variant="primary"><Plus size={12}/> New Tree</Btn>
            <Btn variant="ghost"><Upload size={12}/> Import</Btn>
            <Btn variant="ghost"><Download size={12}/> Export</Btn>
          </>
        }
      />

      <Tabs
        tabs={["Tree Explorer", "Normalization", "Formulas"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      <div className="flex gap-2 mb-4">
        <Btn variant={view === "visual" ? "primary" : "ghost"} onClick={() => setView("visual")}>Visual</Btn>
        <Btn variant={view === "outline" ? "primary" : "ghost"} onClick={() => setView("outline")}>Outline</Btn>
      </div>

      {view === "visual" ? (
        <div className="bg-white border border-neutral-200 rounded-lg p-8 overflow-x-auto shadow-sm">
          <div className="flex justify-center min-w-[700px]">
            <TreeNodeView node={TREE}/>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-sm">
          <OutlineNode node={TREE}/>
        </div>
      )}
    </div>
  );
}
