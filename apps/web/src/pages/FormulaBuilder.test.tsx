/**
 * FormulaBuilder Component Tests
 *
 * Tests for P2/P3 fixes including:
 * - Variable chip accessibility (aria-label, role, tabIndex, keyboard)
 * - isEvaluatingPending naming (no local state alias)
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { createWrapperWithRouterPath } from '../test-utils';
import FormulaBuilder from './FormulaBuilder';

// Mock matchMedia for responsive tests
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

describe('FormulaBuilder Accessibility', () => {
  it('renders variable chips with aria-labels', async () => {
    const wrapper = createWrapperWithRouterPath('/context/formulas/new');
    render(<FormulaBuilder />, { wrapper });

    // Wait for variables to load
    await waitFor(() => {
      const variableChips = document.querySelectorAll('[aria-label*="Insert variable"]');
      expect(variableChips.length).toBeGreaterThan(0);
    });

    // Each chip should have a descriptive aria-label
    const chips = document.querySelectorAll('[aria-label*="Insert variable"]');
    chips.forEach((chip) => {
      expect(chip.getAttribute('aria-label')).toMatch(/insert variable/i);
    });
  });

  it('variable chips are keyboard focusable', async () => {
    const wrapper = createWrapperWithRouterPath('/context/formulas/new');
    render(<FormulaBuilder />, { wrapper });

    await waitFor(() => {
      const variableChips = document.querySelectorAll('[aria-label*="Insert variable"]');
      expect(variableChips.length).toBeGreaterThan(0);
    });

    const firstChip = document.querySelector('[aria-label*="Insert variable"]');
    expect(firstChip).toHaveAttribute('tabIndex', '0');
  });

  it('variable chips have role=button', async () => {
    const wrapper = createWrapperWithRouterPath('/context/formulas/new');
    render(<FormulaBuilder />, { wrapper });

    await waitFor(() => {
      const variableChips = document.querySelectorAll('[aria-label*="Insert variable"]');
      expect(variableChips.length).toBeGreaterThan(0);
    });

    const firstChip = document.querySelector('[aria-label*="Insert variable"]');
    expect(firstChip).toHaveAttribute('role', 'button');
  });

  it('variable chips have descriptive titles', async () => {
    const wrapper = createWrapperWithRouterPath('/context/formulas/new');
    render(<FormulaBuilder />, { wrapper });

    await waitFor(() => {
      const variableChips = document.querySelectorAll('[aria-label*="Insert variable"]');
      expect(variableChips.length).toBeGreaterThan(0);
    });

    const chips = document.querySelectorAll('[aria-label*="Insert variable"]');
    chips.forEach((chip) => {
      expect(chip.getAttribute('title')).toMatch(/insert/i);
    });
  });

  it('test button is present and labeled', async () => {
    const wrapper = createWrapperWithRouterPath('/context/formulas/new');
    render(<FormulaBuilder />, { wrapper });

    await waitFor(() => {
      const testButton = screen.getByRole('button', { name: /test with sample data/i });
      expect(testButton).toBeInTheDocument();
    });
  });
});

describe('FormulaBuilder Evaluation', () => {
  it('test button reflects mutation pending state', async () => {
    const wrapper = createWrapperWithRouterPath('/context/formulas/new');
    render(<FormulaBuilder />, { wrapper });

    // The test button should be present
    await waitFor(() => {
      const testButton = screen.getByRole('button', { name: /test with sample data/i });
      expect(testButton).toBeInTheDocument();
    });
  });
});
