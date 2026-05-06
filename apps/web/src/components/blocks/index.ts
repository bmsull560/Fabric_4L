/**
 * Design System — Block Components
 *
 * Extracted from _ui-prototype and adapted for the production frontend.
 * These are higher-level business components built from shadcn/ui and Fabric primitives.
 *
 * These components represent domain-specific UI patterns and should be preferred
 * over lower-level shadcn/Radix primitives in `components/ui/`.
 *
 * Usage:
 *   import { StatCard, StatusBadgeBlock, ProgressBar } from "@/components/blocks";
 *
 * Note: SectionCard is available via direct import from "./SectionCard" to avoid
 * naming conflict with the backward-compatible SectionCard in WfPrimitives.tsx
 */

// ── Metric & Status ──────────────────────────────────────────────────────
export { StatCard } from "./StatCard";
export type { StatCardProps } from "./StatCard";

export { StatusBadgeBlock } from "./StatusBadge";
export type { StatusBadgeBlockProps, Status } from "./StatusBadge";

export { ProgressBar } from "./ProgressBar";
export type { ProgressBarProps } from "./ProgressBar";

// ── Layout ────────────────────────────────────────────────────────────────
// SectionCard exported directly to avoid conflict with WfPrimitives backward-compat wrapper

// ── Navigation ───────────────────────────────────────────────────────────
export { TabNav } from "./TabNav";
export type { TabItem, TabNavProps } from "./TabNav";

export { TopTabNav } from "./TopTabNav";
export type { TopTabItem, TopTabNavProps } from "./TopTabNav";

// ── Value Model ──────────────────────────────────────────────────────────
export { ModelInputsTracker } from "./ModelInputsTracker";
export type { InputStatus, ModelInput, ModelInputsTrackerProps } from "./ModelInputsTracker";

export { ModelReadinessMeter } from "./ModelReadinessMeter";
export type { ReadinessOpportunity, ModelReadinessMeterProps } from "./ModelReadinessMeter";
