/**
 * Global Component Library
 * 
 * Single import source for all shared components across the application.
 * Organized by category for discoverability.
 * 
 * @example
 * ```tsx
 * import { 
 *   AppShell, 
 *   PageShell, 
 *   Button, 
 *   Card, 
 *   toast 
 * } from "@/components";
 * ```
 */

// ── Layout / Shell Components ─────────────────────────────────────────────────

export { default as AppShell } from "./AppShell";
export { default as Layout } from "./layout/Layout";
export { PageShell } from "./layout/PageShell";

// ── Navigation ─────────────────────────────────────────────────────────────────

export { TieredNav, type UserTier } from "./navigation/TieredNav";

// ── UI Primitives (shadcn/ui) ──────────────────────────────────────────────────

export * from "./ui/accordion";
export * from "./ui/alert";
export * from "./ui/alert-dialog";
export * from "./ui/aspect-ratio";
export * from "./ui/avatar";
export * from "./ui/badge";
export * from "./ui/breadcrumb";
export * from "./ui/button";
export * from "./ui/button-group";
export * from "./ui/calendar";
export * from "./ui/card";
export * from "./ui/carousel";
export * from "./ui/chart";
export * from "./ui/checkbox";
export * from "./ui/collapsible";
export * from "./ui/command";
export * from "./ui/context-menu";
export * from "./ui/dialog";
export * from "./ui/drawer";
export * from "./ui/dropdown-menu";
export * from "./ui/empty";
export * from "./ui/field";
export * from "./ui/form";
export * from "./ui/hover-card";
export * from "./ui/input";
export * from "./ui/input-group";
export * from "./ui/input-otp";
export * from "./ui/item";
export * from "./ui/kbd";
export * from "./ui/label";
export * from "./ui/menubar";
export * from "./ui/navigation-menu";
export * from "./ui/pagination";
export * from "./ui/popover";
export * from "./ui/progress";
export * from "./ui/radio-group";
export * from "./ui/resizable";
export * from "./ui/scroll-area";
export * from "./ui/select";
export * from "./ui/separator";
export * from "./ui/sheet";
export * from "./ui/sidebar";
export * from "./ui/skeleton";
export * from "./ui/slider";
export * from "./ui/sonner";
export * from "./ui/spinner";
export * from "./ui/switch";
export * from "./ui/table";
export * from "./ui/tabs";
export * from "./ui/textarea";
export * from "./ui/toggle";
export * from "./ui/toggle-group";
export * from "./ui/tooltip";

// ── Domain Components (Fabric-specific) ───────────────────────────────────────

export {
  PageHeader,
  FabricCard,
  FilterBar,
  StatusBadge,
  MetricCard,
  DataTable,
  SidePanel,
  FabricDialog,
  TeamMemberList,
  LoadingSkeleton,
  EntityBadge,
} from "./ui/fabric";

// ── Shared Contextual Components ───────────────────────────────────────────────

export { default as ErrorBoundary } from "./ErrorBoundary";
export { default as ValueNarrativeHero } from "./ValueNarrativeHero";
export { QueryState } from "./QueryState";

// ── Graph Components ───────────────────────────────────────────────────────────

export { GraphVisualization } from "./graph/GraphVisualization";
export { GraphInspectorPanel } from "./graph/GraphInspectorPanel";

// ── Ontology Components ────────────────────────────────────────────────────────

export { PropertyEditor } from "./ontology/PropertyEditor";
export { RelationshipMap } from "./ontology/RelationshipMap";
export { TypeTree } from "./ontology/TypeTree";

// ── Integration Components ───────────────────────────────────────────────────

export { IntegrationConfigPanel } from "./integrations/IntegrationConfigPanel";
export { IntegrationGrid } from "./integrations/IntegrationGrid";
export { IntegrationList } from "./integrations/IntegrationList";

// ── Auth Components ────────────────────────────────────────────────────────────

export { SSOButtons } from "./auth/SSOButtons";

// ── Error Handling & Loading States ───────────────────────────────────────────

export { ErrorFallback, InlineError, SectionError } from "./ui/ErrorFallback";
export {
  SkeletonLine,
  SkeletonText,
  SkeletonCard,
  SkeletonTable,
  SkeletonTableRow,
  SkeletonPage,
  SkeletonStats,
  SkeletonForm,
} from "./ui/SkeletonViews";

// ── ValuePack Framework Components ─────────────────────────────────────────────

export {
  ValuePackCard,
  ValuePackCardSkeleton,
  ValuePackDetail,
  type ValuePackFrameworkData,
  type OntologyMapData,
  type TemplateLibraryData,
  type ValuePackComparisonData,
  type ValuePackSuggestion,
  type ProspectProfile,
} from "./valuepack";

// ── Re-export toast utilities for convenience ──────────────────────────────────

export { toast } from "sonner";
