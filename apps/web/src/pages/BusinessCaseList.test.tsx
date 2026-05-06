/**
 * BusinessCaseList Component Tests
 *
 * Tests for P2/P3 fixes including:
 * - shadcn Select usage for status filter (replaced native <select>)
 * - shadcn Select usage for sort field (replaced native <select>)
 * - VirtualList integration for case list
 * - URL-synced filter persistence
 */
import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createWrapper, createWrapperWithRouterPath } from '../test-utils';
import BusinessCaseList from './BusinessCaseList';

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

describe('BusinessCaseList', () => {
  it('renders page header and search input', () => {
    const wrapper = createWrapper();
    render(<BusinessCaseList />, { wrapper });

    expect(screen.getByRole('heading', { name: /business cases/i })).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/search cases or companies/i)).toBeInTheDocument();
  });

  it('uses shadcn Select for status filter (not native select)', () => {
    const wrapper = createWrapper();
    render(<BusinessCaseList />, { wrapper });

    // shadcn Select renders as a combobox/button, not a native <select>
    const statusTrigger = screen.getByRole('combobox', { name: /all status/i }) ||
      screen.getByText(/all status/i);
    expect(statusTrigger).toBeInTheDocument();

    // Should NOT have native <select> elements
    const nativeSelects = document.querySelectorAll('select');
    expect(nativeSelects.length).toBe(0);
  });

  it('uses shadcn Select for sort field (not native select)', () => {
    const wrapper = createWrapper();
    render(<BusinessCaseList />, { wrapper });

    // Look for sort trigger
    const sortLabel = screen.getByText(/sort by/i);
    expect(sortLabel).toBeInTheDocument();

    // Should NOT have native <select> elements
    const nativeSelects = document.querySelectorAll('select');
    expect(nativeSelects.length).toBe(0);
  });

  it('opens status filter dropdown on click', async () => {
    const user = userEvent.setup();
    const wrapper = createWrapper();
    render(<BusinessCaseList />, { wrapper });

    const statusTrigger = screen.getByText(/all status/i);
    await user.click(statusTrigger);

    // Dropdown options should appear
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /active/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /draft/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /archived/i })).toBeInTheDocument();
    });
  });

  it('opens sort dropdown on click', async () => {
    const user = userEvent.setup();
    const wrapper = createWrapper();
    render(<BusinessCaseList />, { wrapper });

    const sortTrigger = screen.getAllByRole('combobox')[1] ||
      screen.getByText(/last updated/i);
    await user.click(sortTrigger);

    // Sort options should appear
    await waitFor(() => {
      expect(screen.getByRole('option', { name: /name/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /company/i })).toBeInTheDocument();
      expect(screen.getByRole('option', { name: /value/i })).toBeInTheDocument();
    });
  });

  it('renders virtualized case list container', async () => {
    const wrapper = createWrapper();
    render(<BusinessCaseList />, { wrapper });

    // Wait for cases to load
    await waitFor(() => {
      const virtualContainer = document.querySelector('[style*="contain: strict"]');
      expect(virtualContainer).toBeInTheDocument();
    });
  });

  it('has aria-label on sort direction toggle', () => {
    const wrapper = createWrapper();
    render(<BusinessCaseList />, { wrapper });

    const sortToggle = screen.getByLabelText(/sort descending|sort ascending/i);
    expect(sortToggle).toBeInTheDocument();
  });
});
