import { Page, Locator, expect } from '@playwright/test';

/**
 * Page Object for App Shell (navigation, header, sidebar)
 *
 * Provides access to global navigation elements that appear
 * on all pages within the application.
 */
export class AppShellPage {
  readonly page: Page;

  // Navigation sidebar
  readonly sidebar: Locator;
  readonly navigation: Locator;

  // Navigation links by section
  readonly commandCenterLink: Locator;
  readonly extractionEngineLink: Locator;
  readonly valuePacksLink: Locator;
  readonly graphExplorerLink: Locator;
  readonly ontologyLink: Locator;
  readonly valueTreesLink: Locator;
  readonly formulaBuilderLink: Locator;
  readonly agentWorkflowsLink: Locator;
  readonly decisionTraceLink: Locator;
  readonly adminSection: Locator;

  // User menu / tier indicator
  readonly userMenu: Locator;
  readonly tierBadge: Locator;
  readonly advancedModeToggle: Locator;

  // Theme toggle
  readonly themeToggle: Locator;

  // Mobile menu (hamburger)
  readonly mobileMenuButton: Locator;

  constructor(page: Page) {
    this.page = page;

    // App shell containers
    this.sidebar = page.locator('aside, [class*="sidebar"], nav[aria-label="Main navigation"]').first();
    this.navigation = page.getByRole('navigation');

    // Primary navigation links - using accessible selectors
    this.commandCenterLink = page.getByRole('link', { name: /command center/i });
    this.extractionEngineLink = page.getByRole('link', { name: /extraction engine/i });
    this.valuePacksLink = page.getByRole('link', { name: /value packs/i });
    this.graphExplorerLink = page.getByRole('link', { name: /graph explorer/i });
    this.ontologyLink = page.getByRole('link', { name: /ontology/i });
    this.valueTreesLink = page.getByRole('link', { name: /value trees/i });
    this.formulaBuilderLink = page.getByRole('link', { name: /formula/i });
    this.agentWorkflowsLink = page.getByRole('link', { name: /agents?|workflows?/i });
    this.decisionTraceLink = page.getByRole('link', { name: /decision trace|audit/i });

    // Admin section
    this.adminSection = page.locator('[class*="admin"], [data-testid="admin-section"]').or(
      page.getByRole('button', { name: /admin/i })
    );

    // User controls
    this.userMenu = page.getByRole('button', { name: /user|account|profile/i }).or(
      page.locator('[data-testid="user-menu"]').first()
    );
    this.tierBadge = page.locator('[data-testid="tier-badge"]').or(
      page.locator('[class*="badge"]').filter({ hasText: /standard|advanced|admin/i }).first()
    );
    this.advancedModeToggle = page.getByRole('switch', { name: /advanced mode/i }).or(
      page.getByLabel(/advanced mode/i)
    );

    // Theme
    this.themeToggle = page.getByRole('button', { name: /theme|dark|light/i });

    // Mobile
    this.mobileMenuButton = page.getByRole('button', { name: /menu|navigation/i }).or(
      page.locator('[aria-label*="menu"]').first()
    );
  }

  /**
   * Navigate to a specific route via sidebar
   */
  async navigateTo(route: string): Promise<void> {
    switch (route.toLowerCase()) {
      case 'command-center':
        await this.commandCenterLink.click();
        break;
      case 'extraction-engine':
        await this.extractionEngineLink.click();
        break;
      case 'value-packs':
        await this.valuePacksLink.click();
        break;
      case 'graph-explorer':
        await this.graphExplorerLink.click();
        break;
      case 'ontology':
        await this.ontologyLink.click();
        break;
      case 'value-trees':
        await this.valueTreesLink.click();
        break;
      case 'formula-builder':
        await this.formulaBuilderLink.click();
        break;
      case 'agent-workflows':
        await this.agentWorkflowsLink.click();
        break;
      case 'decision-trace':
        await this.decisionTraceLink.click();
        break;
      default:
        throw new Error(`Unknown route: ${route}`);
    }
  }

  /**
   * Check if a navigation link is visible (indicating tier access)
   */
  async isNavigationLinkVisible(linkName: string): Promise<boolean> {
    const link = this.page.getByRole('link', { name: new RegExp(linkName, 'i') });
    return link.isVisible();
  }

  /**
   * Get all visible navigation items
   */
  async getVisibleNavigationItems(): Promise<string[]> {
    const links = this.navigation.getByRole('link');
    const texts: string[] = [];
    const count = await links.count();

    for (let i = 0; i < count; i++) {
      const text = await links.nth(i).textContent();
      if (text) texts.push(text.trim());
    }

    return texts;
  }

  /**
   * Toggle advanced mode
   */
  async toggleAdvancedMode(): Promise<void> {
    await this.advancedModeToggle.click();
  }

  /**
   * Open user menu
   */
  async openUserMenu(): Promise<void> {
    await this.userMenu.click();
  }

  /**
   * Toggle theme (dark/light)
   */
  async toggleTheme(): Promise<void> {
    await this.themeToggle.click();
  }

  /**
   * Open mobile navigation menu
   */
  async openMobileMenu(): Promise<void> {
    await this.mobileMenuButton.click();
  }

  /**
   * Assert navigation sidebar is visible
   */
  async assertSidebarVisible(): Promise<void> {
    await expect(this.sidebar).toBeVisible();
  }

  /**
   * Assert specific navigation links are visible based on tier
   */
  async assertNavigationForTier(tier: 'standard' | 'advanced' | 'admin'): Promise<void> {
    // All tiers see these
    await expect(this.commandCenterLink).toBeVisible();
    await expect(this.valuePacksLink).toBeVisible();

    // Advanced and above
    if (tier === 'advanced' || tier === 'admin') {
      await expect(this.extractionEngineLink).toBeVisible();
      await expect(this.graphExplorerLink).toBeVisible();
      await expect(this.valueTreesLink).toBeVisible();
    }

    // Admin only
    if (tier === 'admin') {
      await expect(this.adminSection).toBeVisible();
    }
  }

  /**
   * Assert restricted navigation is not visible
   */
  async assertRestrictedLinksNotVisible(restrictedLinks: string[]): Promise<void> {
    for (const link of restrictedLinks) {
      const locator = this.page.getByRole('link', { name: new RegExp(link, 'i') });
      await expect(locator).toBeHidden();
    }
  }
}
