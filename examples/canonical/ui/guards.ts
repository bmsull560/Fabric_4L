/**
 * Route Guards - Canonical Implementation
 *
 * CONTRACT.md §2.6 - UI State Progression and Route Model
 *
 * Route guards are pure functions that read tenant context and current state
 * to determine if navigation to a target state is permitted.
 *
 * CONTRACT.md §2.6 Rule:
 * - Guards are pure functions with no side effects
 * - Deterministic and testable
 * - Side effects belong in onEnter handlers
 */

import type { NavigationContext, RouteGuard } from "./route-manifest";

// ============================================================================
// Tenant Context Guards
// ============================================================================

/**
 * Guard: Require valid tenant context for navigation.
 *
 * CONTRACT.md §2.1, §2.6:
 * - Most routes require tenant context
 * - Guard reads from NavigationContext (which comes from async scope)
 * - Pure function - no side effects
 *
 * @example
 * ```typescript
 * const routeManifest = {
 *   "/dashboard": {
 *     state: "dashboard",
 *     guards: [requireTenantContext, requireActiveSession],
 *     onEnter: [fetchData],
 *     transitions: { ... },
 *   },
 * };
 * ```
 */
export const requireTenantContext: RouteGuard = (ctx: NavigationContext): boolean => {
  if (!ctx.tenantContext) {
    console.warn(`[Guard] Navigation to "${ctx.targetState}" rejected: No tenant context`);
    return false;
  }

  // Validate tenant ID format (UUIDv4)
  const uuidv4Pattern = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  if (!uuidv4Pattern.test(ctx.tenantContext.tenant_id)) {
    console.warn(`[Guard] Navigation to "${ctx.targetState}" rejected: Invalid tenant ID format`);
    return false;
  }

  return true;
};

/**
 * Guard: Require active user session.
 *
 * Additional check beyond tenant context - ensures user is authenticated.
 * Different from requireTenantContext which validates the tenant exists.
 */
export const requireActiveSession: RouteGuard = (ctx: NavigationContext): boolean => {
  // In production: check session validity, expiration, etc.
  // For now, presence of tenantContext implies active session
  if (!ctx.tenantContext) {
    console.warn(`[Guard] Navigation to "${ctx.targetState}" rejected: No active session`);
    return false;
  }

  return true;
};

// ============================================================================
// Permission Guards
// ============================================================================

/**
 * Create a permission guard for specific scope.
 *
 * CONTRACT.md §2.6:
 * - Guards check permissions from tenant context
 * - Declarative permission requirements in route manifest
 *
 * @param requiredScope Permission scope required (e.g., "analytics:read")
 * @returns RouteGuard that checks for the scope
 *
 * @example
 * ```typescript
 * const routeManifest = {
 *   "/analytics": {
 *     state: "analytics",
 *     guards: [requireTenantContext, requirePermission("analytics:read")],
 *     onEnter: [loadAnalytics],
 *     transitions: { ... },
 *   },
 * };
 * ```
 */
export function requirePermission(requiredScope: string): RouteGuard {
  return (ctx: NavigationContext): boolean => {
    if (!ctx.tenantContext) {
      console.warn(
        `[Guard] Permission check failed for "${ctx.targetState}": No tenant context`
      );
      return false;
    }

    const hasPermission = ctx.tenantContext.scope.includes(requiredScope);

    if (!hasPermission) {
      console.warn(
        `[Guard] Navigation to "${ctx.targetState}" rejected: ` +
          `Missing permission "${requiredScope}". ` +
          `Available: [${ctx.tenantContext.scope.join(", ")}]`
      );
      return false;
    }

    return true;
  };
}

/**
 * Create a guard requiring any of multiple permissions.
 *
 * @param scopes Array of permission scopes - any one grants access
 * @returns RouteGuard that checks for any scope
 *
 * @example
 * ```typescript
 * guards: [requireAnyPermission(["analytics:read", "analytics:admin"])]
 * ```
 */
