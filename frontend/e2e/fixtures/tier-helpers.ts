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
 * Set the user tier in localStorage (simulating login/role assignment)
 *
 * This works because the app uses Zustand with persist middleware
 * to store tier state in localStorage under the key 'user-tier-storage'.
 */
export async function setUserTier(page: Page, tier: UserTier): Promise<void> {
  await page.evaluate((userTier) => {
    const storeKey = 'user-tier-storage';
    const storeState = {
      state: {
        currentTier: userTier,
        isAdvancedModeEnabled: userTier !== 'standard',
        userRole: userTier,
      },
      version: 0,
    };
    localStorage.setItem(storeKey, JSON.stringify(storeState));

    // Also set a flag for tests to detect
    localStorage.setItem('test-user-tier', userTier);
  }, tier);

  // Reload to pick up the new tier state
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
