/**
 * Route Manifest - Canonical Implementation
 *
 * CONTRACT.md §2.6 - UI State Progression and Route Model
 *
 * State-machine-driven navigation with declarative route manifests.
 * URL paths map to state machine states; the state machine determines
 * valid transitions. Navigation is performed through the canonical
 * navigate() function.
 *
 * Copy this file as the starting point for routing in new frontend applications.
 */

import { getTenantContext, type UserTier } from "../context/tenant-context";

// ============================================================================
// Types
// ============================================================================

/** Application state identifier */
export type StateId =
  | "dashboard"
  | "analytics"
  | "analytics_view"
  | "analytics_export"
  | "settings"
  | "settings_profile"
  | "settings_billing"
  | "report_builder"
  | "report_view"
  | "login"
  | "unauthorized"
  | string; // Allow extension

/** Route guard function - pure predicate */
export type RouteGuard = (ctx: NavigationContext) => boolean | Promise<boolean>;

/** Side effect function for onEnter */
export type EnterEffect = (ctx: NavigationContext) => void | Promise<void>;

/** Navigation transition action */
export type TransitionAction = string;

/** Navigation context passed to guards and effects */
export interface NavigationContext {
  /** Current state */
  currentState: StateId;

  /** Target state for transition */
  targetState: StateId;

  /** URL parameters */
  params: Record<string, string>;

  /** Query string parameters */
  query: Record<string, string>;

  /** Tenant context if authenticated */
  tenantContext?: {
    tenant_id: string;
    tier: UserTier;
    scope: string[];
  };

  /** History stack for back navigation */
  history: StateId[];
}

/** State definition in route manifest */
export interface StateDefinition {
  /** Unique state identifier */
  state: StateId;

  /** URL pattern (e.g., "/dashboard", "/analytics/:reportId") */
  route: string;

  /** Route guards - all must pass for navigation to succeed */
  guards: RouteGuard[];

  /** Side effects to run on entry (after guards pass) */
  onEnter: EnterEffect[];

  /** Valid transitions from this state */
  transitions: Record<TransitionAction, StateId>;

  /** Metadata for analytics/UI */
  meta?: {
    title?: string;
    icon?: string;
    parent?: StateId;
  };
}

/** Complete route manifest type */
export type RouteManifest = Record<string, StateDefinition>;

/** Navigation result */
export interface NavigationResult {
  success: boolean;
  state?: StateId;
  error?: {
    code: "GUARD_REJECTED" | "INVALID_TRANSITION" | "STATE_NOT_FOUND";
    message: string;
  };
}

/** Navigation options */
export interface NavigateOptions {
  /** Replace current history entry instead of pushing */
  replace?: boolean;

  /** Query parameters to include */
  query?: Record<string, string>;

  /** Preserve current scroll position */
  preserveScroll?: boolean;
}

// ============================================================================
// Canonical Route Manifest
// ============================================================================

/**
 * Example route manifest demonstrating the canonical pattern.
 *
 * CONTRACT.md §2.6:
 * - States have guards, onEnter effects, and transitions
 * - URL is serialization of state, not authority
 * - Invalid transitions are prevented
 *
 * Copy and modify this manifest for your application.
 */
export const routeManifest: RouteManifest = {
  // Dashboard - main entry point
  "/dashboard": {
    state: "dashboard",
    guards: [requireTenantContext, requireActiveSession],
    onEnter: [trackPageView("dashboard"), fetchDashboardData],
    transitions: {
      VIEW_ANALYTICS: "analytics",
      MANAGE_SETTINGS: "settings",
      CREATE_REPORT: "report_builder",
    },
    meta: {
      title: "Dashboard",
      icon: "dashboard",
    },
  },

  // Analytics list view
  "/analytics": {
    state: "analytics",
    guards: [requireTenantContext, requirePermission("analytics:read")],
    onEnter: [trackPageView("analytics"), loadAnalyticsList],
    transitions: {
      BACK: "dashboard",
      VIEW_REPORT: "analytics_view",
    },
    meta: {
      title: "Analytics",
      icon: "analytics",
      parent: "dashboard",
    },
  },

  // Individual analytics report view
  "/analytics/:reportId": {
    state: "analytics_view",
    guards: [requireTenantContext, requirePermission("analytics:read")],
    onEnter: [trackPageView("analytics_view"), loadReport],
    transitions: {
      BACK: "analytics",
      EXPORT: "analytics_export",
      SHARE: "analytics_share",
    },
    meta: {
      title: "Report View",
      icon: "report",
      parent: "analytics",
    },
  },

  // Analytics export workflow
  "/analytics/export/:reportId": {
    state: "analytics_export",
    guards: [requireTenantContext, requirePermission("analytics:export")],
    onEnter: [trackPageView("analytics_export"), initializeExport],
    transitions: {
      COMPLETE: "analytics_view",
      CANCEL: "analytics_view",
    },
    meta: {
      title: "Export Report",
      icon: "download",
      parent: "analytics_view",
    },
  },

  // Settings section
  "/settings": {
    state: "settings",
    guards: [requireTenantContext],
    onEnter: [trackPageView("settings")],
    transitions: {
      BACK: "dashboard",
      PROFILE: "settings_profile",
      BILLING: "settings_billing",
    },
    meta: {
      title: "Settings",
      icon: "settings",
    },
  },

  // Report builder workflow
  "/reports/build": {
    state: "report_builder",
    guards: [requireTenantContext, requirePermission("reports:create")],
    onEnter: [trackPageView("report_builder"), initializeBuilder],
    transitions: {
      CANCEL: "dashboard",
      SAVE: "report_view",
    },
    meta: {
      title: "Build Report",
      icon: "builder",
    },
  },

  // Login (unauthenticated)
  "/login": {
    state: "login",
    guards: [], // No guards - accessible when unauthenticated
    onEnter: [trackPageView("login")],
    transitions: {
      AUTHENTICATE: "dashboard",
    },
    meta: {
      title: "Login",
    },
  },

  // Unauthorized page
  "/unauthorized": {
    state: "unauthorized",
    guards: [],
    onEnter: [trackPageView("unauthorized")],
    transitions: {
      BACK: "dashboard",
    },
    meta: {
      title: "Unauthorized",
    },
  },
};