export function requireAnyPermission(scopes: string[]): RouteGuard {
  return (ctx: NavigationContext): boolean => {
    if (!ctx.tenantContext) {
      console.warn(`[Guard] Permission check failed: No tenant context`);
      return false;
    }

    const hasAnyPermission = scopes.some((scope) => ctx.tenantContext!.scope.includes(scope));

    if (!hasAnyPermission) {
      console.warn(
        `[Guard] Navigation to "${ctx.targetState}" rejected: ` +
          `Missing any of required permissions [${scopes.join(", ")}]. ` +
          `Available: [${ctx.tenantContext.scope.join(", ")}]`
      );
      return false;
    }

    return true;
  };
}

/**
 * Create a guard requiring all of multiple permissions.
 *
 * @param scopes Array of permission scopes - all required
 * @returns RouteGuard that checks for all scopes
 */
export function requireAllPermissions(scopes: string[]): RouteGuard {
  return (ctx: NavigationContext): boolean => {
    if (!ctx.tenantContext) {
      console.warn(`[Guard] Permission check failed: No tenant context`);
      return false;
    }

    const hasAllPermissions = scopes.every((scope) => ctx.tenantContext!.scope.includes(scope));

    if (!hasAllPermissions) {
      const missing = scopes.filter((scope) => !ctx.tenantContext!.scope.includes(scope));
      console.warn(
        `[Guard] Navigation to "${ctx.targetState}" rejected: ` +
          `Missing permissions [${missing.join(", ")}]. ` +
          `Available: [${ctx.tenantContext.scope.join(", ")}]`
      );
      return false;
    }

    return true;
  };
}

// ============================================================================
// Tier Guards
// ============================================================================

/**
 * Create a guard requiring specific tenant tier.
 *
 * Used for features only available to dedicated or enterprise tenants.
 *
 * @param requiredTier The required tier ("dedicated" | "enterprise")
 * @returns RouteGuard that checks tenant tier
 *
 * @example
 * ```typescript
 * "/advanced-features": {
 *   state: "advanced_features",
 *   guards: [requireTenantContext, requireTier("enterprise")],
 *   onEnter: [loadAdvancedFeatures],
 *   transitions: { ... },
 * }
 * ```
 */
export function requireTier(requiredTier: "dedicated" | "enterprise"): RouteGuard {
  return (ctx: NavigationContext): boolean => {
    if (!ctx.tenantContext) {
      console.warn(`[Guard] Tier check failed for "${ctx.targetState}": No tenant context`);
      return false;
    }

    const tierRank = { shared: 1, dedicated: 2, enterprise: 3 };
    const requiredRank = tierRank[requiredTier];
    const actualRank = tierRank[ctx.tenantContext.tier];

    if (actualRank < requiredRank) {
      console.warn(
        `[Guard] Navigation to "${ctx.targetState}" rejected: ` +
          `Requires ${requiredTier} tier, current: ${ctx.tenantContext.tier}`
      );
      return false;
    }

    return true;
  };
}

// ============================================================================
// State Guards
// ============================================================================

/**
 * Guard: Prevent navigation to same state (no-op detection).
 *
 * Useful for preventing redundant navigation attempts.
 */
export const preventDuplicateNavigation: RouteGuard = (ctx: NavigationContext): boolean => {
  if (ctx.currentState === ctx.targetState) {
    // Check if params are also the same
    const urlParams = ctx.params;
    const currentUrl = window.location?.pathname || "";

    // Simple check - in production would parse and compare params
    if (currentUrl.includes(Object.values(urlParams).join("/"))) {
      console.warn(`[Guard] Navigation to same state "${ctx.targetState}" - no action taken`);
      return false;
    }
  }

  return true;
};

/**
 * Create a guard requiring specific query parameters.
 *
 * @param requiredParams Array of required query parameter names
 * @returns RouteGuard that checks for required query params
 */
