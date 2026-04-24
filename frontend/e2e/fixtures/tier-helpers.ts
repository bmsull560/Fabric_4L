/**
 * Tier/permission helpers for access control testing
 *
 * Provides utilities to set user tier and verify route access
 * in a way that respects the application's actual access control logic.
 *
 * Route taxonomy follows the canonical single-spine navigation:
 *   Home, Library, Discover, Model, Deliver, Evidence, Govern
 */

import { Page } from '@playwright/test';

export type UserTier = 'standard' | 'advanced' | 'admin';

/**
 * Backend-canonical roles from identity provider
 */
export type BackendRole =
  | 'super_admin'
  | 'tenant_admin'
  | 'content_admin'
  | 'analyst'
  | 'read_only'
  | 'system'
  | 'admin'
  | 'advanced'
  | 'standard';

/**
 * Set the user tier in localStorage (simulating login/role assignment)
 *
 * This works because the app uses Zustand with persist middleware
 * to store tier state in localStorage under the key 'user-tier-storage'.
 *
 * @param page - Playwright page object
 * @param tier - Frontend presentation tier
 * @param backendRole - Optional backend-canonical role (defaults to tier value)
 */
export async function setUserTier(
  page: Page,
  tier: UserTier,
  backendRole?: BackendRole
): Promise<void> {
  await page.evaluate((params: { userTier: UserTier; role: string }) => {
    const storeKey = 'user-tier-storage';
    const storeState = {
      state: {
        currentTier: params.userTier,
        isAdvancedModeEnabled: params.userTier !== 'standard',
        userRole: params.role,
      },
      version: 0,
    };
    localStorage.setItem(storeKey, JSON.stringify(storeState));

    // Also set a flag for tests to detect
    localStorage.setItem('test-user-tier', params.userTier);
  }, { userTier: tier, role: backendRole || tier });

  // Reload to pick up the new tier state
  await page.reload();
}

/**
 * Enable advanced mode for a standard user (progressive disclosure toggle)
 */
export async function enableAdvancedMode(page: Page): Promise<void> {
  await page.evaluate(() => {
    const storeKey = 'user-tier-storage';
    const existing = localStorage.getItem(storeKey);
    const storeState = existing
      ? JSON.parse(existing)
      : { state: { currentTier: 'standard', isAdvancedModeEnabled: false, userRole: null }, version: 0 };

    storeState.state.isAdvancedModeEnabled = true;
    localStorage.setItem(storeKey, JSON.stringify(storeState));
  });

  await page.reload();
}

/**
 * Disable advanced mode
 */
export async function disableAdvancedMode(page: Page): Promise<void> {
  await page.evaluate(() => {
    const storeKey = 'user-tier-storage';
    const existing = localStorage.getItem(storeKey);
    if (!existing) return;

    const storeState = JSON.parse(existing);
    storeState.state.isAdvancedModeEnabled = false;
    localStorage.setItem(storeKey, JSON.stringify(storeState));
  });

  await page.reload();
}

/**
 * Clear user tier (logout/reset)
 */
export async function clearUserTier(page: Page): Promise<void> {
  await page.evaluate(() => {
    localStorage.removeItem('user-tier-storage');
    localStorage.removeItem('test-user-tier');
  });
  await page.reload();
}

/**
 * Get current tier from page
 */
export async function getCurrentTier(page: Page): Promise<UserTier | null> {
  return page.evaluate(() => {
    const stored = localStorage.getItem('user-tier-storage');
    if (!stored) return null;
    try {
      const parsed = JSON.parse(stored);
      return parsed.state?.currentTier || null;
    } catch {
      return null;
    }
  });
}

/**
 * Routes accessible by tier — canonical navigation taxonomy
 */
export const ROUTES_BY_TIER: Record<UserTier, { accessible: string[]; restricted: string[] }> = {
  standard: {
    accessible: [
      '/home',
      '/library/packs',
      '/discover/accounts',
      '/discover/jobs',
      '/deliver/cases',
      '/evidence/traces',
    ],
    restricted: [
      '/discover/extraction',
      '/discover/knowledge/graph',
      '/discover/knowledge/ontology',
      '/model/value-studio/explorer',
      '/model/value-studio/formulas',
      '/admin/content/formulas',
    ],
  },
  advanced: {
    accessible: [
      '/home',
      '/library/packs',
      '/discover/accounts',
      '/discover/jobs',
      '/discover/extraction',
      '/discover/knowledge/graph',
      '/discover/knowledge/ontology',
      '/model/value-studio/explorer',
      '/model/value-studio/formulas',
      '/deliver/cases',
      '/deliver/agents',
      '/evidence/traces',
    ],
    restricted: [
      '/admin/content/formulas',
      '/admin/content/benchmarks',
      '/admin/data/variables',
    ],
  },
  admin: {
    accessible: [
      '/home',
      '/library/packs',
      '/discover/accounts',
      '/discover/extraction',
      '/discover/knowledge/graph',
      '/model/value-studio/explorer',
      '/model/value-studio/formulas',
      '/deliver/cases',
      '/deliver/agents',
      '/evidence/traces',
      '/admin/content/formulas',
      '/admin/content/benchmarks',
      '/admin/data/variables',
    ],
    restricted: [],
  },
};

/**
 * Expected redirect destination when accessing restricted routes.
 * The RouteGuard in App.tsx redirects all restricted access to /home.
 */
export const TIER_REDIRECTS: Record<UserTier, string> = {
  standard: '/home',
  advanced: '/home',
  admin: '/home',
};
