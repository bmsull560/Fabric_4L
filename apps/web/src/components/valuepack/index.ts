/**
 * ValuePack Framework Components
 * 
 * UI components for the ValuePack Framework v1.0 system.
 */

export { ValuePackCard, ValuePackCardSkeleton } from "./ValuePackCard";
export { ValuePackDetail } from "./ValuePackDetail";

// Re-export types from hooks for convenience
export type {
  ValuePackFrameworkData,
  OntologyMapData,
  TemplateLibraryData,
  ValuePackComparisonData,
  ValuePackSuggestion,
  ProspectProfile,
} from "@/hooks/useValuePacks";
