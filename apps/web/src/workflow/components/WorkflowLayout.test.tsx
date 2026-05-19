import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import { WorkflowLayout } from './WorkflowLayout';

vi.mock('../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    sessionId: null,
    prospect: null,
    initSession: vi.fn(),
    setWorkflowContext: vi.fn(),
  }),
}));

function renderLayout(path: string, children: React.ReactNode = <div>page content</div>) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <WorkflowLayout>{children}</WorkflowLayout>
    </MemoryRouter>
  );
}

describe('WorkflowLayout — render', () => {
  it('renders children', () => {
    renderLayout('/workflow');
    expect(screen.getByText('page content')).toBeInTheDocument();
  });

  it('renders the Workflow header title', () => {
    renderLayout('/workflow');
    expect(screen.getByText('Workflow')).toBeInTheDocument();
  });

  it('renders the subtitle', () => {
    renderLayout('/workflow');
    expect(screen.getByText('Guided value-case creation')).toBeInTheDocument();
  });
});

describe('WorkflowLayout — step navigation', () => {
  it('renders all 7 step labels', () => {
    renderLayout('/workflow');
    expect(screen.getByText('Prospect')).toBeInTheDocument();
    expect(screen.getByText('Intelligence')).toBeInTheDocument();
    expect(screen.getByText('AI Model')).toBeInTheDocument();
    expect(screen.getByText('Driver Tree')).toBeInTheDocument();
    expect(screen.getByText('Evidence')).toBeInTheDocument();
    expect(screen.getByText('Calculator')).toBeInTheDocument();
    expect(screen.getByText('Value Case')).toBeInTheDocument();
  });

  it('renders step links as anchor elements', () => {
    renderLayout('/workflow');
    const links = screen.getAllByRole('link');
    const hrefs = links.map((l) => l.getAttribute('href'));
    expect(hrefs).toContain('/workflow');
    expect(hrefs).toContain('/workflow/intelligence');
    expect(hrefs).toContain('/workflow/ai-model');
    expect(hrefs).toContain('/workflow/driver-tree');
    expect(hrefs).toContain('/workflow/evidence');
    expect(hrefs).toContain('/workflow/calculator');
    expect(hrefs).toContain('/workflow/value-case');
  });

  it('marks the Prospect step active on the /workflow path', () => {
    renderLayout('/workflow');
    // Step 0 path is '/workflow' — exact match → active
    const prospectLink = screen.getByRole('link', { name: /Prospect/i });
    const innerDiv = prospectLink.querySelector('div');
    expect(innerDiv?.className).toContain('bg-primary/10');
  });

  it('inactive steps use hover:bg-muted class', () => {
    renderLayout('/workflow');
    // Intelligence is step 1 — not active on /workflow
    const intelligenceLink = screen.getByRole('link', { name: /Intelligence/i });
    const innerDiv = intelligenceLink.querySelector('div');
    expect(innerDiv?.className).toContain('hover:bg-muted');
  });
});

describe('WorkflowLayout — missing context warning', () => {
  it('does not show missing context alert on the prospect step', () => {
    // Step 0 is always active (startsWith match), requiresAccountContext = false
    renderLayout('/workflow');
    expect(screen.queryByText(/Missing workflow context/i)).not.toBeInTheDocument();
  });

  it('renders the main content area', () => {
    renderLayout('/workflow');
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('renders children inside the main area', () => {
    renderLayout('/workflow');
    const main = screen.getByRole('main');
    expect(main).toContainElement(screen.getByText('page content'));
  });
});
