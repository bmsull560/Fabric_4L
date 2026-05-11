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
  type ValuePackFilters,
  type ValuePackFrameworkData,
  type OntologyMapData,
  type TemplateLibraryData,
  type ValuePackComparisonData,
  type ValuePackComparisonRequest,
  type ValuePackSuggestion,
  type ProspectProfile,
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
export {
  useTasks,
  useCreateTask,
  useUpdateTask,
  type TaskRecord,
  type TaskStatus,
} from "./useTasks";
export {
  useComments,
  useCreateComment,
  type CommentRecord,
} from "./useComments";
export {
  useNotifications,
  useCreateNotification,
  useMarkNotificationRead,
  type NotificationRecord,
} from "./useNotifications";

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
export {
  usePaginatedList,
  type PaginatedListOptions,
  type PaginatedListState,
} from "./usePaginatedList";

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

// ── Navigation Hooks ─────────────────────────────────────────────────────────

export { useNavigation } from "./useNavigation";
export { useRoutePrefetch } from "./useRoutePrefetch";
export type { RouteState } from "@/navigation/navigationService";