export function requireQueryParams(requiredParams: string[]): RouteGuard {
  return (ctx: NavigationContext): boolean => {
    const missing = requiredParams.filter((param) => !ctx.query[param]);

    if (missing.length > 0) {
      console.warn(
        `[Guard] Navigation to "${ctx.targetState}" rejected: ` +
          `Missing required query params: [${missing.join(", ")}]`
      );
      return false;
    }

    return true;
  };
}

// ============================================================================
// Async Guards
// ============================================================================

/**
 * Create an async guard that fetches data before allowing navigation.
 *
 * CONTRACT.md §2.6:
 * - Guards are pure functions with no side effects
 * - Data fetching belongs in onEnter, not guards
 * - This is for validation checks that require async (e.g., checking if resource exists)
 *
 * @param validator Async validation function
 * @returns Async RouteGuard
 *
 * @example
 * ```typescript
 * const requireValidReport = createAsyncGuard(async (ctx) => {
 *   const report = await fetchReport(ctx.params.reportId);
 *   return report !== null && report.tenant_id === ctx.tenantContext?.tenant_id;
 * });
 * ```
 */
export function createAsyncGuard(
  validator: (ctx: NavigationContext) => Promise<boolean>
): RouteGuard {
  return async (ctx: NavigationContext): Promise<boolean> => {
    try {
      const isValid = await validator(ctx);
      if (!isValid) {
        console.warn(`[Guard] Async validation failed for "${ctx.targetState}"`);
      }
      return isValid;
    } catch (error) {
      console.error(`[Guard] Async validation error for "${ctx.targetState}":`, error);
      return false;
    }
  };
}

// ============================================================================
// Composite Guards
// ============================================================================

/**
 * Combine multiple guards with AND logic.
 *
 * All guards must pass for navigation to succeed.
 *
 * @param guards Array of guards to combine
 * @returns Combined RouteGuard
 *
 * @example
 * ```typescript
 * guards: [allOf([requireTenantContext, requireActiveSession, requirePermission("admin")])]
 * ```
 */
export function allOf(guards: RouteGuard[]): RouteGuard {
  return async (ctx: NavigationContext): Promise<boolean> => {
    for (const guard of guards) {
      const passes = await guard(ctx);
      if (!passes) return false;
    }
    return true;
  };
}

/**
 * Combine multiple guards with OR logic.
 *
 * Any guard passing allows navigation.
 *
 * @param guards Array of guards to combine
 * @returns Combined RouteGuard
 *
 * @example
 * ```typescript
 * guards: [anyOf([requireTier("enterprise"), requirePermission("beta:access")])]
 * ```
 */
export function anyOf(guards: RouteGuard[]): RouteGuard {
  return async (ctx: NavigationContext): Promise<boolean> => {
    for (const guard of guards) {
      const passes = await guard(ctx);
      if (passes) return true;
    }
    return false;
  };
}

// ============================================================================
// Testing Utilities
// ============================================================================

/**
 * Create a mock navigation context for testing guards.
 *
 * @param overrides Partial context to override defaults
 * @returns Complete NavigationContext for testing
 *
 * @example
 * ```typescript
 * describe("requirePermission guard", () => {
 *   it("should allow navigation with correct permission", async () => {
 *     const ctx = createMockContext({
 *       targetState: "analytics",
 *       tenantContext: { scope: ["analytics:read"] },
 *     });
 *
 *     const result = await requirePermission("analytics:read")(ctx);
 *     expect(result).toBe(true);
 *   });
 * });
 * ```
 */
export function createMockContext(
  overrides: Partial<NavigationContext> = {}
): NavigationContext {
  return {
    currentState: "dashboard",
    targetState: "analytics",
    params: {},
    query: {},
    history: ["login", "dashboard"],
    tenantContext: {
      tenant_id: "550e8400-e29b-41d4-a716-446655440000",
      tier: "shared",
      scope: ["read", "write"],
    },
    ...overrides,
  };
}
