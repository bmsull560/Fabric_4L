import { test } from '@playwright/test';
import { seedAuthState } from './fixtures/auth-helpers';
import { setUserTier } from './fixtures/tier-helpers';

type DebugAuthWindowHooks = Window & {
  __authClientClearSession?: () => void;
};

type SchemaProbeResult = {
  removedKeys: string[];
};

type PostNavigationState = {
  url: string;
  token: string | null;
  userInfo: string | null;
};

test('debug auth flow', async ({ page }) => {
  await page.goto('/login', { waitUntil: 'networkidle' });
  await page.evaluate(() => {
    localStorage.clear();
    sessionStorage.clear();
  });

  await seedAuthState(page);
  await setUserTier(page, 'admin', 'super_admin');

  // Inject a script to test schema validation
  const schemaResult = await page.evaluate<SchemaProbeResult>(() => {
    // The Zod schema isn't globally accessible, but we can try to import it
    // Actually, let's just check what the authClient does
    // We'll monkey-patch clearSession to see if it's being called
    const browserWindow = window as DebugAuthWindowHooks;
    void browserWindow.__authClientClearSession;
    
    // We can't easily access the authClient instance, but we can listen for localStorage changes
    let removedKeys: string[] = [];
    const origRemoveItem = localStorage.removeItem.bind(localStorage);
    localStorage.removeItem = (key: string) => {
      removedKeys.push(key);
      return origRemoveItem(key);
    };

    return new Promise<SchemaProbeResult>((resolve) => {
      setTimeout(() => {
        resolve({ removedKeys });
      }, 2000);
    });
  });

  console.log('Schema result before nav:', JSON.stringify(schemaResult, null, 2));

  await page.goto('/home', { waitUntil: 'networkidle' });
  await page.waitForTimeout(3000);

  const afterNav = await page.evaluate<PostNavigationState>(() => {
    // We need to re-inject since navigation resets the page
    // Actually localStorage persists, so let's just check what's there
    return {
      url: window.location.href,
      token: localStorage.getItem('accessToken'),
      userInfo: localStorage.getItem('userInfo'),
    };
  });

  console.log('After nav:', JSON.stringify(afterNav, null, 2));

  await page.screenshot({ path: 'e2e-results/debug-auth.png', fullPage: true });
});
