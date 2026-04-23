/**
 * Canonical routing types for Fabric 4L frontend.
 *
 * wouter is the ONLY routing library.
 */

/** Route parameter definitions for typed wouter routes */
export interface RouteParams {
  accountId?: string;
  tab?: string;
  workflowId?: string;
}

/** Workspace domain identifiers */
export type WorkspaceDomain =
  | "intelligence"
  | "studio"
  | "context"
  | "deliverables"
  | "governance"
  | "settings";

/** Route tier requirements for RBAC */
export type RouteTier = "standard" | "advanced" | "admin";

/** Access decision with reason */
export type AccessDecision =
  | { allowed: true }
  | { allowed: false; reason: string };

/** Guard result for route protection */
export interface RouteGuardResult {
  allowed: boolean;
  redirectTo?: string;
  reason?: string;
}
