/**
 * Screen 4 — Entity Detail
 * Design: Refined Enterprise SaaS
 *
 * Displays full entity details fetched from L3 Knowledge Graph API.
 * Route: /context/ontology/entities/:entityId
 *
 * Connected hooks:
 * - useEntity (detail by ID with relationships and provenance)
 * - useEntities (for related entities list)
 */
import { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useNavigation } from "@/hooks";
import {
  ArrowLeft, Zap, ExternalLink, Clock, Shield, GitBranch,
  AlertCircle, ChevronRight
} from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useEntity, useEntities, type Entity } from "@/hooks/useEntities";
import { cn } from "@/lib/utils";
import { SectionCard } from "@/components/blocks/SectionCard";
import { Btn } from "@/components/ui/fabric";
import { EntityBadge } from "@/lib/entity-colors";

// ── Helpers ──────────────────────────────────────────────────────────────────────────────
function confidenceColor(c: number) {
  if (c >= 0.9) return "text-emerald-700 font-semibold";
  if (c >= 0.7) return "text-amber-700";
  return "text-red-600";
}

function statusBadge(status: string) {
  const map: Record<string, string> = {
    validated: "bg-emerald-100 text-emerald-800",
    pending: "bg-amber-100 text-amber-800",
    draft: "bg-neutral-100 text-neutral-700",
    deprecated: "bg-red-100 text-red-700",
  };
  return (
    <span className={cn("px-2 py-0.5 rounded-full text-[10px] font-semibold uppercase", map[status] || map.draft)}>
      {status}
    </span>
  );
}

