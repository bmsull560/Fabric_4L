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
export {
  useFormulas,
  useFormula,
  useFormulaApprovals,
  useApproveFormula,
  useSubmitFormula,
  type Formula,
  type FormulaStatus,
  type ApprovalRequest,
} from "./useFormulas";
export {
  useBenchmarks,
  useBenchmark,
  useBenchmarkPolicies,
  useUpdateBenchmarkPolicy,
  type Benchmark,
  type ConfidenceLevel,
  type BenchmarkStatus,
} from "./useBenchmarks";
export { useSources } from "./useSources";
export { useBilling } from "./useBilling";
export {
  useValuePacks,
  useValuePack,
  useApplyValuePack,
  useValuePackFrameworkList,
  useValuePackOntologyMap,
  useValuePackTemplates,
  useValuePackComparison,
  useSuggestValuePacks,
  type ValuePack,
  type PackStatus,
} from "./useValuePacks";
export {
  useSystemHealth,
  useHealthAlerts,
  type ServiceStatus,
  type ServiceHealth,
  type HealthAlert,
} from "./useHealthMonitor";
export {
  useAccounts,
  useAccount,
  useCreateAccount,
  useAccountFilterOptions,
  useAccountSyncStatus,
  useSyncAccounts,
  useRefreshAccount,
  type Account,
  type CRMProvider,
  type SyncStatus,
  type AccountSyncStatusInfo,
} from "./useAccounts";

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

export {
  useTruths,
  useTruthAuditTrail,
  useTruthFreshnessSummary,
  useStaleTruths,
  useMaturityLadder,
  type TruthStatus,
  type TruthObjectSummary,
  type ValidationEventResponse,
  type MaturityLadderResponse,
} from "./useGroundTruthGovernance";
