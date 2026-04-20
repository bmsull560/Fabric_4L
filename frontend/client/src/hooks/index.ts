/**
 * Global Hooks Library
 * 
 * Centralized exports for all custom React hooks.
 * 
 * @example
 * ```tsx
 * import { useAuthContext, useGraphQuery, useFormulas } from "@/hooks";
 * ```
 */

// ── Auth Hooks ─────────────────────────────────────────────────────────────────

export { useAuthContext } from "../contexts/AuthContext";

// ── API/Data Hooks ───────────────────────────────────────────────────────────

export { useGraphQuery, useSubgraph, useGraphViewState } from "./useGraphQuery";
export { useFormulas, useFormula, useFormulaApprovals, useApproveFormula, useSubmitFormula } from "./useFormulas";
export { useBenchmarks, useBenchmark, useBenchmarkPolicies, useUpdateBenchmarkPolicy } from "./useBenchmarks";
export { useSources } from "./useSources";
export { useBilling } from "./useBilling";
export { useValuePacks } from "./useValuePacks";

// ── Utility Hooks ─────────────────────────────────────────────────────────────

export { usePersistFn } from "./usePersistFn";
export {
  usePrefersReducedMotion,
  usePrefersHighContrast,
  useFocusTrap,
  useAnnouncer,
  useListKeyboardNavigation,
  useSkipLink,
} from "./useAccessibility";

// ── Domain Hooks ─────────────────────────────────────────────────────────────

export { useUserTierStore } from "../stores/userTierStore";
export type { UserTier } from "../stores/userTierStore";