function formatDate(iso?: string) {
  if (!iso) return "\u2014";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ── Main Component ───────────────────────────────────────────────────────────────────────
export default function EntityDetail() {
  const params = useParams<{ entityId: string }>();
  const { navigateTo } = useNavigation();
  const entityId = params.entityId || null;
  const [activeTab, setActiveTab] = useState("details");

  // Fetch entity detail (includes relationships and provenance)
  const { data: entity, isLoading, error } = useEntity(entityId);

  // Fetch related entities from the same domain for context
  const { data: relatedData } = useEntities(
    entity ? { domains: entity.domain ? [entity.domain] : undefined, limit: 5 } : undefined
  );
  const relatedEntities = relatedData?.results?.filter((e: Entity) => e.id !== entityId) ?? [];

  // ── Loading State ──────────────────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <div className="p-6 max-w-4xl">
        <div className="flex items-center gap-2 mb-6">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-4 w-4" />
          <Skeleton className="h-4 w-32" />
        </div>
        <Skeleton className="h-8 w-64 mb-2" />
        <Skeleton className="h-4 w-48 mb-6" />
        <div className="grid grid-cols-4 gap-4 mb-6">
          {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-20" />)}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  // ── Error State ────────────────────────────────────────────────────────────────────────
  if (error || !entity) {
    return (
      <div className="p-6 max-w-4xl">
        <Btn variant="ghost" onClick={() => navigateTo('entity-browser')}>
          <ArrowLeft size={14} className="mr-1" /> Back to Entity Browser
        </Btn>
        <div className="mt-8 text-center">
          <AlertCircle size={48} className="mx-auto text-red-400 mb-3" />
          <h2 className="text-lg font-bold text-neutral-800 mb-1">Entity Not Found</h2>
          <p className="text-sm text-neutral-500">
            {error?.message || `Entity "${entityId}" could not be loaded.`}
          </p>
        </div>
      </div>
    );
  }

  // ── Render ───────────────────────────────────────────────────────────────────────────
  const tabs = ["details", "relationships", "provenance", "related"];

  return (
    <div className="p-6 max-w-4xl">
      {/* Breadcrumb */}
      <div className="mb-4 text-[11px] text-neutral-400 flex items-center gap-1">
        <Link to="/context/ontology/entities" className="hover:text-neutral-600 cursor-pointer">
          Ontology
        </Link>
        <ChevronRight size={10} />
        <Link to="/context/ontology/entities" className="hover:text-neutral-600 cursor-pointer">
          Entity Browser
        </Link>
        <ChevronRight size={10} />
        <span className="text-neutral-600">{entity.name}</span>
      </div>

      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-xl bg-violet-100 flex items-center justify-center">
            <Zap size={20} className="text-violet-600" />
          </div>
          <div>
            <h1 className="text-[22px] font-extrabold text-neutral-900">{entity.name}</h1>
            <div className="flex items-center gap-3 mt-1">
              <EntityBadge type={entity.type.toLowerCase()} />
              {statusBadge(entity.status)}
              <span className={cn("text-[12px]", confidenceColor(entity.confidence))}>
                {Math.round(entity.confidence * 100)}% confidence
              </span>
            </div>
          </div>
        </div>
        <Btn variant="ghost" onClick={() => navigateTo('entity-browser')}>
          <ArrowLeft size={14} className="mr-1" /> Back
        </Btn>
      </div>

      {/* Metadata Cards */}
      <div className="grid grid-cols-4 gap-3 mb-6">
        <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Domain</div>
          <div className="text-[13px] font-semibold text-neutral-800 truncate">{entity.domain || "\u2014"}</div>
        </div>
        <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Source</div>
          <div className="text-[13px] font-semibold text-neutral-800 truncate">{entity.sourceName || "\u2014"}</div>
        </div>
        <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Updated</div>
          <div className="text-[13px] font-semibold text-neutral-800">{formatDate(entity.updatedAt)}</div>
        </div>
        <div className="p-3 bg-neutral-50 rounded-lg border border-neutral-100">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Created</div>
          <div className="text-[13px] font-semibold text-neutral-800">{formatDate(entity.createdAt)}</div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-neutral-200 mb-4">
        {tabs.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-4 py-2.5 text-[12px] font-semibold border-b-2 -mb-px transition-colors capitalize",
              activeTab === tab
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-neutral-500 hover:text-neutral-800"
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "details" && (
        <SectionCard>
          <div className="space-y-4">
            {entity.description && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Description</div>
                <p className="text-[13px] text-neutral-700 leading-relaxed">{entity.description}</p>
              </div>
            )}
            {entity.properties && Object.keys(entity.properties).length > 0 && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-2">Properties</div>
                <div className="space-y-1.5">
                  {Object.entries(entity.properties).map(([key, value]) => (
                    <div key={key} className="flex items-center gap-2 text-[12px]">
                      <span className="text-neutral-500 font-medium w-[140px] shrink-0">{key}:</span>
                      <span className="text-neutral-800">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {entity.extractionJobId && (
              <div>
                <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">Extraction Job</div>
                <div className="text-[12px] text-neutral-600 font-mono">{entity.extractionJobId}</div>
              </div>
            )}
            {!entity.description && (!entity.properties || Object.keys(entity.properties).length === 0) && (
              <div className="text-[12px] text-neutral-400 text-center py-4">
                No additional details available for this entity.
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {activeTab === "relationships" && (
        <SectionCard>
          <div className="text-[12px] text-neutral-500 mb-3">
            <GitBranch size={14} className="inline mr-1" />
            Relationships loaded from the Knowledge Graph. View the full graph at{" "}
            <Link to="/context/ontology/graph" className="text-blue-600 hover:underline">
              Graph Explorer
            </Link>.
          </div>
          <div className="space-y-2">
            <div className="text-[11px] font-semibold text-neutral-600 uppercase tracking-wider mb-2">
              Connected Entities in {entity.domain || "this domain"}
            </div>
            {relatedEntities.length > 0 ? (
              relatedEntities.map((rel: Entity) => (
                <Link
                  key={rel.id}
                  to={`/context/ontology/entities/${encodeURIComponent(rel.id)}`}
                  className="flex items-center gap-3 p-2.5 bg-neutral-50 rounded-md border border-neutral-100 hover:border-blue-200 transition-colors cursor-pointer"
                >
                  <EntityBadge type={rel.type.toLowerCase()} />
                  <span className="text-[12px] font-semibold text-neutral-800 flex-1">{rel.name}</span>
                  <span className={cn("text-[11px]", confidenceColor(rel.confidence))}>
                    {Math.round(rel.confidence * 100)}%
                  </span>
                  <ExternalLink size={12} className="text-neutral-400" />
                </Link>
              ))
            ) : (
              <div className="text-[12px] text-neutral-400 text-center py-4">
                No related entities found in this domain.
              </div>
            )}
          </div>
        </SectionCard>
      )}

      {activeTab === "provenance" && (
        <SectionCard>
          <div className="space-y-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-400 mb-1">
                <Shield size={12} className="inline mr-1" />
                Data Lineage
              </div>
              <div className="text-[12px] text-neutral-700 space-y-1.5 mt-2">
                <div className="flex items-center gap-2">
                  <Clock size={12} className="text-neutral-400" />
                  <span>Created: {formatDate(entity.createdAt)}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Clock size={12} className="text-neutral-400" />
                  <span>Last updated: {formatDate(entity.updatedAt)}</span>
                </div>
                {entity.createdBy && (
                  <div className="flex items-center gap-2">
                    <Shield size={12} className="text-neutral-400" />
                    <span>Created by: {entity.createdBy}</span>
                  </div>
                )}
                {entity.sourceName && (
                  <div className="flex items-center gap-2">
                    <ExternalLink size={12} className="text-neutral-400" />
                    <span>Source: {entity.sourceName}</span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </SectionCard>
      )}

      {activeTab === "related" && (
        <SectionCard>
          <div className="text-[11px] font-semibold text-neutral-600 uppercase tracking-wider mb-3">
            Other entities from {entity.domain || "this domain"}
          </div>
          {relatedEntities.length > 0 ? (
            <div className="space-y-2">
              {relatedEntities.map((rel: Entity) => (
                <Link
                  key={rel.id}
                  to={`/context/ontology/entities/${encodeURIComponent(rel.id)}`}
                  className="flex items-center gap-3 p-2.5 bg-neutral-50 rounded-md border border-neutral-100 hover:border-blue-200 transition-colors cursor-pointer"
                >
                  <EntityBadge type={rel.type.toLowerCase()} />
                  <div className="flex-1">
                    <div className="text-[12px] font-semibold text-neutral-800">{rel.name}</div>
                    <div className="text-[11px] text-neutral-500">{rel.status}</div>
                  </div>
                  <span className={cn("text-[11px]", confidenceColor(rel.confidence))}>
                    {Math.round(rel.confidence * 100)}%
                  </span>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-[12px] text-neutral-400 text-center py-4">
              No related entities found.
            </div>
          )}
        </SectionCard>
      )}
    </div>
  );
}
