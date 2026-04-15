/**
 * Screen 5 — Value Trees: Tree Explorer
 * Design: Refined Enterprise SaaS
 * 
 * Features:
 * - Fetch value trees from Layer 3 API using entity_id
 * - Visual tree view with collapsible nodes
 * - Outline/compact view alternative
 * - Entity selector to choose root entity
 * - Loading, error, and empty states
 */
import { useState, useMemo } from "react";
import { useSearchParams } from "wouter";
import { 
  ChevronDown, 
  ChevronRight, 
  Plus, 
  Upload, 
  Download, 
  Loader2, 
  AlertCircle,
  RefreshCw,
  Search,
  TreeDeciduous
} from "lucide-react";
import { PageHeader, Btn, Toolbar, Tabs, SectionCard } from "@/components/WfPrimitives";
import { EntityBadge } from "@/components/WfPrimitives";
import type { EntityType } from "@/components/WfPrimitives";
import { Skeleton } from "@/components/ui/skeleton";
import { useValueTree } from "@/hooks/useValueTrees";
import { useEntities } from "@/hooks/useEntities";
import type { ValueTreeNode, ValueTreeEdge } from "@/api/valueTrees";

// Types for UI tree rendering
interface TreeNode {
  id: string;
  label: string;
  type: EntityType;
  children?: TreeNode[];
}

// Map backend entity types to UI EntityType
type BackendEntityType = 'Capability' | 'UseCase' | 'Persona' | 'ValueDriver' | string;

function mapEntityType(type: BackendEntityType): EntityType {
  const mapping: Record<string, EntityType> = {
    'Capability': 'capability',
    'UseCase': 'usecase',
    'Persona': 'persona',
    'ValueDriver': 'valuedriver',
  };
  return mapping[type] || 'capability';
}

// Constants for UI truncation
const ENTITY_ID_SHORT_LENGTH = 12;
const ENTITY_ID_LIST_LENGTH = 16;

// Build hierarchical tree from flat nodes/edges
function buildTree(nodes: ValueTreeNode[], edges: ValueTreeEdge[], rootId: string): TreeNode | null {
  if (!nodes.length) return null;

  // Create node map for quick lookup
  const nodeMap = new Map<string, ValueTreeNode>();
  nodes.forEach(node => nodeMap.set(node.id, node));

  // Build adjacency list (parent -> children)
  const childrenMap = new Map<string, string[]>();
  edges.forEach(edge => {
    const list = childrenMap.get(edge.source) || [];
    list.push(edge.target);
    childrenMap.set(edge.source, list);
  });

  // Recursive tree builder
  function buildNode(nodeId: string): TreeNode | null {
    const node = nodeMap.get(nodeId);
    if (!node) return null;

    const childIds = childrenMap.get(nodeId) || [];
    const children = childIds
      .map(childId => buildNode(childId))
      .filter((child): child is TreeNode => child !== null);

    return {
      id: node.id,
      label: node.label,
      type: mapEntityType(node.type),
      children: children.length > 0 ? children : undefined,
    };
  }

  return buildNode(rootId);
}

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
              <div key={child.id} className="flex flex-col items-center">
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
      {hasChildren && open && node.children!.map((child) => (
        <OutlineNode key={child.id} node={child} depth={depth + 1}/>
      ))}
    </div>
  );
}

