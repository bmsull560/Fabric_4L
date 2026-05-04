import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for HealthMonitor
 *
 * Route: /admin/system/health
 * Tier: admin
 *
 * Covers system health dashboard with service grid and alerts
 */
export class HealthMonitorPage {
  readonly page: Page;

  // Header elements
  readonly header: Locator;
  readonly subtitle: Locator;
  readonly refreshButton: Locator;

  // Status indicators
  readonly overallStatusBadge: Locator;
  readonly healthyCount: Locator;
  readonly degradedCount: Locator;
  readonly unhealthyCount: Locator;

  // Service grid
  readonly serviceCards: Locator;
  readonly serviceNames: Locator;
  readonly serviceStatuses: Locator;

  // Alerts section
  readonly alertsSection: Locator;
  readonly alertItems: Locator;
  readonly dismissAlertButtons: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /health monitor|system health/i });
    this.subtitle = page.locator('text=/service status|real-time/i');
    this.refreshButton = page.getByRole('button', { name: /refresh/i });

    // Status indicators
    this.overallStatusBadge = page.locator('[class*="badge"]').filter({
      hasText: /healthy|degraded|unhealthy/i,
    }).first();
    this.healthyCount = page.locator('text=/\\d+ healthy/i');
    this.degradedCount = page.locator('text=/\\d+ degraded/i');
    this.unhealthyCount = page.locator('text=/\\d+ unhealthy/i');

    // Service grid
    this.serviceCards = page.locator('[class*="service"], [class*="card"]').filter({
      has: page.locator('text=/l1-ingestion|l2-extraction|l3-knowledge|l4-agents/i'),
    });
    this.serviceNames = page.locator('text=/l1-ingestion|l2-extraction|l3-knowledge|l4-agents/i');
    this.serviceStatuses = page.locator('[class*="status"], [class*="badge"]').filter({
      hasText: /healthy|degraded|unhealthy|unknown/i,
    });

    // Alerts section
    this.alertsSection = page.locator('text=/active alerts|health alerts/i').locator('..');
    this.alertItems = page.locator('[class*="alert"], [class*="item"]').filter({
      has: page.locator('text=/warning|critical|memory|database/i'),
    });
    this.dismissAlertButtons = page.getByRole('button', { name: /dismiss/i });

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
    this.errorMessage = page.getByRole('alert').or(page.getByText(/failed to load/i));
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to Health Monitor
   */
  async goto(): Promise<void> {
    await this.page.goto('/admin/system/health');
    await this.waitForPageLoad();
  }

  /**
   * Wait for page to be fully loaded
   */
  async waitForPageLoad(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Wait for data to load
   */
  async waitForDataLoad(): Promise<void> {
    const hasSkeleton = await this.loadingSkeleton.isVisible().catch(() => false);
    if (hasSkeleton) {
      await expect(this.loadingSkeleton).toBeHidden({ timeout: 10000 });
    }
  }

  // ── Actions ───────────────────────────────────────────────────────

  /**
   * Click refresh button
   */
  async clickRefresh(): Promise<void> {
    await this.refreshButton.click();
  }

  /**
   * Dismiss alert at index
   */
  async dismissAlert(index: number): Promise<void> {
    const btn = this.dismissAlertButtons.nth(index);
    await btn.click();
  }

  // ── Getters ────────────────────────────────────────────────────────

  /**
   * Get service count
   */
  async getServiceCount(): Promise<number> {
    return this.serviceCards.count();
  }

  /**
   * Get alert count
   */
  async getAlertCount(): Promise<number> {
    return this.alertItems.count();
  }

  // ── Assertions ─────────────────────────────────────────────────────

  /**
   * Assert page loaded successfully
   */
  async assertPageLoaded(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Assert services are displayed
   */
  async assertServicesVisible(): Promise<void> {
    const count = await this.getServiceCount();
    expect(count).toBeGreaterThan(0);
  }
}
