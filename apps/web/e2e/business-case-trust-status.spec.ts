/**
 * CONTRACT TEST: Business Case Trust Status Row
 *
 * Covers the trust status row added in Sprint 4 (W3).
 * All tests use mocked API routes — no backend required.
 *
 * Covers:
 *   TS-01  Degraded badge and "Internal draft only" badge render when
 *          customer_facing_allowed is false
 *   TS-02  Pending Review badge and "Internal draft only" badge render
 *          when status is pending
 *   TS-03  Validated badge renders when status is approved without document_url
 *   TS-04  Export Ready badge renders when status is completed with document_url
 *   TS-05  Export Blocked badge renders when status is failed
 *   TS-06  Export PDF button is disabled when case is degraded
 *   TS-07  Export PDF button is disabled when case is pending review
 *   TS-08  Export PDF button is enabled when case is export_ready
 *
 * All API routes are mocked — no backend required.
 * Uses the contract-test fixture which auto-installs the API harness.
 */
import { test, expect, type Page } from './fixtures/contract-test';
import { seedAuthState, clearAuthState } from './fixtures/auth-helpers';
import { setUserTier, clearUserTier } from './fixtures/tier-helpers';
import { BusinessCasePage } from './pages';

// ── Mock helpers ──────────────────────────────────────────────────────────────

const BASE_CASE = {
  case_id: 'trust-test-001',
  title: 'Trust Status Test Case',
  summary: 'Test summary for trust status row.',
  total_value: 500000,
  implementation_cost: 100000,
  roi_ratio: 5.0,
  payback_months: 8,
  confidence_score: 0.88,
  recommendations: ['Recommendation A'],
  status: 'completed',
  created_at: '2026-01-01T00:00:00Z',
  page_count: 12,
  file_size_bytes: 51200,
};

async function mockBusinessCase(
  page: Page,
  overrides: Record<string, unknown> = {},
): Promise<void> {
  const body = { ...BASE_CASE, ...overrides };
  await page.route('**/api/v1/agents/cases/trust-test-001', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify(body) });
    } else {
      await route.continue();
    }
  });
  // Also handle the list endpoint used by some navigation hooks
  await page.route('**/api/v1/agents/cases?**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        contentType: 'application/json',
        body: JSON.stringify({ items: [body], total: 1, has_more: false }),
      });
    } else {
      await route.continue();
    }
  });
}

// ── Suite ─────────────────────────────────────────────────────────────────────

test.describe('Contract: Business Case Trust Status Row', () => {
  let businessCase: BusinessCasePage;

  test.beforeEach(async ({ page }) => {
    await seedAuthState(page);
    await setUserTier(page, 'standard');
    businessCase = new BusinessCasePage(page);
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
    await clearAuthState(page);
  });

  // ── TS-01: Degraded ────────────────────────────────────────────────────────

  test('TS-01: Degraded and Internal draft only badges render when customer_facing_allowed is false', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'completed',
      case_metadata: { customer_facing_allowed: false },
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.degradedBadge).toBeVisible({ timeout: 5000 });
    await expect(businessCase.internalDraftBadge).toBeVisible({ timeout: 5000 });
  });

  // ── TS-02: Pending Review ──────────────────────────────────────────────────

  test('TS-02: Pending Review and Internal draft only badges render for pending status', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'pending',
      case_metadata: {},
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.pendingReviewBadge).toBeVisible({ timeout: 5000 });
    await expect(businessCase.internalDraftBadge).toBeVisible({ timeout: 5000 });
  });

  // ── TS-03: Validated ───────────────────────────────────────────────────────

  test('TS-03: Validated badge renders when approved without document_url', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'approved',
      document_url: null,
      case_metadata: {},
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.validatedBadge).toBeVisible({ timeout: 5000 });
  });

  // ── TS-04: Export Ready ────────────────────────────────────────────────────

  test('TS-04: Export Ready badge renders when completed with document_url', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'completed',
      document_url: 'https://example.com/doc.pdf',
      case_metadata: {},
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.exportReadyBadge).toBeVisible({ timeout: 5000 });
  });

  // ── TS-05: Export Blocked ──────────────────────────────────────────────────

  test('TS-05: Export Blocked badge renders when status is failed', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'failed',
      case_metadata: {},
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.exportBlockedBadge).toBeVisible({ timeout: 5000 });
  });

  // ── TS-06: Export disabled when degraded ──────────────────────────────────

  test('TS-06: Export PDF button is disabled when case is degraded', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'completed',
      document_url: 'https://example.com/doc.pdf',
      case_metadata: { customer_facing_allowed: false },
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.exportPdfButton).toBeDisabled({ timeout: 5000 });
  });

  // ── TS-07: Export disabled when pending review ─────────────────────────────

  test('TS-07: Export PDF button is disabled when case is pending review', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'pending',
      document_url: 'https://example.com/doc.pdf',
      case_metadata: {},
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.exportPdfButton).toBeDisabled({ timeout: 5000 });
  });

  // ── TS-08: Export enabled when export_ready ────────────────────────────────

  test('TS-08: Export PDF button is enabled when case is export_ready', async ({ page }) => {
    await mockBusinessCase(page, {
      status: 'completed',
      document_url: 'https://example.com/doc.pdf',
      case_metadata: {},
    });
    await page.goto('/deliverables/cases/trust-test-001');
    await page.waitForLoadState('domcontentloaded');

    await expect(businessCase.exportPdfButton).not.toBeDisabled({ timeout: 5000 });
  });
});
