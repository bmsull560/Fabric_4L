import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for PlatformSettings
 *
 * Route: /admin/system/settings
 * Tier: admin
 *
 * Covers tenant platform configuration with tabs for features, notifications, security, branding
 */
export class PlatformSettingsPage {
  readonly page: Page;

  // Header elements
  readonly header: Locator;
  readonly saveButton: Locator;

  // Tabs
  readonly featuresTab: Locator;
  readonly notificationsTab: Locator;
  readonly securityTab: Locator;
  readonly brandingTab: Locator;

  // Features tab
  readonly advancedAnalyticsToggle: Locator;
  readonly customIntegrationsToggle: Locator;
  readonly aiAssistantToggle: Locator;
  readonly auditTrailToggle: Locator;

  // Notifications tab
  readonly emailAlertsToggle: Locator;
  readonly slackWebhookInput: Locator;

  // Security tab
  readonly require2faToggle: Locator;
  readonly sessionTimeoutInput: Locator;

  // Branding tab
  readonly logoUrlInput: Locator;
  readonly primaryColorInput: Locator;

  // Loading / error
  readonly loadingSkeleton: Locator;
  readonly errorMessage: Locator;

  constructor(page: Page) {
    this.page = page;

    // Header
    this.header = page.getByRole('heading', { name: /platform settings|tenant settings/i });
    this.saveButton = page.getByRole('button', { name: /save|update/i });

    // Tabs
    this.featuresTab = page.getByRole('tab', { name: /features/i });
    this.notificationsTab = page.getByRole('tab', { name: /notifications/i });
    this.securityTab = page.getByRole('tab', { name: /security/i });
    this.brandingTab = page.getByRole('tab', { name: /branding/i });

    // Features tab toggles
    this.advancedAnalyticsToggle = page.locator('label').filter({ hasText: /advanced analytics/i }).locator('..').getByRole('switch').or(
      page.locator('input[type="checkbox"]').first()
    );
    this.customIntegrationsToggle = page.locator('label').filter({ hasText: /custom integrations/i }).locator('..').getByRole('switch');
    this.aiAssistantToggle = page.locator('label').filter({ hasText: /ai assistant/i }).locator('..').getByRole('switch');
    this.auditTrailToggle = page.locator('label').filter({ hasText: /audit trail/i }).locator('..').getByRole('switch');

    // Notifications tab
    this.emailAlertsToggle = page.locator('label').filter({ hasText: /email alerts/i }).locator('..').getByRole('switch');
    this.slackWebhookInput = page.getByPlaceholder(/slack webhook/i).or(
      page.locator('input[type="url"]').first()
    );

    // Security tab
    this.require2faToggle = page.locator('label').filter({ hasText: /two-factor|2fa/i }).locator('..').getByRole('switch');
    this.sessionTimeoutInput = page.getByLabel(/session timeout/i).or(
      page.locator('input[type="number"]').first()
    );

    // Branding tab
    this.logoUrlInput = page.getByLabel(/logo url/i).or(
      page.locator('input[placeholder*="logo"]').first()
    );
    this.primaryColorInput = page.getByLabel(/primary color/i).or(
      page.locator('input[type="color"], input[placeholder*="#"]').first()
    );

    // Loading / error
    this.loadingSkeleton = page.locator('[class*="skeleton"]').first();
    this.errorMessage = page.getByRole('alert').or(page.getByText(/failed to load/i));
  }

  // ── Navigation ────────────────────────────────────────────────────

  /**
   * Navigate to Platform Settings
   */
  async goto(): Promise<void> {
    await this.page.goto('/admin/system/settings');
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
   * Switch to Features tab
   */
  async switchToFeaturesTab(): Promise<void> {
    await this.featuresTab.click();
  }

  /**
   * Switch to Notifications tab
   */
  async switchToNotificationsTab(): Promise<void> {
    await this.notificationsTab.click();
  }

  /**
   * Switch to Security tab
   */
  async switchToSecurityTab(): Promise<void> {
    await this.securityTab.click();
  }

  /**
   * Switch to Branding tab
   */
  async switchToBrandingTab(): Promise<void> {
    await this.brandingTab.click();
  }

  /**
   * Toggle advanced analytics
   */
  async toggleAdvancedAnalytics(): Promise<void> {
    await this.advancedAnalyticsToggle.click();
  }

  /**
   * Check if advanced analytics toggle is checked
   */
  async isAdvancedAnalyticsChecked(): Promise<boolean> {
    return await this.advancedAnalyticsToggle.isChecked();
  }

  /**
   * Toggle AI assistant
   */
  async toggleAiAssistant(): Promise<void> {
    await this.aiAssistantToggle.click();
  }

  /**
   * Set Slack webhook URL
   */
  async setSlackWebhook(url: string): Promise<void> {
    await this.slackWebhookInput.fill(url);
  }

  /**
   * Click save button
   */
  async clickSave(): Promise<void> {
    await this.saveButton.click();
  }

  // ── Assertions ─────────────────────────────────────────────────────

  /**
   * Assert page loaded successfully
   */
  async assertPageLoaded(): Promise<void> {
    await expect(this.header).toBeVisible();
  }

  /**
   * Assert Features tab is active
   */
  async assertFeaturesTabActive(): Promise<void> {
    await expect(this.featuresTab).toHaveAttribute('aria-selected', 'true');
  }
}
