/**
 * Navigation Service — Centralized Navigation with State Machine Support
 *
 * Replaces imperative useNavigate() calls with declarative state-based navigation.
 * Per CONTRACT.md §2.6: UI State Progression and Route Model
 *
 * Migration from:
 *   - navigate('/path') → navigateToState('stateId', params)
 *   - URL concatenation → route configuration with parameters
 */

import type { ReactNode } from "react";
import type { NavigateOptions, To } from 'react-router-dom';

// ─────────────────────────────────────────────────────────────────────────────
// Route State Definitions (Contract §2.6)
// ─────────────────────────────────────────────────────────────────────────────

export type RouteState =
  // Auth
  | 'login'
  | 'signup'
  | 'login-callback'
  // Home
  | 'root'
  | 'home'
  | 'command-center'
  // Accounts
  | 'accounts'
  | 'account-detail'
  // Workspaces
  | 'intelligence'
  | 'intelligence-signals'
  | 'account-intelligence'
  | 'hypothesis'
  | 'drivers'
  | 'drivers-evidence'
  | 'calculator'
  | 'value-case'
  | 'realization'
  // Studio (legacy)
  | 'studio'
  // Context Engine
  | 'value-packs'
  | 'my-models'
  | 'model-detail'
  | 'formulas'
  | 'formula-builder'
  | 'formula-new'
  | 'value-trees'
  | 'normalization'
  | 'agent-workflows'
  | 'ontology'
  | 'entity-browser'
  | 'entity-detail'
  | 'graph-explorer'
  | 'ingestion-jobs'
  | 'extraction'
  | 'integrations'
  | 'sources'
  | 'targets'
  // Discover
  | 'opportunities'
  | 'opportunity-scan'
  // Deliverables
  | 'business-cases'
  | 'business-cases-agent'
  | 'business-case-detail'
  | 'business-case-new'
  | 'business-case-interactive'
  // Decision Support
  | 'decision-trace'
  | 'interactive-calculator'
  | 'cfo-view'
  | 'executive-view'
  | 'technical-view'
  // Governance
  | 'governance-traces'
  | 'governance-evidence'
  | 'governance-provenance'
  | 'governance-integrity'
  | 'governance-compliance'
  | 'governance-benchmarks'
  | 'governance-audit-log'
  | 'governance-change-history'
  | 'governance-health'
  // Workflow
  | 'workflow-prospect'
  | 'workflow-intelligence'
  | 'workflow-ai-model'
  | 'workflow-driver-tree'
  | 'workflow-evidence'
  | 'workflow-calculator'
  | 'workflow-value-case'
  // Settings - Personal
  | 'personal-profile'
  | 'personal-security'
  | 'personal-preferences'
  | 'personal-notifications'
  | 'personal-sessions'
  // Settings - Workspace
  | 'settings-workspace'
  | 'settings-subscription'
  | 'settings-usage'
  | 'settings-payment-methods'
  | 'settings-invoices'
  // Settings - Team
  | 'settings-team-members'
  | 'settings-team-invitations'
  | 'settings-team-roles'
  | 'settings-team-permissions'
  | 'settings-team-api-keys'
  // Settings - Data
  | 'settings-data-sources'
  | 'settings-data-integrations'
  | 'settings-data-variables'
  | 'settings-data-value-packs'
  | 'settings-data-ingestion-rules'
  // Settings - Governance
  | 'settings-governance-policies'
  | 'settings-governance-compliance'
  | 'settings-governance-health'
  | 'settings-governance-audit-trail'
  | 'settings-governance-admin-controls'
  // Dev Tools
  | 'dev-integration';

// ─────────────────────────────────────────────────────────────────────────────
// Route Configuration Map
// ─────────────────────────────────────────────────────────────────────────────

interface RouteConfig {
  path: string;
  params?: string[];
}