// ============================================================================
// Navigation Service
// ============================================================================

/**
 * Navigation state and history management.
 *
 * CONTRACT.md §2.6:
 * - State machine is the authority for navigation validity
 * - URL is a reflection of current state
 * - Browser history is not the source of truth
 */
class NavigationService {
  private currentState: StateId = "login";
  private stateHistory: StateId[] = [];
  private maxHistorySize = 50;

  /**
   * Navigate to a new state.
   *
   * CONTRACT.md §2.6:
   * - Validates transition is valid before executing
   * - Invalid transitions are no-ops with warnings
   * - Only programmatic navigation via this function
   *
   * @param targetState State to navigate to
   * @param params URL parameters for the state
   * @param options Navigation options
   * @returns Navigation result
   *
   * @example
   * ```typescript
   * // CORRECT: Use navigate() with state ID
   * navigate("analytics_view", { reportId: "123" });
   *
   * // WRONG: Don't use router.push with paths
   * // router.push(`/analytics/${reportId}`) // ❌ ANTI-PATTERN
   * ```
   */
  async navigate(
    targetState: StateId,
    params: Record<string, string> = {},
    options: NavigateOptions = {}
  ): Promise<NavigationResult> {
    // Find target state definition
    const targetRoute = this.findRouteByState(targetState);
    if (!targetRoute) {
      console.warn(`[Navigation] State not found: ${targetState}`);
      return {
        success: false,
        error: { code: "STATE_NOT_FOUND", message: `State "${targetState}" not found` },
      };
    }

    // Build navigation context
    const ctx: NavigationContext = {
      currentState: this.currentState,
      targetState,
      params,
      query: options.query || {},
      history: [...this.stateHistory],
      tenantContext: this.getTenantContext(),
    };

    // Validate transition from current state
    const currentRoute = this.findRouteByState(this.currentState);
    if (currentRoute) {
      const validTransitions = Object.values(currentRoute.transitions);
      if (!validTransitions.includes(targetState)) {
        // Check if there's a direct transition action
        const hasTransition = Object.entries(currentRoute.transitions).some(
          ([, state]) => state === targetState
        );

        if (!hasTransition) {
          console.warn(
            `[Navigation] Invalid transition: ${this.currentState} -> ${targetState}`
          );
          return {
            success: false,
            error: {
              code: "INVALID_TRANSITION",
              message: `Cannot navigate from "${this.currentState}" to "${targetState}"`,
            },
          };
        }
      }
    }

    // Run route guards
    for (const guard of targetRoute.guards) {
      const passes = await guard(ctx);
      if (!passes) {
        console.warn(`[Navigation] Guard rejected: ${targetState}`);
        return {
          success: false,
          error: { code: "GUARD_REJECTED", message: `Navigation to "${targetState}" rejected` },
        };
      }
    }

    // Execute onEnter effects
    try {
      for (const effect of targetRoute.onEnter) {
        await effect(ctx);
      }
    } catch (error) {
      console.error(`[Navigation] onEnter effect failed:`, error);
      // Rollback - keep current state
      return {
        success: false,
        error: { code: "GUARD_REJECTED", message: "Failed to enter state" },
      };
    }

    // Update state and history
    if (!options.replace) {
      this.stateHistory.push(this.currentState);
      if (this.stateHistory.length > this.maxHistorySize) {
        this.stateHistory.shift();
      }
    }
    this.currentState = targetState;

    // Update URL (serialization of state)
    const url = this.buildUrl(targetRoute.route, params, options.query);
    this.updateBrowserUrl(url, options.replace);

    // Dispatch navigation event
    this.dispatchNavigationEvent(targetState, url);

    return { success: true, state: targetState };
  }

  /**
   * Navigate back using state machine history.
   *
   * CONTRACT.md §2.6:
   * - Uses state machine history stack, not browser history
   * - Respects workflow constraints
   */
  async back(): Promise<NavigationResult> {
    if (this.stateHistory.length === 0) {
      return {
        success: false,
        error: { code: "INVALID_TRANSITION", message: "No history to navigate back" },
      };
    }

    const previousState = this.stateHistory.pop()!;
    return this.navigate(previousState, {}, { replace: true });
  }

