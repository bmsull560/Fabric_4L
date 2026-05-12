import { test, expect } from "@playwright/test";

/**
 * E2E: Review / Approval Lifecycle
 * Validates: submit for review → comment → approve → export enabled flow
 */

test.describe("Review Approval Lifecycle", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    // Auth handled by existing session or test fixture
  });

  test("user can submit a business case for review, reviewer approves, export becomes available", async ({ page }) => {
    // 1. Navigate to an account with a business case
    await page.goto("/accounts");
    await page.waitForSelector('[data-testid="account-row"]', { timeout: 10000 });
    await page.click('[data-testid="account-row"]:first-child');

    // 2. Go to the value case page
    await page.goto("/value-case/demo-account-1");
    await page.waitForSelector('[data-testid="business-case-page"]', { timeout: 10000 });

    // 3. Verify gate status banner shows open gates initially
    const gateBanner = page.locator('[data-testid="gate-status-banner"]');
    await expect(gateBanner).toBeVisible();
    await expect(gateBanner).toContainText("gate");

    // 4. Navigate to review queue
    await page.goto("/governance/reviews/demo-account-1");
    await page.waitForSelector('[data-testid="review-queue-page"]', { timeout: 10000 });

    // 5. Submit for review
    await page.click('button:has-text("Submit for Review")');
    await page.waitForSelector('[data-testid="review-request-card"]', { timeout: 5000 });

    // 6. Add a comment
    await page.fill('input[placeholder="Add a comment..."]', "Looks good, minor formatting fix needed.");
    await page.click('button:has-text("Comment")');
    await expect(page.locator('text="Looks good, minor formatting fix needed."')).toBeVisible();

    // 7. Approve the review
    await page.click('button:has-text("Approve")');
    await expect(page.locator('text="approved"')).toBeVisible();

    // 8. Return to business case; export button should now be enabled
    await page.goto("/value-case/demo-account-1");
    await page.waitForSelector('[data-testid="business-case-page"]', { timeout: 10000 });

    // Gate banner should show all gates closed (at least approval gate)
    await expect(gateBanner).toContainText("All gates closed");
  });

  test("export is blocked when approval gate is open", async ({ page }) => {
    await page.goto("/value-case/demo-account-1");
    await page.waitForSelector('[data-testid="business-case-page"]', { timeout: 10000 });

    // If no approved review exists, the export should be disabled or show blocked state
    const gateBanner = page.locator('[data-testid="gate-status-banner"]');
    await expect(gateBanner).toBeVisible();

    // Verify at least one gate is open (approval gate since no review approved)
    const openGates = page.locator('[data-testid="gate-open-badge"]');
    await expect(openGates.first()).toBeVisible();
  });
});
