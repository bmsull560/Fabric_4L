/**
 * Accessibility audit tests using axe-core and Playwright.
 * 
 * These tests verify WCAG 2.1 AA compliance across all critical pages.
 * Run with: npx playwright test e2e/accessibility/
 */

import { test, expect } from '../fixtures/a11y-test';
import AxeBuilder from '@axe-core/playwright';

// Critical pages that must pass accessibility audit
const CRITICAL_PAGES = [
  { path: '/login', name: 'Login' },
  { path: '/home', name: 'Home Dashboard' },
  { path: '/library/packs', name: 'Value Packs Library' },
  { path: '/discover/accounts', name: 'Account Discovery' },
  { path: '/discover/knowledge/graph', name: 'Knowledge Graph' },
  { path: '/admin/content/formulas', name: 'Formula Governance' },
  { path: '/my-models', name: 'My Models' },
  { path: '/business-case', name: 'Business Case Builder' },
];

// WCAG tags to test against
const WCAG_TAGS = ['wcag2a', 'wcag2aa', 'wcag21aa'];

test.describe('WCAG 2.1 AA Accessibility Audit', () => {
  test.beforeEach(async ({ page }) => {
    // Login before testing protected routes
    await page.goto('/login');
    await page.getByRole('button', { name: 'Sign in' }).click();
    await page.waitForURL(/\/(home|library)/);
  });

  for (const { path, name } of CRITICAL_PAGES) {
    test(`${name} page (${path}) passes axe-core audit`, async ({ page }) => {
      await page.goto(path);
      
      // Wait for page to be fully loaded
      await page.waitForLoadState('networkidle');
      
      // Run axe accessibility scan
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(WCAG_TAGS)
        .analyze();
      
      // Report violations for debugging
      if (accessibilityScanResults.violations.length > 0) {
        console.log(`Violations on ${path}:`, JSON.stringify(
          accessibilityScanResults.violations.map(v => ({
            rule: v.id,
            impact: v.impact,
            description: v.description,
            nodes: v.nodes.length,
          })),
          null,
          2
        ));
      }
      
      // Assert no violations
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  }
});

test.describe('Keyboard Navigation Accessibility', () => {
  test('all interactive elements are keyboard accessible', async ({ page }) => {
    await page.goto('/home');
    
    // Get all interactive elements
    const interactiveElements = page.locator('button, a, input, select, textarea, [role="button"], [role="link"], [tabindex]:not([tabindex="-1"])');
    const count = await interactiveElements.count();
    
    // Test that each element can receive focus
    for (let i = 0; i < Math.min(count, 20); i++) {
      const element = interactiveElements.nth(i);
      
      // Check element is visible and enabled
      const isVisible = await element.isVisible().catch(() => false);
      const isEnabled = await element.isEnabled().catch(() => false);
      
      if (isVisible && isEnabled) {
        // Focus the element
        await element.focus();
        
        // Verify it has focus
        const hasFocus = await element.evaluate(el => el === document.activeElement);
        expect(hasFocus).toBe(true);
      }
    }
  });

  test('focus indicators are visible', async ({ page }) => {
    await page.goto('/home');
    
    // Focus on first button
    const firstButton = page.locator('button').first();
    await firstButton.focus();
    
    // Check for visible focus indicator
    const hasFocusRing = await firstButton.evaluate((el) => {
      const styles = window.getComputedStyle(el);
      const outlineWidth = parseInt(styles.outlineWidth);
      const boxShadow = styles.boxShadow;
      
      // Focus indicator can be outline or box-shadow
      return outlineWidth > 0 || boxShadow !== 'none';
    });
    
    expect(hasFocusRing).toBe(true);
  });

  test('tab order follows logical sequence', async ({ page }) => {
    await page.goto('/home');
    
    // Press Tab multiple times and record focused elements
    const focusedElements: string[] = [];
    
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      const activeElement = await page.evaluate(() => {
        const el = document.activeElement;
        return el ? {
          tag: el.tagName.toLowerCase(),
          role: el.getAttribute('role'),
          ariaLabel: el.getAttribute('aria-label'),
          text: el.textContent?.slice(0, 50),
        } : null;
      });
      
      if (activeElement) {
        focusedElements.push(JSON.stringify(activeElement));
      }
    }
    
    // Should have focused multiple unique elements
    const uniqueElements = new Set(focusedElements);
    expect(uniqueElements.size).toBeGreaterThan(3);
  });
});

test.describe('Screen Reader Accessibility', () => {
  test('agent workflow states announce to screen readers', async ({ page }) => {
    await page.goto('/discover');
    
    // Start an agent workflow
    await page.getByRole('button', { name: /analyze/i }).first().click();
    
    // Check for aria-live region for status updates
    const liveRegion = page.locator('[aria-live="polite"], [aria-live="assertive"], [role="status"], [role="alert"]').first();
    
    // Wait for status to update
    await expect(liveRegion).toBeVisible({ timeout: 5000 });
    
    // Verify status is being announced
    const liveText = await liveRegion.textContent();
    expect(liveText).toBeTruthy();
  });

  test('page titles are descriptive', async ({ page }) => {
    await page.goto('/home');
    
    const title = await page.title();
    expect(title).toBeTruthy();
    expect(title.length).toBeGreaterThan(5);
    expect(title.toLowerCase()).not.toBe('document');  // Should not be default
  });

  test('images have alt text', async ({ page }) => {
    await page.goto('/home');
    
    // Get all images
    const images = page.locator('img');
    const count = await images.count();
    
    for (let i = 0; i < count; i++) {
      const img = images.nth(i);
      const alt = await img.getAttribute('alt');
      const ariaLabel = await img.getAttribute('aria-label');
      const role = await img.getAttribute('role');
      const isPresentation = await img.evaluate(el => 
        el.getAttribute('role') === 'presentation' || 
        el.getAttribute('aria-hidden') === 'true'
      );
      
      // Images should have alt text, aria-label, or be marked as presentation
      if (!isPresentation) {
        expect(alt || ariaLabel).toBeTruthy();
      }
    }
  });

  test('form inputs have associated labels', async ({ page }) => {
    await page.goto('/home');
    
    // Get all input elements
    const inputs = page.locator('input, select, textarea').filter({ has: page.locator(':visible') });
    const count = await inputs.count();
    
    for (let i = 0; i < Math.min(count, 10); i++) {
      const input = inputs.nth(i);
      const inputId = await input.getAttribute('id');
      const ariaLabel = await input.getAttribute('aria-label');
      const ariaLabelledBy = await input.getAttribute('aria-labelledby');
      const hasLabel = await input.evaluate(el => {
        const id = el.id;
        const ariaLabel = el.getAttribute('aria-label');
        const ariaLabelledBy = el.getAttribute('aria-labelledby');
        
        // Check for label element
        const labelFor = id ? document.querySelector(`label[for="${id}"]`) : null;
        const parentLabel = el.closest('label');
        const ariaLabelElement = ariaLabelledBy ? document.getElementById(ariaLabelledBy) : null;
        
        return !!(labelFor || parentLabel || ariaLabel || ariaLabelElement);
      });
      
      if (inputId || ariaLabel || ariaLabelledBy) {
        expect(hasLabel).toBe(true);
      }
    }
  });
});

test.describe('Color Contrast Accessibility', () => {
  test('text meets minimum contrast ratio', async ({ page }) => {
    await page.goto('/home');
    
    // Run axe specifically for color contrast
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .withRules({ 'color-contrast': { enabled: true } })
      .analyze();
    
    const contrastViolations = accessibilityScanResults.violations.filter(
      (v: { id: string }) => v.id === 'color-contrast'
    );
    
    expect(contrastViolations).toEqual([]);
  });
});

test.describe('ARIA and Semantic HTML', () => {
  test('headings follow hierarchical structure', async ({ page }) => {
    await page.goto('/home');
    
    const headingLevels = await page.evaluate(() => {
      const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
      return Array.from(headings).map(h => ({
        level: parseInt(h.tagName[1]),
        text: h.textContent?.slice(0, 50),
      }));
    });
    
    // Should have at least one h1
    const hasH1 = headingLevels.some(h => h.level === 1);
    expect(hasH1).toBe(true);
    
    // Heading levels should not skip (no h3 without h2, etc.)
    let prevLevel = 0;
    for (const heading of headingLevels) {
      // Headings can stay same or go deeper, but shouldn't skip levels
      if (heading.level > prevLevel + 1 && prevLevel > 0) {
        expect(false, `Heading level ${heading.level} follows level ${prevLevel}`).toBe(true);
      }
      if (heading.level > prevLevel || heading.level === prevLevel) {
        prevLevel = heading.level;
      }
    }
  });

  test('navigation landmarks exist', async ({ page }) => {
    await page.goto('/home');
    
    const hasNavigation = await page.locator('nav, [role="navigation"]').count() > 0;
    const hasMain = await page.locator('main, [role="main"]').count() > 0;
    
    expect(hasNavigation).toBe(true);
    expect(hasMain).toBe(true);
  });

  test('buttons have proper roles', async ({ page }) => {
    await page.goto('/home');
    
    const buttons = page.locator('button, [role="button"]');
    const count = await buttons.count();
    
    expect(count).toBeGreaterThan(0);
    
    // All button elements should have proper semantics
    for (let i = 0; i < Math.min(count, 5); i++) {
      const button = buttons.nth(i);
      const role = await button.getAttribute('role');
      const tag = await button.evaluate(el => el.tagName.toLowerCase());
      
      expect(tag === 'button' || role === 'button').toBe(true);
    }
  });
});

test.describe('Modal and Dialog Accessibility', () => {
  test('modals trap focus', async ({ page }) => {
    await page.goto('/home');
    
    // Look for and open a modal
    const modalTrigger = page.locator('button').filter({ hasText: /new|create|add/i }).first();
    
    if (await modalTrigger.isVisible().catch(() => false)) {
      await modalTrigger.click();
      
      // Wait for modal
      const modal = page.locator('[role="dialog"], .modal, [aria-modal="true"]').first();
      await expect(modal).toBeVisible();
      
      // Focus should be within modal
      const activeElement = await page.evaluate(() => document.activeElement);
      const isInModal = await page.evaluate(() => {
        const modal = document.querySelector('[role="dialog"], .modal, [aria-modal="true"]');
        const active = document.activeElement;
        return modal?.contains(active);
      });
      
      expect(isInModal).toBe(true);
    }
  });

  test('modals can be closed with Escape key', async ({ page }) => {
    await page.goto('/home');
    
    const modalTrigger = page.locator('button').filter({ hasText: /new|create|add/i }).first();
    
    if (await modalTrigger.isVisible().catch(() => false)) {
      await modalTrigger.click();
      
      const modal = page.locator('[role="dialog"], .modal, [aria-modal="true"]').first();
      await expect(modal).toBeVisible();
      
      // Press Escape
      await page.keyboard.press('Escape');
      
      // Modal should close (or at least not be visible)
      await expect(modal).not.toBeVisible({ timeout: 2000 });
    }
  });
});

test.describe('Responsive Accessibility', () => {
  test('mobile viewport passes accessibility audit', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/home');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('tablet viewport passes accessibility audit', async ({ page }) => {
    // Set tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    
    await page.goto('/home');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .analyze();
    
    expect(accessibilityScanResults.violations).toEqual([]);
  });
});
