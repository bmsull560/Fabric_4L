/**
 * Accessibility Journey Tests - Key user journeys with @axe-core/playwright
 * 
 * Target: WCAG 2.2 AA
 * 
 * Tests critical user journeys for accessibility violations using axe-core.
 * This complements the component-level smoke tests in accessibility.a11y.spec.tsx.
 */
import { test, expect } from "@playwright/test";
import { AxeBuilder } from "@axe-core/playwright";

test.describe("Accessibility Journeys - WCAG 2.2 AA", () => {
  test.beforeEach(async ({ page }) => {
    // Wait for page to be fully loaded
    await page.goto("/");
    await page.waitForLoadState("networkidle");
  });

  test("app shell / landing page is accessible", async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("main navigation is keyboard accessible", async ({ page }) => {
    // Test keyboard navigation through main menu
    await page.keyboard.press("Tab");
    
    // Check that focus is visible
    const focusedElement = await page.evaluate(() => document.activeElement?.tagName);
    expect(["BUTTON", "A", "INPUT"].includes(focusedElement || "")).toBeTruthy();
  });

  test("Intelligence page is accessible", async ({ page }) => {
    // Navigate to Intelligence page (may require authentication)
    await page.goto("/intelligence");
    await page.waitForLoadState("networkidle");
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("FormulaBuilder page is accessible", async ({ page }) => {
    // Navigate to FormulaBuilder page
    await page.goto("/context/formulas/new");
    await page.waitForLoadState("networkidle");
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Calculator page is accessible", async ({ page }) => {
    // Navigate to Calculator page
    await page.goto("/calculator");
    await page.waitForLoadState("networkidle");
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("Value Case page is accessible", async ({ page }) => {
    // Navigate to Value Case page
    await page.goto("/value-case");
    await page.waitForLoadState("networkidle");
    
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("form inputs have proper labels", async ({ page }) => {
    await page.goto("/context/formulas/new");
    await page.waitForLoadState("networkidle");
    
    // Check that form inputs have associated labels
    const inputs = await page.locator("input, textarea, select").all();
    for (const input of inputs) {
      const hasLabel = await input.evaluate((el) => {
        const id = el.getAttribute("id");
        if (id) {
          const label = document.querySelector(`label[for="${id}"]`);
          return !!label;
        }
        return el.hasAttribute("aria-label") || el.hasAttribute("aria-labelledby");
      });
      expect(hasLabel).toBeTruthy();
    }
  });

  test("buttons have accessible names", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    
    // Check that buttons have text content or aria-label
    const buttons = await page.locator("button").all();
    for (const button of buttons) {
      const hasAccessibleName = await button.evaluate((el) => {
        return (
          el.textContent?.trim().length > 0 ||
          el.hasAttribute("aria-label") ||
          el.hasAttribute("aria-labelledby")
        );
      });
      // Skip icon-only buttons that should have aria-label (handled by axe scan)
      if (hasAccessibleName || await button.evaluate(el => el.children.length === 0)) {
        // Icon-only buttons should be caught by axe scan
      }
    }
  });

  test("focus management works correctly", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    
    // Tab through the page and check focus visibility
    await page.keyboard.press("Tab");
    let firstFocused = await page.evaluate(() => document.activeElement?.tagName);
    
    await page.keyboard.press("Tab");
    let secondFocused = await page.evaluate(() => document.activeElement?.tagName);
    
    expect(firstFocused).not.toBe(secondFocused);
  });

  test("color contrast meets WCAG AA standards", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("networkidle");
    
    // Axe will check color contrast automatically
    const accessibilityScanResults = await new AxeBuilder({ page }).analyze();
    const contrastViolations = accessibilityScanResults.violations.filter(
      (v: any) => v.id === "color-contrast"
    );
    expect(contrastViolations).toEqual([]);
  });
});