const ROUTE_MAP: Record<RouteState, RouteConfig> = {
  // Auth
  'login': { path: '/login' },
  'signup': { path: '/signup' },
  'login-callback': { path: '/login/callback' },

  // Home
  'root': { path: '/' },
  'home': { path: '/home' },
  'command-center': { path: '/command-center' },

  // Accounts
  'accounts': { path: '/accounts' },
  'account-detail': { path: '/accounts/:accountId', params: ['accountId'] },

  // Workspaces (account-scoped)
  'intelligence': { path: '/intelligence/:accountId', params: ['accountId'] },
  'intelligence-signals': { path: '/intelligence/:accountId/signals', params: ['accountId'] },
  'account-intelligence': { path: '/accounts/:accountId/intelligence', params: ['accountId'] },
  'hypothesis': { path: '/hypothesis/:accountId', params: ['accountId'] },
  'drivers': { path: '/drivers/:accountId', params: ['accountId'] },
  'drivers-evidence': { path: '/drivers/:accountId/evidence', params: ['accountId'] },
  'calculator': { path: '/calculator/:accountId', params: ['accountId'] },
  'value-case': { path: '/value-case/:accountId', params: ['accountId'] },
  'realization': { path: '/realization/:accountId', params: ['accountId'] },

  // Studio (legacy, account-scoped)
  'studio': { path: '/studio/:accountId', params: ['accountId'] },

  // Context Engine
  'value-packs': { path: '/context/packs' },
  'my-models': { path: '/context/models' },
  'model-detail': { path: '/library/models/:modelId', params: ['modelId'] },
  'formulas': { path: '/context/formulas' },
  'formula-builder': { path: '/context/formulas/:formulaId', params: ['formulaId'] },
  'formula-new': { path: '/model/value-studio/formulas/new' },
  'value-trees': { path: '/context/value-trees/explorer' },
  'normalization': { path: '/model/value-studio/normalization' },
  'agent-workflows': { path: '/context/agents' },
  'ontology': { path: '/context/ontology' },
  'entity-browser': { path: '/context/ontology/entities' },
  'entity-detail': { path: '/context/ontology/entities/:entityId', params: ['entityId'] },
  'graph-explorer': { path: '/context/ontology/graph' },
  'ingestion-jobs': { path: '/context/ingestion/jobs' },
  'extraction': { path: '/context/extraction' },
  'integrations': { path: '/context/integrations' },
  'sources': { path: '/context/sources' },
  'targets': { path: '/context/targets' },

  // Discover
  'opportunities': { path: '/discover/opportunities' },
  'opportunity-scan': { path: '/discover/opportunities/scan' },

  // Deliverables
  'business-cases': { path: '/deliverables/cases' },
  'business-cases-agent': { path: '/agents/business-cases' },
  'business-case-detail': { path: '/deliverables/cases/:caseId', params: ['caseId'] },
  'business-case-new': { path: '/deliverables/cases/new' },
  'business-case-interactive': { path: '/agents/business-cases/explore' },
  'interactive-calculator': { path: '/deliverables/calculators' },
  'decision-trace': { path: '/decision-trace' },
  'cfo-view': { path: '/deliverables/views/cfo' },
  'executive-view': { path: '/deliverables/views/executive' },
  'technical-view': { path: '/deliverables/views/technical' },

  // Governance
  'governance-traces': { path: '/governance/traces' },
  'governance-evidence': { path: '/governance/evidence' },
  'governance-provenance': { path: '/governance/provenance' },
  'governance-integrity': { path: '/governance/integrity' },
  'governance-compliance': { path: '/governance/compliance' },
  'governance-benchmarks': { path: '/governance/benchmarks' },
  'governance-audit-log': { path: '/governance/audit/log' },
  'governance-change-history': { path: '/governance/audit/changes' },
  'governance-health': { path: '/governance/health' },

  // Workflow
  'workflow-prospect': { path: '/workflow/prospect' },
  'workflow-intelligence': { path: '/workflow/intelligence' },
  'workflow-ai-model': { path: '/workflow/ai-model' },
  'workflow-driver-tree': { path: '/workflow/driver-tree' },
  'workflow-evidence': { path: '/workflow/evidence' },
  'workflow-calculator': { path: '/workflow/calculator' },
  'workflow-value-case': { path: '/workflow/value-case' },

  // Settings - Personal
  'personal-profile': { path: '/personal/profile' },
  'personal-security': { path: '/personal/security' },
  'personal-preferences': { path: '/personal/preferences' },
  'personal-notifications': { path: '/personal/notifications' },
  'personal-sessions': { path: '/personal/sessions' },

  // Settings - Workspace
  'settings-workspace': { path: '/settings/workspace' },
  'settings-subscription': { path: '/settings/billing/subscription' },
  'settings-usage': { path: '/settings/billing/usage' },
  'settings-payment-methods': { path: '/settings/billing/payment-methods' },
  'settings-invoices': { path: '/settings/billing/invoices' },

  // Settings - Team
  'settings-team-members': { path: '/settings/team' },
  'settings-team-invitations': { path: '/settings/team/invitations' },
  'settings-team-roles': { path: '/settings/team/roles' },
  'settings-team-permissions': { path: '/settings/team/permissions' },
  'settings-team-api-keys': { path: '/settings/team/api-keys' },

  // Settings - Data
  'settings-data-sources': { path: '/settings/data/sources' },
  'settings-data-integrations': { path: '/settings/data/integrations' },
  'settings-data-variables': { path: '/settings/data/variables' },
  'settings-data-value-packs': { path: '/settings/data/value-packs' },
  'settings-data-ingestion-rules': { path: '/settings/data/ingestion-rules' },

  // Settings - Governance
  'settings-governance-policies': { path: '/settings/governance/policies' },
  'settings-governance-compliance': { path: '/settings/governance/compliance' },
  'settings-governance-health': { path: '/settings/governance/health' },
  'settings-governance-audit-trail': { path: '/settings/governance/audit-trail' },
  'settings-governance-admin-controls': { path: '/settings/governance/admin-controls' },

  // Dev Tools
  'dev-integration': { path: '/dev/integration' },
};

// ─────────────────────────────────────────────────────────────────────────────
// Navigation Functions
// ─────────────────────────────────────────────────────────────────────────────

