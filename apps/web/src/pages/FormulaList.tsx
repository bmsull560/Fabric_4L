/**
 * Formula List Page - Browse and manage formulas
 *
 * Route: /model/value-studio/formulas
 * Tier: advanced (Tier 2+)
 *
 * Features:
 * - List all formulas with filters
 * - Create new formula
 * - Edit/delete existing formulas
 * - View formula status and metadata
 */
import { useState } from "react";
import {
  Plus,
  Search,
  Filter,
  ChevronRight,
  Clock,
  CheckCircle2,
  AlertCircle,
  Archive,
  Edit3,
  Trash2,
  Play,
} from "lucide-react";
import { PageHeader, Btn, SectionCard } from "@/components/WfPrimitives";
import {
  useFormulas,
  useDeleteFormula,
  type Formula,
  type FormulaStatus,
} from "@/hooks/useFormulas";
import { useNavigation } from "@/hooks";
import { formatRelativeTime } from "@/lib/formatters";

// ─────────────────────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────────────────────

type StatusFilter = "all" | FormulaStatus;

// ─────────────────────────────────────────────────────────────────────────────
// Status Configuration
// ─────────────────────────────────────────────────────────────────────────────

const STATUS_CONFIG: Record<FormulaStatus, { label: string; color: string; icon: React.ReactNode }> = {
  active: {
    label: "Active",
    color: "bg-emerald-50 text-emerald-700 border-emerald-200",
    icon: <CheckCircle2 size={14} />,
  },
  draft: {
    label: "Draft",
    color: "bg-muted/30 text-muted-foreground border-border",
    icon: <Clock size={14} />,
  },
  pending: {
    label: "Pending",
    color: "bg-amber-50 text-amber-700 border-amber-200",
    icon: <AlertCircle size={14} />,
  },
  deprecated: {
    label: "Deprecated",
    color: "bg-orange-50 text-orange-700 border-orange-200",
    icon: <AlertCircle size={14} />,
  },
  archived: {
    label: "Archived",
    color: "bg-muted/20 text-muted-foreground/60 border-border",
    icon: <Archive size={14} />,
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Components
// ─────────────────────────────────────────────────────────────────────────────

interface FormulaRowProps {
  formula: Formula;
  onEdit: (id: string) => void;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}

function FormulaRow({ formula, onEdit, onDelete, isDeleting }: FormulaRowProps) {
  const status = STATUS_CONFIG[formula.status as FormulaStatus];
  const { navigateTo } = useNavigation();

  return (
    <div className="flex items-center gap-4 p-4 bg-card rounded-lg border border-border hover:border-neutral-300 hover:shadow-sm transition-all group">
      {/* Status Badge */}
      <div className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium border ${status.color}`}>
        {status.icon}
        {status.label}
      </div>

      {/* Formula Info */}
      <div className="flex-1 min-w-0">
        <h3 className="text-[13px] font-semibold text-foreground truncate">
          {formula.name}
        </h3>
        <p className="text-[11px] text-muted-foreground truncate">
          {formula.description || "No description"}
          {formula.pack_name && ` • ${formula.pack_name}`}
        </p>
      </div>

      {/* Metadata */}
      <div className="hidden sm:flex items-center gap-6 text-[11px] text-muted-foreground">
        <div className="text-right">
          <div className="font-medium text-muted-foreground">v{formula.version}</div>
          <div>Version</div>
        </div>
        <div className="text-right">
          <div className="font-medium text-muted-foreground">{formula.used_in_count}</div>
          <div>Used in</div>
        </div>
        <div className="text-right">
          <div className="font-medium text-muted-foreground">
            {formatRelativeTime(formula.updated_at ?? '')}
          </div>
          <div>Updated</div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          onClick={() => navigateTo('formula-builder', { formulaId: formula.id })}
          className="p-2 text-muted-foreground hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
          title="Edit"
        >
          <Edit3 size={16} />
        </button>
        <button
          onClick={() => onEdit(formula.id)}
          className="p-2 text-muted-foreground hover:text-emerald-600 hover:bg-emerald-50 rounded-md transition-colors"
          title="Test"
        >
          <Play size={16} />
        </button>
        <button
          onClick={() => onDelete(formula.id)}
          disabled={isDeleting}
          className="p-2 text-muted-foreground hover:text-red-600 hover:bg-red-50 rounded-md transition-colors disabled:opacity-50"
          title="Delete"
        >
          <Trash2 size={16} />
        </button>
      </div>

      <ChevronRight size={16} className="text-neutral-300" />
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────────
// Main Component
// ─────────────────────────────────────────────────────────────────────────────

export default function FormulaList() {
  const { navigateTo } = useNavigation();
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  // Fetch formulas
  const { data: formulas, isLoading, isError, error } = useFormulas({
    status: statusFilter === "all" ? undefined : statusFilter,
    search: searchQuery || undefined,
  });

  // Delete mutation
  const { mutate: deleteFormula, isPending: isDeleting } = useDeleteFormula();

  // Filter formulas locally for search (API may not support search yet)
  const filteredFormulas = formulas?.filter((f) => {
    if (!searchQuery) return true;
    const query = searchQuery.toLowerCase();
    return (
      f.name.toLowerCase().includes(query) ||
      f.description?.toLowerCase().includes(query) ||
      f.pack_name?.toLowerCase().includes(query)
    );
  });

  const handleDelete = (id: string) => {
    deleteFormula(id, {
      onSuccess: () => {
        setShowDeleteConfirm(null);
      },
    });
  };

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <PageHeader
          breadcrumbs={[{ label: "Value Models" }, { label: "Formula Studio" }]}
          title="Formulas"
          subtitle="Create and manage value calculation formulas"
        />
        <Btn variant="primary" onClick={() => navigateTo('formula-new')}>
          <Plus size={14} /> New Formula
        </Btn>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 mb-6">
        {/* Search */}
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground/60" size={16} />
          <input
            type="text"
            placeholder="Search formulas..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-border rounded-lg text-[13px] focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500"
          />
        </div>

        {/* Status Filter */}
        <div className="flex items-center gap-1 bg-card border border-border rounded-lg p-1">
          {/* All valid statuses from STATUS_CONFIG are filterable. Excluded statuses would require product justification. */}
          {(["all", "active", "draft", "pending", "deprecated", "archived"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setStatusFilter(status)}
              className={`px-3 py-1.5 rounded-md text-[12px] font-medium transition-colors ${
                statusFilter === status
                  ? "bg-neutral-800 text-white"
                  : "text-muted-foreground hover:bg-muted/30"
              }`}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <SectionCard title={`${filteredFormulas?.length || 0} Formulas`} className="min-h-[400px]">
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-neutral-800"></div>
          </div>
        )}

        {isError && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <AlertCircle size={32} className="text-red-400 mb-3" />
            <h3 className="text-[14px] font-semibold text-foreground mb-1">
              Failed to load formulas
            </h3>
            <p className="text-[13px] text-muted-foreground max-w-sm">
              {error?.message || "An error occurred while loading formulas. Please try again."}
            </p>
            <Btn
              variant="ghost"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Retry
            </Btn>
          </div>
        )}

        {!isLoading && !isError && filteredFormulas?.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <div className="w-12 h-12 bg-muted/30 rounded-full flex items-center justify-center mb-3">
              <Filter size={20} className="text-muted-foreground/60" />
            </div>
            <h3 className="text-[14px] font-semibold text-foreground mb-1">
              No formulas found
            </h3>
            <p className="text-[13px] text-muted-foreground max-w-sm">
              {searchQuery
                ? `No formulas matching "${searchQuery}". Try a different search term.`
                : statusFilter !== "all"
                ? `No ${statusFilter} formulas found. Try changing the filter.`
                : "Get started by creating your first formula."}
            </p>
            {!searchQuery && statusFilter === "all" && (
              <Btn
                variant="primary"
                className="mt-4"
                onClick={() => navigateTo('formula-new')}
              >
                <Plus size={14} /> Create Formula
              </Btn>
            )}
          </div>
        )}

        {!isLoading && !isError && filteredFormulas && filteredFormulas.length > 0 && (
          <div className="space-y-2">
            {filteredFormulas.map((formula) => (
              <div
                key={formula.id}
                onClick={() => navigateTo('formula-builder', { formulaId: formula.id })}
                className="cursor-pointer"
              >
                <FormulaRow
                  formula={formula}
                  onEdit={(id) => navigateTo('formula-builder', { formulaId: id })}
                  onDelete={(id) => setShowDeleteConfirm(id)}
                  isDeleting={isDeleting && showDeleteConfirm === formula.id}
                />
              </div>
            ))}
          </div>
        )}
      </SectionCard>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-card rounded-lg p-6 max-w-sm w-full mx-4">
            <h3 className="text-[16px] font-semibold text-foreground mb-2">
              Delete Formula?
            </h3>
            <p className="text-[13px] text-muted-foreground mb-6">
              This action cannot be undone. The formula will be permanently removed from the system.
            </p>
            <div className="flex justify-end gap-3">
              <Btn variant="ghost" onClick={() => setShowDeleteConfirm(null)}>
                Cancel
              </Btn>
              <Btn
                variant="primary"
                className="bg-red-600 hover:bg-red-700"
                onClick={() => handleDelete(showDeleteConfirm)}
                disabled={isDeleting}
              >
                {isDeleting ? "Deleting..." : "Delete"}
              </Btn>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
