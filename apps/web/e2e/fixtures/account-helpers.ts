/**
 * Account Context Helpers for Playwright Contract Tests
 *
 * Provides utilities to set/clear the selected account context
 * in the browser. Account-scoped routes (intelligence/:accountId,
 * studio/:accountId) require an account to be selected before
 * the workspace tabs become accessible.
 *
 * Contract: The accountContextStore is a zustand store persisted
 *           to localStorage under the key 'fabric-account-context'.
 *
 * IMPORTANT: All localStorage operations require the page to be on a
 * same-origin URL first. These helpers ensure that.
 */
import { Page } from '@playwright/test';

export interface TestAccount {
  id: string;
  name: string;
  industry?: string;
  tier?: string;
}

/**
 * Canonical test accounts for deterministic testing.
 */
export const TEST_ACCOUNTS = {
  meridian: {
    id: 'acct-meridian-001',
    name: 'Meridian Automotive',
    industry: 'Manufacturing',
    tier: 'enterprise',
  } satisfies TestAccount,

  acme: {
    id: 'acct-acme-002',
    name: 'Acme Corp',
    industry: 'Technology',
    tier: 'mid-market',
  } satisfies TestAccount,

  globalFinance: {
    id: 'acct-gf-003',
    name: 'Global Finance Inc',
    industry: 'Financial Services',
    tier: 'enterprise',
  } satisfies TestAccount,
};

/**
 * Ensure the page is on a same-origin URL so localStorage is accessible.
 */
async function ensureSameOrigin(page: Page): Promise<void> {
  const url = page.url();
  if (url === 'about:blank' || url === '' || url === 'chrome://newtab/') {
    await page.goto('/login', { waitUntil: 'commit' });
  }
}

/**
 * Set the selected account in the zustand store via localStorage.
 * Must be called before navigating to account-scoped routes.
 */
export async function setSelectedAccount(page: Page, account: TestAccount): Promise<void> {
  await ensureSameOrigin(page);

  await page.evaluate((acct) => {
    // Must match zustand persist shape: only selectedAccountId is partialised
    const storeState = {
      state: {
        selectedAccountId: acct.id,
      },
      version: 0,
    };
    localStorage.setItem('fabric-account-context', JSON.stringify(storeState));
  }, account);
}

/**
 * Clear the selected account from the zustand store.
 */
export async function clearSelectedAccount(page: Page): Promise<void> {
  try {
    await page.evaluate(() => {
      localStorage.removeItem('fabric-account-context');
    });
  } catch {
    // Page may already be closed — safe to ignore
  }
}

/**
 * Get the currently selected account ID from the store.
 */
export async function getSelectedAccountId(page: Page): Promise<string | null> {
  return page.evaluate(() => {
    const raw = localStorage.getItem('fabric-account-context');
    if (!raw) return null;
    try {
      const parsed = JSON.parse(raw);
      return parsed?.state?.selectedAccountId ?? null;
    } catch {
      return null;
    }
  });
}
