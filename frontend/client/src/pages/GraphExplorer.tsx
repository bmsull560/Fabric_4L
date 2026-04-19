/**
 * Screen 7 — Knowledge Graph Explorer
 * Refactored: ~180 lines (was 589)
 */
import { useState, useCallback } from "react";
import { Loader2, AlertCircle, RefreshCw, Search, ZoomIn, ZoomOut, RotateCcw, Move } from "lucide-react";
import { PageHeader as WfPageHeader, Btn, SearchInput, GraphLegend, SectionCard } from "@/components/WfPrimitives";
import { Empty, EmptyHeader, EmptyTitle, EmptyDescription, EmptyMedia } from "@/components/ui/empty";
import { PageShell } from "@/components/layout/PageShell";
import { GraphVisualization } from "@/components/graph/GraphVisualization";
import { GraphInspectorPanel } from "@/components/graph/GraphInspectorPanel";
import { useSubgraph, useEntityContext, useGraphQuery } from "@/hooks/useGraphQuery";
import { useGraphCanvas } from "@/hooks/useGraphCanvas";
import { useGraphData } from "@/hooks/useGraphData";
import { getEntityBadgeClasses } from "@/lib/graph-utils";
import { cn } from "@/lib/utils";

export default function GraphExplorer() {
  const [selected, setSelected] = useState<string | null>(null);
  const [queryText, setQueryText] = useState("");
  const [searchError, setSearchError] = useState<string | null>(null);
  const [searchResults, setSearchResults] = useState<{ entities: any[]; relationships: any[] } | null>(null);

  const { data: subgraph, isLoading: subgraphLoading, error: subgraphError, refetch: refetchSubgraph } = useSubgraph({
    query: '',
    depth: 2,
    limit: 100,
  });

  const { data: entityContext, isLoading: contextLoading } = useEntityContext(selected, 2);
  const graphQuery = useGraphQuery();
  const canvas = useGraphCanvas();

  const { data: graphData, isEmpty, nodeTypeCounts } = useGraphData({
    subgraph: subgraph,
    entityContext: entityContext,
    searchResults: searchResults,
  });

  const isLoading = subgraphLoading || contextLoading || graphQuery.isPending;
  const error = subgraphError?.message || graphQuery.error?.message || searchError;

  const handleNodeClick = useCallback((nodeId: string) => {
    setSelected(prev => nodeId === prev ? null : nodeId);
  }, []);

  const handleSearch = async () => {
    if (!queryText.trim()) {
      setSearchResults(null);
      return;
    }
    setSearchError(null);
    try {
      const results = await graphQuery.mutateAsync({
        query: queryText,
        max_hops: 2,
        max_results: 20,
      });
      setSearchResults({
        entities: results.entities,
        relationships: results.relationships,
      });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Search failed';
      setSearchError(message);
    }
  };

  const selectedNodeData = graphData.nodes.find(n => n.id === selected) || null;

  const handleReset = () => {
    setSelected(null);
    setSearchResults(null);
    setQueryText("");
    canvas.actions.resetView();
    refetchSubgraph();
  };

  return (
    <PageShell>
      <WfPageHeader
        breadcrumbs={[{ label: "Knowledge Graph" }, { label: "Graph Explorer" }]}
        title="Graph Explorer"
        subtitle="Visualize and navigate the knowledge graph"
        actions={
          <div className="flex items-center gap-2">
            <Btn variant="ghost" onClick={handleSearch} disabled={!queryText.trim() || graphQuery.isPending}>
              {graphQuery.isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Search className="w-3 h-3" />}
              Search
            </Btn>
            {/* TODO: Implement export */}
            {false && <Btn variant="ghost">Export</Btn>}
            {/* TODO: Implement focus selection */}
            {false && <Btn variant="primary">Focus Selection</Btn>}
          </div>
        }
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
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              />

              {/* Zoom Controls */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">Zoom</div>
                <div className="flex gap-2">
                  <Btn variant="ghost" className="flex-1 text-[11px]" onClick={canvas.actions.zoomIn}>
                    <ZoomIn className="w-3 h-3 mr-1" /> In
                  </Btn>
                  <Btn variant="ghost" className="flex-1 text-[11px]" onClick={canvas.actions.zoomOut}>
                    <ZoomOut className="w-3 h-3 mr-1" /> Out
                  </Btn>
                </div>
                <div className="text-[10px] text-muted-foreground/70 text-center">
                  {Math.round(canvas.view.scale * 100)}%
                </div>
              </div>

              {/* View Controls */}
              <div className="space-y-2">
                <div className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider">View</div>
                <Btn variant="ghost" className="w-full text-[11px] justify-center" onClick={canvas.actions.resetView}>
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
            <div className="flex flex-col items-center justify-center min-h-[380px] gap-4">
              <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Loading knowledge graph...</span>
            </div>
          )}

          {error && !isLoading && (
            <div className="flex items-center justify-center min-h-[380px]">
              <Empty className="border-0">
                <EmptyMedia variant="icon">
                  <AlertCircle className="text-destructive" />
                </EmptyMedia>
                <EmptyHeader>
                  <EmptyTitle className="text-destructive">Error loading graph</EmptyTitle>
                  <EmptyDescription>{error}</EmptyDescription>
                </EmptyHeader>
                <Btn variant="outline" onClick={() => refetchSubgraph()} className="text-xs">
                  <RefreshCw className="w-3 h-3 mr-1" /> Retry
                </Btn>
              </Empty>
            </div>
          )}

          {!isLoading && !error && graphData.nodes.length === 0 && (
            <div className="flex items-center justify-center min-h-[380px]">
              <Empty className="border-0">
                <EmptyHeader>
                  <EmptyTitle>No matching entities found</EmptyTitle>
                  <EmptyDescription>
                    Try adjusting your search query or filters to see more results
                  </EmptyDescription>
                </EmptyHeader>
              </Empty>
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

          {!isLoading && !error && !isEmpty && (
            <div {...canvas.handlers} className="w-full h-full">
              <GraphVisualization
                nodes={graphData.nodes}
                edges={graphData.edges}
                selectedNodeId={selected}
                onNodeClick={handleNodeClick}
                viewTransform={canvas.view}
                isDragging={canvas.isDragging}
                className="w-full h-full"
              />
            </div>
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
    </PageShell>
  );
}
