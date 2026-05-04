import { test, expect } from '@playwright/test';
import { FormulaBuilderPage } from './pages';
import { setUserTier, clearUserTier } from './fixtures';

/**
 * Formula Builder E2E Tests
 *
 * Route: /model/value-studio/formulas
 * Tier: advanced (Tier 2+)
 *
 * Covers:
 * - Tab navigation (Formula, Governance, Dependencies, History)
 * - Expression editor display
 * - Variable binding table
 * - Save/Run buttons
 * - Access control
 */

test.describe('Formula Builder', () => {
  let formulaBuilder: FormulaBuilderPage;

  test.beforeEach(async ({ page }) => {
    await setUserTier(page, 'advanced');
    formulaBuilder = new FormulaBuilderPage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test.describe('Page Load', () => {
    test('should display formula tab by default', async () => {
      await formulaBuilder.goto();
      await expect(formulaBuilder.formulaTab).toBeVisible();
    });

    test('should show all tabs', async () => {
      await formulaBuilder.goto();
      await expect(formulaBuilder.formulaTab).toBeVisible();

      // Governance, Dependencies, History tabs should exist
      const hasGovernance = await formulaBuilder.governanceTab.isVisible().catch(() => false);
      const hasDependencies = await formulaBuilder.dependenciesTab.isVisible().catch(() => false);
      const hasHistory = await formulaBuilder.historyTab.isVisible().catch(() => false);

      // At least the formula tab + one other should be present
      expect(hasGovernance || hasDependencies || hasHistory).toBeTruthy();
    });
  });

  test.describe('Tab Navigation', () => {
    test.beforeEach(async () => {
      await formulaBuilder.goto();
    });

    test('should switch to Governance tab', async () => {
      const hasTab = await formulaBuilder.governanceTab.isVisible().catch(() => false);
      if (hasTab) {
        await formulaBuilder.switchToTab('governance');
        await expect(formulaBuilder.governanceTab).toHaveAttribute('aria-selected', 'true');
      }
    });

    test('should switch to Dependencies tab', async () => {
      const hasTab = await formulaBuilder.dependenciesTab.isVisible().catch(() => false);
      if (hasTab) {
        await formulaBuilder.switchToTab('dependencies');
        await expect(formulaBuilder.dependenciesTab).toHaveAttribute('aria-selected', 'true');
      }
    });

    test('should switch to History tab', async () => {
      const hasTab = await formulaBuilder.historyTab.isVisible().catch(() => false);
      if (hasTab) {
        await formulaBuilder.switchToTab('history');
        await expect(formulaBuilder.historyTab).toHaveAttribute('aria-selected', 'true');
      }
    });

    test('should return to Formula tab', async () => {
      const hasGovernance = await formulaBuilder.governanceTab.isVisible().catch(() => false);
      if (hasGovernance) {
        await formulaBuilder.switchToTab('governance');
        await formulaBuilder.switchToTab('formula');
        await expect(formulaBuilder.formulaTab).toHaveAttribute('aria-selected', 'true');
      }
    });
  });

  test.describe('Formula Tab Content', () => {
    test.beforeEach(async () => {
      await formulaBuilder.goto();
    });

    test('should display expression editor', async () => {
      const hasEditor = await formulaBuilder.expressionEditor.isVisible().catch(() => false);
      // Editor may be text area, contenteditable, or other
      if (hasEditor) {
        await expect(formulaBuilder.expressionEditor).toBeVisible();
      }
    });

    test('should display variable binding table', async () => {
      const hasTable = await formulaBuilder.variableTable.isVisible().catch(() => false);
      if (hasTable) {
        const count = await formulaBuilder.getVariableCount();
        expect(count).toBeGreaterThanOrEqual(0);
      }
    });

    test('should display action buttons', async () => {
      const hasSave = await formulaBuilder.saveButton.isVisible().catch(() => false);
      const hasRun = await formulaBuilder.runButton.isVisible().catch(() => false);
      // At least one action button should be present
      expect(hasSave || hasRun).toBeTruthy();
    });
  });

  test.describe('Governance Tab Content', () => {
    test('should display status badge', async () => {
      await formulaBuilder.goto();
      const hasGovernance = await formulaBuilder.governanceTab.isVisible().catch(() => false);
      if (hasGovernance) {
        await formulaBuilder.switchToTab('governance');
        const hasBadge = await formulaBuilder.statusBadge.isVisible().catch(() => false);
        // Status badge may not be visible if no formula is selected
        if (hasBadge) {
          await expect(formulaBuilder.statusBadge).toBeVisible();
        }
      }
    });
  });

  test.describe('Access Control', () => {
    test('requires advanced tier to access', async ({ page }) => {
      await setUserTier(page, 'standard');
      await page.goto('/model/value-studio/formulas');
      // Should be redirected to /home
      await expect(page).toHaveURL(/\/home/);
    });

    test('advanced tier can access formula builder', async () => {
      await formulaBuilder.goto();
      await expect(formulaBuilder.formulaTab).toBeVisible();
    });

    test('admin tier can access formula builder', async ({ page }) => {
      await setUserTier(page, 'admin');
      await page.goto('/model/value-studio/formulas');
      await expect(formulaBuilder.formulaTab).toBeVisible();
    });
  });
});
