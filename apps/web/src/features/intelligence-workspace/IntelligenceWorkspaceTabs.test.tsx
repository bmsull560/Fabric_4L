import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import IntelligenceWorkspaceTabs from './IntelligenceWorkspaceTabs';

vi.mock('./hooks/useWorkspaceContext', () => ({
  useWorkspaceContext: () => ({ accountId: 'acct-123', tabId: 'signals' }),
}));

describe('IntelligenceWorkspaceTabs', () => {
  it('renders horizontal tablist navigation', () => {
    render(<MemoryRouter><IntelligenceWorkspaceTabs /></MemoryRouter>);
    expect(screen.getByRole('tablist')).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: 'Signals' })).toBeInTheDocument();
  });

  it('marks only active tab as selected', () => {
    render(<MemoryRouter><IntelligenceWorkspaceTabs /></MemoryRouter>);
    expect(screen.getByRole('tab', { name: 'Signals' })).toHaveAttribute('aria-selected', 'true');
    expect(screen.getByRole('tab', { name: 'Account Enrichment' })).toHaveAttribute('aria-selected', 'false');
  });
});
