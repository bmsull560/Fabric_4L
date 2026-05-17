import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import AIModel from './AIModel';

vi.mock('../components/WorkflowLayout', () => ({
  WorkflowLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockSetCurrentStep = vi.fn();

vi.mock('../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    setCurrentStep: mockSetCurrentStep,
  }),
}));

vi.mock('@/hooks/useNavigation', () => ({
  useNavigation: () => ({ navigateTo: vi.fn() }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <AIModel />
    </MemoryRouter>
  );
}

describe('AIModel page — render', () => {
  it('renders the page heading', () => {
    renderPage();
    expect(screen.getByText('AI-Generated Value Model')).toBeInTheDocument();
  });

  it('renders all 5 hypothesis cards', () => {
    renderPage();
    expect(screen.getByText('Reduce Labor Dependency in Assembly')).toBeInTheDocument();
    expect(screen.getByText('Eliminate Torque Defects')).toBeInTheDocument();
    expect(screen.getByText('Increase Throughput on 3 Shifts')).toBeInTheDocument();
    expect(screen.getByText('Reduce Ergonomic Injuries')).toBeInTheDocument();
    expect(screen.getByText('Cut Changeover Time for Mixed-Model')).toBeInTheDocument();
  });

  it('renders the stat cards', () => {
    renderPage();
    expect(screen.getByText('AI Hypotheses')).toBeInTheDocument();
    expect(screen.getByText('Approved')).toBeInTheDocument();
  });

  it('renders the continue button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /Build Driver Tree/i })).toBeInTheDocument();
  });

  it('renders the regenerate button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /Regenerate/i })).toBeInTheDocument();
  });
});

describe('AIModel page — hypothesis approval', () => {
  it('shows Approve, Modify, and Skip buttons for each suggested hypothesis', () => {
    renderPage();
    const approveButtons = screen.getAllByRole('button', { name: /Approve/i });
    expect(approveButtons.length).toBe(5);
  });

  it('approving a hypothesis shows the approved state label', async () => {
    const user = userEvent.setup();
    renderPage();

    const approveButtons = screen.getAllByRole('button', { name: /Approve/i });
    await user.click(approveButtons[0]);

    expect(screen.getByText('Approved — will build driver tree')).toBeInTheDocument();
  });

  it('skipping a hypothesis shows the skipped state', async () => {
    const user = userEvent.setup();
    renderPage();

    const skipButtons = screen.getAllByRole('button', { name: /Skip/i });
    await user.click(skipButtons[0]);

    expect(screen.getByText('Skipped')).toBeInTheDocument();
  });

  it('approved hypothesis no longer shows Approve/Skip buttons', async () => {
    const user = userEvent.setup();
    renderPage();

    const approveButtons = screen.getAllByRole('button', { name: /Approve/i });
    const initialCount = approveButtons.length;
    await user.click(approveButtons[0]);

    const remainingApprove = screen.getAllByRole('button', { name: /Approve/i });
    expect(remainingApprove.length).toBe(initialCount - 1);
  });

  it('approved count stat updates after approving a hypothesis', async () => {
    const user = userEvent.setup();
    renderPage();

    // Before approving: sub-text shows "5 pending" (all 5 hypotheses pending)
    expect(screen.getByText('5 pending')).toBeInTheDocument();

    const approveButtons = screen.getAllByRole('button', { name: /Approve/i });
    await user.click(approveButtons[0]);

    // After approving 1: sub-text updates to "4 pending"
    expect(screen.getByText('4 pending')).toBeInTheDocument();
  });
});

describe('AIModel page — navigation', () => {
  it('clicking Build Driver Tree calls setCurrentStep', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /Build Driver Tree/i }));
    expect(mockSetCurrentStep).toHaveBeenCalled();
  });
});