function ValueTreeSkeleton({ view }: { view: "visual" | "outline" }) {
  if (view === "visual") {
    return (
      <div className="bg-white border border-neutral-200 rounded-lg p-8 overflow-x-auto shadow-sm">
        <div className="flex justify-center min-w-[700px]">
          {/* Skeleton tree structure */}
          <div className="flex flex-col items-center gap-4">
            <Skeleton className="h-16 w-32 rounded-lg" />
            <div className="w-px h-8 bg-neutral-200" />
            <div className="flex gap-8">
              {[1, 2, 3].map(i => (
                <div key={i} className="flex flex-col items-center gap-4">
                  <div className="w-px h-8 bg-neutral-200" />
                  <Skeleton className="h-14 w-28 rounded-lg" />
                  <div className="w-px h-6 bg-neutral-200" />
                  <div className="flex gap-4">
                    <Skeleton className="h-10 w-24 rounded-lg" />
                    <Skeleton className="h-10 w-24 rounded-lg" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-sm">
      <div className="space-y-2">
        {[1, 2, 3, 4, 5, 6, 7, 8].map(i => (
          <Skeleton key={i} className="h-6" style={{ marginLeft: `${Math.min(i, 3) * 16}px` }} />
        ))}
      </div>
    </div>
  );
}

export default function ValueTreeExplorer() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [activeTab, setActiveTab] = useState("Tree Explorer");
  const [view, setView] = useState<"visual"|"outline">("visual");
  const [showEntitySelector, setShowEntitySelector] = useState(false);
  
  // Get entity_id from URL or null
  const entityId = searchParams.get("entityId");
  
  // Fetch value tree data
  const { 
    data: treeData, 
    isLoading: treeLoading, 
    error: treeError,
    refetch: refetchTree 
  } = useValueTree(entityId, { 
    direction: 'upward', 
    maxDepth: 4 
  });

  // Fetch available entities for selection
  const { data: entities = [], isLoading: entitiesLoading } = useEntities();

  // Build hierarchical tree for rendering
  const tree = useMemo(() => {
    if (!treeData) return null;
    return buildTree(treeData.nodes, treeData.edges, treeData.root_entity_id);
  }, [treeData]);

  // Stats for display
  const stats = useMemo(() => {
    if (!treeData) return null;
    return {
      totalNodes: treeData.stats.total_nodes,
      totalEdges: treeData.stats.total_edges,
      maxDepth: treeData.stats.max_depth,
      byLayer: treeData.stats.by_layer,
    };
  }, [treeData]);

  // Handle entity selection
  const handleSelectEntity = (id: string) => {
    setSearchParams({ entityId: id });
    setShowEntitySelector(false);
  };

  // Filter entities that could be tree roots (ValueDrivers or Capabilities)
  const rootCandidates = useMemo(() => {
    return entities.filter(entity => 
      entity.type === 'ValueDriver' || entity.type === 'Capability' || entity.type === 'UseCase'
    );
  }, [entities]);

  return (
    <div className="p-6 max-w-6xl">
      <PageHeader
        breadcrumbs={["Value Trees", "Tree Explorer"]}
        title="Tree Explorer"
        subtitle={entityId 
          ? `Visualizing value hierarchy from entity: ${entityId.slice(0, ENTITY_ID_SHORT_LENGTH)}...`
          : "Select an entity to visualize its value hierarchy."
        }
        actions={
          <>
            <div className="relative">
              <Btn 
                variant="ghost" 
                onClick={() => setShowEntitySelector(!showEntitySelector)}
                className={showEntitySelector ? "bg-neutral-100" : ""}
              >
                {entityId ? "Change Root Entity ▾" : "Select Tree ▾"}
              </Btn>
              {showEntitySelector && (
                <div className="absolute top-full right-0 mt-1 w-80 bg-white border border-neutral-200 rounded-lg shadow-lg z-50">
                  <div className="p-3 border-b border-neutral-100">
                    <div className="flex items-center gap-2 text-[12px] text-neutral-500">
                      <Search size={12} />
                      <span>Select root entity</span>
                    </div>
                  </div>
                  <div className="max-h-64 overflow-y-auto p-2 space-y-1">
                    {entitiesLoading ? (
                      <div className="p-4 text-center text-neutral-500 text-[12px]">
                        <Loader2 size={14} className="animate-spin inline mr-2" />
                        Loading entities...
                      </div>
                    ) : rootCandidates.length === 0 ? (
                      <div className="p-4 text-center text-neutral-500 text-[12px]">
                        No entities available. 
                        <a href="/discover/knowledge/entities" className="text-blue-600 hover:underline ml-1">
                          Browse entities
                        </a>
                      </div>
                    ) : (
                      rootCandidates.map(entity => (
                        <button
                          key={entity.id}
                          onClick={() => handleSelectEntity(entity.id)}
                          className={`w-full text-left px-3 py-2 rounded-lg text-[12px] transition-colors ${
                            entityId === entity.id 
                              ? "bg-blue-50 text-blue-700" 
                              : "hover:bg-neutral-50 text-neutral-700"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <EntityBadge type={mapEntityType(entity.type)} />
                            <span className="font-medium truncate">{entity.name}</span>
                          </div>
                          <div className="text-[10px] text-neutral-400 mt-1">
                            {entity.id.slice(0, ENTITY_ID_LIST_LENGTH)}...
                          </div>
                        </button>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>
            <Btn variant="primary" disabled><Plus size={12}/> New Tree</Btn>
            <Btn variant="ghost" disabled><Upload size={12}/> Import</Btn>
            <Btn 
              variant="ghost" 
              onClick={() => {
                // Export as JSON
                if (treeData) {
                  const blob = new Blob([JSON.stringify(treeData, null, 2)], { type: 'application/json' });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement('a');
                  a.href = url;
                  a.download = `value-tree-${entityId}.json`;
                  a.click();
                  URL.revokeObjectURL(url);
                }
              }}
              disabled={!treeData}
            >
              <Download size={12}/> Export
            </Btn>
          </>
        }
      />

      <Tabs
        tabs={["Tree Explorer", "Normalization", "Formulas"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      {/* Stats bar */}
      {stats && (
        <div className="flex gap-4 mb-4">
          <SectionCard className="flex-1 py-3">
            <div className="flex items-center gap-4 text-[12px]">
              <div>
                <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Nodes</span>
                <p className="font-bold text-neutral-800 text-[18px]">{stats.totalNodes}</p>
              </div>
              <div className="w-px h-8 bg-neutral-200" />
              <div>
                <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Edges</span>
                <p className="font-bold text-neutral-800 text-[18px]">{stats.totalEdges}</p>
              </div>
              <div className="w-px h-8 bg-neutral-200" />
              <div>
                <span className="text-neutral-400 uppercase tracking-wider text-[10px]">Max Depth</span>
                <p className="font-bold text-neutral-800 text-[18px]">{stats.maxDepth}</p>
              </div>
              <div className="ml-auto flex gap-2">
                {Object.entries(stats.byLayer).map(([layer, count]) => (
                  <div key={layer} className="text-center px-2 py-1 bg-neutral-50 rounded">
                    <span className="text-[10px] text-neutral-400">L{layer}</span>
                    <p className="font-semibold text-neutral-700">{count}</p>
                  </div>
                ))}
              </div>
            </div>
          </SectionCard>
        </div>
      )}

      <div className="flex gap-2 mb-4">
        <Btn variant={view === "visual" ? "primary" : "ghost"} onClick={() => setView("visual")}>Visual</Btn>
        <Btn variant={view === "outline" ? "primary" : "ghost"} onClick={() => setView("outline")}>Outline</Btn>
        {tree && (
          <Btn variant="ghost" className="ml-auto text-[11px]" onClick={() => refetchTree()}>
            <RefreshCw size={12} className="mr-1" /> Refresh
          </Btn>
        )}
      </div>

      {/* Loading State */}
      {treeLoading && <ValueTreeSkeleton view={view} />}

      {/* Error State */}
      {!treeLoading && treeError && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-8 text-center">
          <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-3" />
          <h3 className="text-[14px] font-semibold text-red-800 mb-1">Failed to load value tree</h3>
          <p className="text-[12px] text-red-600 mb-4">
            {treeError instanceof Error ? treeError.message : 'An unexpected error occurred'}
          </p>
          <div className="flex justify-center gap-2">
            <Btn variant="outline" onClick={() => refetchTree()}>
              <RefreshCw size={12} className="mr-1" /> Retry
            </Btn>
          </div>
        </div>
      )}

      {/* Empty State - No entity selected */}
      {!entityId && !treeLoading && !treeError && (
        <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-12 text-center">
          <TreeDeciduous className="w-12 h-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-[14px] font-semibold text-neutral-700 mb-2">No Entity Selected</h3>
          <p className="text-[12px] text-neutral-500 mb-4 max-w-md mx-auto">
            Select a root entity (Value Driver, Persona, or Capability) to visualize its value hierarchy.
          </p>
          <Btn variant="primary" onClick={() => setShowEntitySelector(true)}>
            <Search size={12} className="mr-1" /> Select Entity
          </Btn>
        </div>
      )}

      {/* Empty State - No tree data */}
      {entityId && !treeLoading && !treeError && !tree && (
        <div className="bg-neutral-50 border border-neutral-200 rounded-lg p-12 text-center">
          <TreeDeciduous className="w-12 h-12 text-neutral-300 mx-auto mb-4" />
          <h3 className="text-[14px] font-semibold text-neutral-700 mb-2">No Value Tree Found</h3>
          <p className="text-[12px] text-neutral-500 mb-4 max-w-md mx-auto">
            This entity doesn&apos;t have any connected value relationships. Try selecting a different entity or create relationships in the knowledge graph.
          </p>
          <Btn variant="outline" onClick={() => setShowEntitySelector(true)}>
            Select Different Entity
          </Btn>
        </div>
      )}

      {/* Success State - Tree Display */}
      {!treeLoading && !treeError && tree && (
        view === "visual" ? (
          <div className="bg-white border border-neutral-200 rounded-lg p-8 overflow-x-auto shadow-sm">
            <div className="flex justify-center min-w-[700px]">
              <TreeNodeView node={tree}/>
            </div>
          </div>
        ) : (
          <div className="bg-white border border-neutral-200 rounded-lg p-4 shadow-sm">
            <OutlineNode node={tree}/>
          </div>
        )
      )}
    </div>
  );
}
