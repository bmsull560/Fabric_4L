import { test, expect } from '@playwright/test';
import { CommandCenterPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Command Center E2E Tests
 *
 * Route: /home
 * Tier: standard (all tiers)
 *
 * Covers the primary ingestion workflow:
 * - Domain submission
 * - KPI display
 * - Recent jobs listing
 * - Advanced configuration
 */

test.describe('Command Center', () => {
  let commandCenter: CommandCenterPage;

  test.beforeEach(async ({ page }) => {
    // Set standard tier for basic access
    await setUserTier(page, 'standard');
    commandCenter = new CommandCenterPage(page);
    await commandCenter.goto();
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Page Load', () => {
    test('should display page header and main input', async () => {
      await commandCenter.assertInitialState();
    });

    test('should show KPI cards with loading state', async () => {
      // KPIs should be visible even while loading
      await expect(commandCenter.totalDomainsCard).toBeVisible();
      await expect(commandCenter.pagesSynthesizedCard).toBeVisible();
      await expect(commandCenter.sourcesAnalyzedCard).toBeVisible();
    });

    test('should display recent jobs section', async () => {
      await commandCenter.waitForJobs();
      // Either table with jobs or empty state should be visible
      const hasTable = await commandCenter.jobsTable.isVisible().catch(() => false);
      const hasEmpty = await commandCenter.noJobsMessage.isVisible().catch(() => false);
      expect(hasTable || hasEmpty).toBeTruthy();
    });
  });

  test.describe('Domain Submission', () => {
    test('should enable synthesize button when domain is entered', async () => {
      await commandCenter.assertSynthesizeEnabledWithInput();
    });

    test('should disable synthesize button when input is empty', async () => {
      await expect(commandCenter.synthesizeButton).toBeDisabled();
    });

    test('should submit domain on button click', async () => {
      // Fill in domain and submit
      await commandCenter.submitDomain('https://example.com');

      // Button should show loading state or become disabled during submission
      await expect(commandCenter.synthesizeButton).toBeDisabled();

      // Input should be cleared after successful submission
      await expect(commandCenter.domainInput).toHaveValue('');
    });

    test('should handle invalid domain gracefully', async () => {
      // Submit invalid input
      await commandCenter.submitDomain('not-a-valid-url');

      // Should show validation error or remain in form without crash
      await expect(commandCenter.header).toBeVisible();
    });
  });

  test.describe('Advanced Configuration', () => {
    test('should toggle advanced options panel', async () => {
      // Initially hidden
      await expect(commandCenter.profileSelect).toBeHidden();

      // Toggle open
      await commandCenter.toggleAdvancedConfig();
      await expect(commandCenter.profileSelect).toBeVisible();
      await expect(commandCenter.ontologySelect).toBeVisible();
      await expect(commandCenter.depthSelect).toBeVisible();

      // Toggle closed
      await commandCenter.toggleAdvancedConfig();
      await expect(commandCenter.profileSelect).toBeHidden();
    });

    test('should persist advanced settings during submission', async () => {
      // Open advanced config
      await commandCenter.toggleAdvancedConfig();

      // Change settings
      await commandCenter.setProfile('Deep Crawl');
      await commandCenter.setOntology('Financial Services');

      // Submit should work with custom settings
      await commandCenter.enterDomain('https://testcompany.io');
      await commandCenter.clickSynthesize();

      // Form should submit without errors
      await expect(commandCenter.synthesizeButton).toBeDisabled();
    });
  });

  test.describe('Jobs Table', () => {
    test('should display job status badges correctly', async () => {
      await commandCenter.waitForJobs();

      // Look for status indicators in the table
      const table = commandCenter.jobsTable;
      const statusBadges = table.locator('[class*="badge"], [class*="status"]').first();

      // If there are jobs, status should be visible
      const hasJobs = await table.locator('tbody tr').count() > 0;
      if (hasJobs) {
        await expect(statusBadges).toBeVisible();
      }
    });

    test('should show loading state while fetching jobs', async () => {
      // Navigate fresh and check loading state
      await commandCenter.goto();

      // Loading indicator should appear briefly
      const loading = commandCenter.jobsLoadingState;
      if (await loading.isVisible().catch(() => false)) {
        await expect(loading).toBeHidden();
      }
    });
  });

  test.describe('Access Control', () => {
    test('standard tier user can access command center', async ({ page }) => {
      // Already set to standard in beforeEach
      await expect(page).toHaveURL(/\/home/);
      await expect(commandCenter.header).toBeVisible();
    });

    test('advanced tier user can access command center', async ({ page }) => {
      await setUserTier(page, 'advanced');
      await page.goto('/home');
      await expect(commandCenter.header).toBeVisible();
    });
  });
});