  /**
   * Get the current state.
   */
  getCurrentState(): StateId {
    return this.currentState;
  }

  /**
   * Get the state history.
   */
  getHistory(): StateId[] {
    return [...this.stateHistory];
  }

  /**
   * Handle deep linking - URL to state translation.
   *
   * CONTRACT.md §2.6:
   * - URL translated to state on load
   * - If target invalid, redirect to nearest valid ancestor
   */
  async handleDeepLink(url: string): Promise<NavigationResult> {
    // Parse URL to find matching route
    for (const [path, definition] of Object.entries(routeManifest)) {
      const params = this.matchRoute(path, url);
      if (params !== null) {
        return this.navigate(definition.state, params);
      }
    }

    // No matching route - redirect to dashboard or login
    const defaultState = this.getTenantContext() ? "dashboard" : "login";
    return this.navigate(defaultState);
  }

  // ========================================================================
  // Private Methods
  // ========================================================================

  private findRouteByState(state: StateId): StateDefinition | undefined {
    return Object.values(routeManifest).find((def) => def.state === state);
  }

  private getTenantContext(): NavigationContext["tenantContext"] {
    const ctx = getTenantContext();
    if (!ctx) return undefined;

    return {
      tenant_id: ctx.tenant_id,
      tier: ctx.tenant_tier,
      scope: ctx.scope,
    };
  }

  private matchRoute(routePattern: string, url: string): Record<string, string> | null {
    // Simple route matching - production would use proper router
    const pattern = routePattern.replace(/:\w+/g, "([^/]+)");
    const regex = new RegExp(`^${pattern}$`);
    const match = url.match(regex);

    if (!match) return null;

    // Extract params
    const params: Record<string, string> = {};
    const paramNames = routePattern.match(/:(\w+)/g) || [];
    paramNames.forEach((name, index) => {
      params[name.slice(1)] = match[index + 1];
    });

    return params;
  }

  private buildUrl(
    routePattern: string,
    params: Record<string, string>,
    query?: Record<string, string>
  ): string {
    // Replace params in pattern
    let url = routePattern;
    for (const [key, value] of Object.entries(params)) {
      url = url.replace(`:${key}`, encodeURIComponent(value));
    }

    // Add query string
    if (query && Object.keys(query).length > 0) {
      const queryString = new URLSearchParams(query).toString();
      url += `?${queryString}`;
    }

    return url;
  }

  private updateBrowserUrl(url: string, replace = false): void {
    if (typeof window === "undefined") return;

    if (replace) {
      window.history.replaceState({}, "", url);
    } else {
      window.history.pushState({}, "", url);
    }
  }

  private dispatchNavigationEvent(state: StateId, url: string): void {
    if (typeof window === "undefined") return;

    window.dispatchEvent(
      new CustomEvent("fabric:navigation", {
        detail: { state, url, timestamp: Date.now() },
      })
    );
  }
}

// ============================================================================
// Singleton Export
// ============================================================================

export const navigationService = new NavigationService();

/**
 * Canonical navigate function.
 *
 * CONTRACT.md §2.6:
 * - Centralized navigation function for all navigation
 * - Validates transitions before executing
 * - Handles URL generation correctly
 *
 * @example
 * ```typescript
 * // Navigate to analytics report
 * navigate("analytics_view", { reportId: "123" });
 *
 * // Navigate with query params
 * navigate("analytics", {}, { query: { filter: "active" } });
 *
 * // Replace instead of push
 * navigate("settings", {}, { replace: true });
 * ```
 */
export function navigate(
  state: StateId,
  params?: Record<string, string>,
  options?: NavigateOptions
): Promise<NavigationResult> {
  return navigationService.navigate(state, params, options);
}

/**
 * Navigate back using state machine history.
 */
export function navigateBack(): Promise<NavigationResult> {
  return navigationService.back();
}

// ============================================================================
// Enter Effects (Examples)
// ============================================================================

function trackPageView(page: string): EnterEffect {
  return () => {
    // Analytics tracking
    console.log(`[Analytics] Page view: ${page}`);
  };
}

function fetchDashboardData(): EnterEffect {
  return async () => {
    // Fetch dashboard data
    console.log("[Data] Fetching dashboard data...");
  };
}

function loadAnalyticsList(): EnterEffect {
  return async () => {
    console.log("[Data] Loading analytics list...");
  };
}

function loadReport(): EnterEffect {
  return async (ctx) => {
    console.log(`[Data] Loading report: ${ctx.params.reportId}`);
  };
}

function initializeExport(): EnterEffect {
  return async (ctx) => {
    console.log(`[Export] Initializing export for report: ${ctx.params.reportId}`);
  };
}

function initializeBuilder(): EnterEffect {
  return async () => {
    console.log("[Builder] Initializing report builder...");
  };
}

// ============================================================================
// Route Guards (imported from guards.ts)
// ============================================================================

import { requireTenantContext, requireActiveSession, requirePermission } from "./guards";