export type NavigationParams = Record<string, string | number | undefined>;

/**
 * Build a URL path by substituting parameters into the route template.
 * Replaces URL string concatenation per CONTRACT.md §2.6.
 *
 * @example
 * buildPath('/accounts/:accountId', { accountId: '123' })
 * // Returns: '/accounts/123'
 */
export function buildPath(pathTemplate: string, params: NavigationParams = {}): string {
  let path = pathTemplate;

  for (const [key, value] of Object.entries(params)) {
    if (value === undefined) continue;
    path = path.replace(`:${key}`, String(value));
  }

  // Remove any remaining optional params that weren't provided
  path = path.replace(/\/:[^/]+/g, '');

  return path;
}

/**
 * Get the URL path for a given route state with parameters.
 *
 * @example
 * getStatePath('intelligence', { accountId: '123' })
 * // Returns: '/intelligence/123'
 */
export function getStatePath(state: RouteState, params?: NavigationParams): string {
  const config = ROUTE_MAP[state];
  if (!config) {
    throw new Error(`Unknown route state: ${state}`);
  }
  return buildPath(config.path, params);
}

/**
 * Resolve a navigation target for react-router's navigate() function.
 * This is the primary replacement for imperative navigation.
 *
 * @example
 * // Instead of: navigate(`/intelligence/${accountId}`)
 * // Use: navigate(getNavigateTarget('intelligence', { accountId }))
 */
export function getNavigateTarget(
  state: RouteState,
  params?: NavigationParams
): { to: To; options?: NavigateOptions } {
  const path = getStatePath(state, params);
  return { to: path };
}

/**
 * Check if a route state requires specific parameters.
 */
export function stateRequiresParams(state: RouteState): string[] {
  return ROUTE_MAP[state]?.params ?? [];
}

/**
 * Validate that all required parameters are provided for a route state.
 */
export function validateStateParams(
  state: RouteState,
  params?: NavigationParams
): { valid: boolean; missing: string[] } {
  const required = stateRequiresParams(state);
  const missing = required.filter((param) => params?.[param] === undefined);
  return { valid: missing.length === 0, missing };
}

// ─────────────────────────────────────────────────────────────────────────────
// Legacy Compatibility Helpers (for gradual migration)
// ─────────────────────────────────────────────────────────────────────────────

const ACCOUNT_SCOPED_PREFIXES = [
  '/intelligence',
  '/hypothesis',
  '/drivers',
  '/calculator',
  '/value-case',
  '/realization',
];

/**
 * Resolve a workspace path with an account ID.
 * Replaces the URL concatenation in navHelpers.ts and Layout.tsx
 *
 * @example
 * resolveWorkspacePath('/intelligence', '123')
 * // Returns: '/intelligence/123'
 */
export function resolveWorkspacePath(path: string, accountId: string | null): string {
  if (!accountId) return path;

  for (const prefix of ACCOUNT_SCOPED_PREFIXES) {
    if (path === prefix) {
      return `${prefix}/${accountId}`;
    }
    if (path.startsWith(`${prefix}/`)) {
      const suffix = path.slice(prefix.length + 1);
      return `${prefix}/${accountId}/${suffix}`;
    }
  }

  // Legacy studio routes
  if (path === '/studio') return `/studio/${accountId}`;
  if (path.startsWith('/studio/')) {
    const suffix = path.slice('/studio/'.length);
    return `/studio/${accountId}/${suffix}`;
  }

  return path;
}

/**
 * Map common path patterns to route states.
 * Useful for breadcrumb and navigation highlighting.
 */
export function pathToState(path: string): { state: RouteState | null; params: NavigationParams } {
  // Reverse lookup in ROUTE_MAP
  for (const [state, config] of Object.entries(ROUTE_MAP)) {
    const paramNames = config.params ?? [];

    // Build regex pattern from path template
    let pattern = config.path.replace(/:[^/]+/g, '([^/]+)');
    pattern = '^' + pattern + '$';

    const regex = new RegExp(pattern);
    const match = path.match(regex);

    if (match) {
      const params: NavigationParams = {};
      paramNames.forEach((name, i) => {
        params[name] = match[i + 1];
      });
      return { state: state as RouteState, params };
    }
  }

  return { state: null, params: {} };
}

// ─────────────────────────────────────────────────────────────────────────────
// Re-export for convenience
// ─────────────────────────────────────────────────────────────────────────────

export { ROUTE_MAP };


export type UserTier = "standard" | "advanced" | "admin";

export interface NavItem {
  id: string;
  label: string;
  icon?: ReactNode;
  path: string;
  tier: UserTier;
  children?: NavItem[];
  badge?: string | number;
  description?: string;
}

export function isItemVisible(item: NavItem, userTier: UserTier): boolean {
  if (userTier === "admin") return true;
  if (userTier === "advanced") return item.tier !== "admin";
  return item.tier === "standard";
}

export function isRouteActive(location: string, resolvedPath: string): boolean {
  return location === resolvedPath || location.startsWith(resolvedPath + "/");
}
