/**
 * Screen 3 — Ontology Entity Browser
 * Design: Refined Enterprise SaaS
 * Data Flow: React Query for server state, Zustand for UI state
 */
import { useState, useMemo } from "react";
import { Plus, Loader2 } from "lucide-react";
import { useEntities, type Entity } from "@/hooks/useEntities";
import { useEntityUIStore, type Entity as EntityTypeDef } from "@/stores";
import {
  PageHeader, EntityBadge, DataTable, Toolbar, SearchInput, Btn, SectionCard, Tabs
} from "@/components/WfPrimitives";
import type { EntityType } from "@/components/WfPrimitives";

const CONF_COLORS = (c: number) =>
  c >= 90 ? "text-emerald-700 font-semibold" : c >= 80 ? "text-amber-700" : "text-red-600";

const mapEntityType = (type: string): EntityType => {
  const mapping: Record<string, EntityType> = {
    'Capability': 'capability',
    'UseCase': 'usecase',
    'Persona': 'persona',
    'ValueDriver': 'valuedriver',
  };
  return mapping[type] || 'capability';
};

export default function OntologyBrowser() {
  const [activeTab, setActiveTab] = useState("Entity Browser");

  // Server state: React Query
  const { data: entities = [], isLoading, error, refetch } = useEntities();

  // UI state: Zustand
  const { searchQuery, selectedType, setSearchQuery, setSelectedType, clearFilters } = useEntityUIStore();

  // Client-side filtering
  const filteredEntities = useMemo(() => {
    let result = entities;
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      result = result.filter((e: Entity) => e.name.toLowerCase().includes(query));
    }
    if (selectedType) {
      result = result.filter((e: Entity) => e.type === selectedType);
    }
    return result;
  }, [entities, searchQuery, selectedType]);

  const errorMessage = error
    ? (error as any).response?.data?.detail || (error as Error).message
    : null;

  return (
    <div className="p-6 max-w-5xl">
      <PageHeader
        breadcrumbs={["Ontology", "Entity Browser"]}
        title="Entity Browser"
        subtitle="Browse and manage extracted ontology entities across all domains."
        actions={<Btn variant="primary"><Plus size={12}/> New Entity</Btn>}
      />

      <Tabs
        tabs={["Entity Browser", "Extraction Jobs", "Reference Models", "Validation"]}
        active={activeTab}
        onChange={setActiveTab}
      />

      {/* Error display */}
      {errorMessage && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-center justify-between">
            <span className="text-red-700 text-sm">{errorMessage}</span>
            <Btn variant="ghost" className="text-[11px]" onClick={() => refetch()}>Retry</Btn>
          </div>
        </div>
      )}

      {/* Filter toolbar */}
      <Toolbar>
        <SearchInput
          placeholder="Search entities…"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
        <Btn
          variant={selectedType ? "primary" : "ghost"}
          onClick={() => setSelectedType(selectedType ? null : 'Capability')}
        >
          Type: {selectedType || 'All'} ▾
        </Btn>
        <Btn variant="ghost" onClick={clearFilters}>Clear Filters</Btn>
      </Toolbar>

      {/* Type legend chips */}
      <div className="flex gap-2 mb-4 flex-wrap">
        {(["capability","usecase","persona","valuedriver"] as EntityType[]).map(t => (
          <button key={t} onClick={() => setSelectedType(selectedType === t ? null : t)} className="cursor-pointer">
            <EntityBadge type={t}/>
          </button>
        ))}
      </div>

      <SectionCard noPad>
        {isLoading ? (
          <div className="flex items-center justify-center p-12">
            <Loader2 size={24} className="animate-spin text-blue-600" />
            <span className="ml-2 text-neutral-500">Loading entities...</span>
          </div>
        ) : (
          <DataTable
            columns={["Entity Name", "Type", "Confidence", "Status", "Actions"]}
            rows={filteredEntities.map((e: Entity | EntityTypeDef) => [
              <span className="font-semibold text-neutral-800">{e.name}</span>,
              <EntityBadge type={mapEntityType(e.type)}/>,
              <span className={`text-[12px] ${CONF_COLORS(e.confidence)}`}>{e.confidence}%</span>,
              <span className={`text-[11px] font-semibold ${e.confidence >= 90 ? "text-emerald-700" : "text-amber-600"}`}>
                {e.confidence >= 90 ? "● Validated" : "○ Pending"}
              </span>,
              <div className="flex gap-2">
                <button className="text-blue-600 text-[11px] hover:underline">View</button>
                <button className="text-neutral-400 text-[11px] hover:underline">Edit</button>
              </div>,
            ])}
          />
        )}
        {filteredEntities.length === 0 && !isLoading && (
          <div className="text-center p-8 text-neutral-500">
            {searchQuery || selectedType ? 'No entities match your filters.' : 'No entities found.'}
          </div>
        )}
      </SectionCard>
    </div>
  );
}
