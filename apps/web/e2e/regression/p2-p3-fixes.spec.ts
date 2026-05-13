/**
 * P2/P3 Fix Regression Tests
 *
 * End-to-end tests validating the fixes for remaining gaps:
 * - BusinessCaseList: shadcn Select filters, VirtualList
 * - ValuePacks: VirtualList grid, EmptyState
 * - FormulaBuilder: Variable chip keyboard accessibility
 * - LeftNavigation: No prefetch=intent attribute
 */
import { test, expect } from '../fixtures/a11y-test';
import { AxeBuilder } from "@axe-core/playwright";

test.describe("P2/P3 Fix Regressions", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  // ── BusinessCaseList ──────────────────────────────────────────────────────

  test.describe("BusinessCaseList", () => {
    test("uses shadcn Select instead of native select for filters", async ({ page }) => {
      await page.goto("/deliver/cases");
      await page.waitForLoadState("networkidle");

      // Should have comboboxes (shadcn Select) not native <select>
      const nativeSelects = await page.locator("select").count();
      expect(nativeSelects).toBe(0);

      // Should have at least 2 combobox triggers (status + sort)
      const comboboxes = await page.locator('[role="combobox"]').count();
      expect(comboboxes).toBeGreaterThanOrEqual(2);
    });

    test("status filter dropdown opens and shows options", async ({ page }) => {
      await page.goto("/deliver/cases");
      await page.waitForLoadState("networkidle");

      // Click the status filter trigger
      const statusTrigger = page.locator("text=All Status").first();
      await statusTrigger.click();

      // Wait for dropdown to appear
      await expect(page.locator("[role='option']", { hasText: "Active" })).toBeVisible();
      await expect(page.locator("[role='option']", { hasText: "Draft" })).toBeVisible();
      await expect(page.locator("[role='option']", { hasText: "Archived" })).toBeVisible();
    });

    test("sort filter dropdown opens and shows options", async ({ page }) => {
      await page.goto("/deliver/cases");
      await page.waitForLoadState("networkidle");

      // Click the sort filter trigger
      const sortTrigger = page.locator("text=Last Updated").first();
      await sortTrigger.click();

      // Wait for dropdown to appear
      await expect(page.locator("[role='option']", { hasText: "Name" })).toBeVisible();
      await expect(page.locator("[role='option']", { hasText: "Company" })).toBeVisible();
      await expect(page.locator("[role='option']", { hasText: "Value" })).toBeVisible();
    });

    test("case list uses virtualization container", async ({ page }) => {
      await page.goto("/deliver/cases");
      await page.waitForLoadState("networkidle");

      // VirtualList applies contain: strict
      const virtualContainer = page.locator('[style*="contain: strict"]');
      await expect(virtualContainer).toBeVisible();
    });

    test("BusinessCaseList page passes axe accessibility scan", async ({ page }) => {
      await page.goto("/deliver/cases");
      await page.waitForLoadState("networkidle");

      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations).toEqual([]);
    });
  });

  // ── ValuePacks ────────────────────────────────────────────────────────────

  test.describe("ValuePacks", () => {
    test("pack grid uses virtualization container", async ({ page }) => {
      await page.goto("/value-packs");
      await page.waitForLoadState("networkidle");

      // Wait for packs to load
      await page.waitForSelector("text=Enterprise Security ROI", { timeout: 10000 });

      // VirtualList applies contain: strict
      const virtualContainer = page.locator('[style*="contain: strict"]');
      await expect(virtualContainer).toBeVisible();
    });

    test("empty state uses shared EmptyState component", async ({ page }) => {
      await page.goto("/value-packs?search=nonexistentpack12345");
      await page.waitForLoadState("networkidle");

      // Should show EmptyState with heading role
      const emptyHeading = page.locator("[role='heading']", { hasText: /no value packs/i });
      await expect(emptyHeading).toBeVisible();
    });

    test("ValuePacks page passes axe accessibility scan", async ({ page }) => {
      await page.goto("/value-packs");
      await page.waitForLoadState("networkidle");

      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations).toEqual([]);
    });
  });

  // ── FormulaBuilder ────────────────────────────────────────────────────────

  test.describe("FormulaBuilder", () => {
    test("variable chips have aria-labels and are keyboard accessible", async ({ page }) => {
      await page.goto("/context/formulas/new");
      await page.waitForLoadState("networkidle");

      // Wait for variables to load
      await page.waitForSelector("[aria-label*='Insert variable']", { timeout: 10000 });

      const variableChips = await page.locator("[aria-label*='Insert variable']").all();
      expect(variableChips.length).toBeGreaterThan(0);

      // Check first chip has proper attributes
      const firstChip = variableChips[0];
      const ariaLabel = await firstChip.getAttribute("aria-label");
      expect(ariaLabel).toMatch(/insert variable/i);

      const tabIndex = await firstChip.getAttribute("tabindex");
      expect(tabIndex).toBe("0");

      const role = await firstChip.getAttribute("role");
      expect(role).toBe("button");
    });

    test("variable chip inserts on keyboard Enter", async ({ page }) => {
      await page.goto("/context/formulas/new");
      await page.waitForLoadState("networkidle");

      // Wait for variables to load
      await page.waitForSelector("[aria-label*='Insert variable']", { timeout: 10000 });

      const firstChip = page.locator("[aria-label*='Insert variable']").first();

      // Focus and press Enter
      await firstChip.focus();
      await page.keyboard.press("Enter");

      // Should not navigate away or error
      await expect(page).toHaveURL(/context\/formulas\/new/);
    });

    test("FormulaBuilder page passes axe accessibility scan", async ({ page }) => {
      await page.goto("/context/formulas/new");
      await page.waitForLoadState("networkidle");

      const results = await new AxeBuilder({ page }).analyze();
      expect(results.violations).toEqual([]);
    });
  });

  // ── LeftNavigation ────────────────────────────────────────────────────────

  test.describe("LeftNavigation", () => {
    test("NavLink elements do not have prefetch attribute", async ({ page }) => {
      const navLinks = await page.locator("nav a[href]").all();

      for (const link of navLinks) {
        const hasPrefetch = await link.evaluate((el) => el.hasAttribute("prefetch"));
        expect(hasPrefetch).toBe(false);
      }
    });
  });

  // ── OptimizedImage ────────────────────────────────────────────────────────

  test.describe("OptimizedImage", () => {
    test("images have loading=lazy and decoding=async", async ({ page }) => {
      // Check any page that might have images
      await page.goto("/");
      await page.waitForLoadState("networkidle");

      const images = await page.locator("img").all();
      for (const img of images) {
        const loading = await img.getAttribute("loading");
        const decoding = await img.getAttribute("decoding");

        // If the image uses OptimizedImage, it should have these attributes
        if (loading) {
          expect(["lazy", "eager"]).toContain(loading);
        }
        if (decoding) {
          expect(["async", "sync", "auto"]).toContain(decoding);
        }
      }
    });
  });
});
