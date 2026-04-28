/**
 * Design System — Block Components
 *
 * Extracted from _ui-prototype and adapted for the production frontend.
 * These are higher-level, opinionated primitives built on top of Tailwind
 * utility classes and Lucide icons. They complement (not replace) the
 * lower-level shadcn/Radix primitives in `components/ui/`.
 *
 * Usage:
 *   import { StatCard, StatusBadgeBlock, ProgressBar } from "@/components/blocks";
 */

// ── Metric & Status ──────────────────────────────────────────────────────
export { StatCard } from "./StatCard";
export type { StatCardProps } from "./StatCard";

export { StatusBadgeBlock } from "./StatusBadge";
export type { Status, StatusBadgeBlockProps } from "./StatusBadge";

export { ProgressBar } from "./ProgressBar";
export type { ProgressBarProps } from "./ProgressBar";

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
