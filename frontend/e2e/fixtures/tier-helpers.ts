/**
 * Tier/permission helpers for access control testing
 *
 * Provides utilities to set user tier and verify route access
 * in a way that respects the application's actual access control logic.
 */

import { Page } from '@playwright/test';

export type UserTier = 'standard' | 'advanced' | 'admin';

/**
 * Set the user tier in localStorage (simulating login/role assignment)
 *
 * This works because the app uses Zustand with persist middleware
 * to store tier state in localStorage.
 */
export async function setUserTier(page: Page, tier: UserTier): Promise<void> {
  await page.evaluate((userTier) => {
    // Set the Zustand store state directly via localStorage
    const storeKey = 'user-tier-storage';
    const storeState = {
      state: {
        currentTier: userTier,
        isAdvancedModeEnabled: userTier !== 'standard',
        userRole: userTier,
        permissions: getPermissionsForTier(userTier),
      },
      version: 0,
    };
    localStorage.setItem(storeKey, JSON.stringify(storeState));

    // Also set a flag for tests to detect
    localStorage.setItem('test-user-tier', userTier);

    function getPermissionsForTier(t: UserTier) {
      const base = {
        canAccessAdvanced: t !== 'standard',
        canAccessAdmin: t === 'admin',
        canEditFormulas: t !== 'standard',
        canManageBenchmarks: t === 'admin',
        canManageVariables: t === 'admin',
        canManagePacks: t === 'admin',
        canManageUsers: t === 'admin',
      };
      return base;
    }
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
 * Routes accessible by tier
 */
export const ROUTES_BY_TIER: Record<UserTier, { accessible: string[]; restricted: string[] }> = {
  standard: {
    accessible: ['/command-center', '/value-packs'],
    restricted: ['/extraction-engine', '/graph/explorer', '/ontology/entities', '/admin/formulas'],
  },
  advanced: {
    accessible: ['/command-center', '/value-packs', '/extraction-engine', '/graph/explorer', '/ontology/entities'],
    restricted: ['/admin/formulas', '/admin/benchmarks', '/admin/variables'],
  },
  admin: {
    accessible: [
      '/command-center', '/value-packs', '/extraction-engine', '/graph/explorer',
      '/ontology/entities', '/admin/formulas', '/admin/benchmarks', '/admin/variables',
    ],
    restricted: [],
  },
};

/**
 * Expected redirect destinations when accessing restricted routes
 */
export const TIER_REDIRECTS: Record<UserTier, string> = {
  standard: '/command-center',
  advanced: '/extraction-engine',
  admin: '/command-center', // Admin can access everything
};
