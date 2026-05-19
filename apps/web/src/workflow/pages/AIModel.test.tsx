import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AIModel from './AIModel';
import type { HarnessRun } from '@/api/harness';

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

// ── Harness hook mocks ────────────────────────────────────────────────────────

const mockUseHarnessRuns = vi.fn();
const mockUseHarnessRun = vi.fn();

vi.mock('@/hooks/useHarness', () => ({
  useHarnessRuns: (...args: unknown[]) => mockUseHarnessRuns(...args),
  useHarnessRun: (...args: unknown[]) => mockUseHarnessRun(...args),
}));

function makeRun(overrides: Partial<HarnessRun> = {}): HarnessRun {
  return {
    id: 'run-001',
    tenant_id: 'tenant-001',
    account_id: 'acct-001',
    workflow_type: 'roi_calculator_generation',
    initiated_by: 'user',
    status: 'running',
    current_state: 'VALIDATE_CLAIMS',
    value_pack_id: null,
    trace_id: 'trace-abc123',
    created_at: new Date(Date.now() - 60_000).toISOString(),
    updated_at: new Date(Date.now() - 30_000).toISOString(),
    ...overrides,
  };
}

const emptyRunsState = { data: { items: [], total: 0, has_more: false }, isLoading: false, error: null };
const loadingState = { data: undefined, isLoading: true, error: null };
const errorState = { data: undefined, isLoading: false, error: new Error('Network error') };

function renderPage() {
  return render(
    <MemoryRouter>
      <AIModel />
    </MemoryRouter>
  );
}

// ── WorkflowStatusBanner tests ────────────────────────────────────────────────

describe('AIModel page — workflow status banner', () => {
  beforeEach(() => {
    // Default: no run found
    mockUseHarnessRuns.mockReturnValue(emptyRunsState);
    mockUseHarnessRun.mockReturnValue({ data: undefined, isLoading: false, error: null });
  });

  it('shows empty state when no run exists', () => {
    renderPage();
    expect(screen.getByText(/No active workflow run found/i)).toBeInTheDocument();
  });

  it('shows loading state while fetching runs', () => {
    mockUseHarnessRuns.mockReturnValue(loadingState);
    renderPage();
    expect(screen.getByText(/Loading workflow status/i)).toBeInTheDocument();
  });

  it('shows running status when run is active', () => {
    const run = makeRun({ status: 'running' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue({ data: run, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Running')).toBeInTheDocument();
  });

  it('shows queued status', () => {
    const run = makeRun({ status: 'queued', current_state: 'INIT' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue({ data: run, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Queued')).toBeInTheDocument();
  });

  it('shows waiting for review status', () => {
    const run = makeRun({ status: 'waiting_for_human', current_state: 'HUMAN_REVIEW' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue({ data: run, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Waiting for Review')).toBeInTheDocument();
  });

  it('shows failed status', () => {
    const run = makeRun({ status: 'failed', current_state: 'FAILED' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue({ data: run, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Failed')).toBeInTheDocument();
  });

  it('shows cancelled status', () => {
    const run = makeRun({ status: 'cancelled', current_state: 'CANCELLED' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue({ data: run, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Cancelled')).toBeInTheDocument();
  });

  it('shows completed status', () => {
    const run = makeRun({ status: 'completed', current_state: 'DONE' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue({ data: run, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Completed')).toBeInTheDocument();
  });

  it('shows error state when run fetch fails', () => {
    const run = makeRun({ status: 'running' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue(errorState);
    renderPage();
    expect(screen.getByText(/Workflow status unavailable/i)).toBeInTheDocument();
  });

  it('shows loading state while fetching individual run', () => {
    const run = makeRun({ status: 'running' });
    mockUseHarnessRuns.mockReturnValue({ data: { items: [run], total: 1, has_more: false }, isLoading: false, error: null });
    mockUseHarnessRun.mockReturnValue(loadingState);
    renderPage();
    expect(screen.getByText(/Loading workflow status/i)).toBeInTheDocument();
  });

  it('renders the demo data annotation', () => {
    mockUseHarnessRuns.mockReturnValue(emptyRunsState);
    renderPage();
    expect(screen.getByText(/Hypotheses are demo data/i)).toBeInTheDocument();
  });
});

describe('AIModel page — render', () => {
  beforeEach(() => {
    mockUseHarnessRuns.mockReturnValue(emptyRunsState);
    mockUseHarnessRun.mockReturnValue({ data: undefined, isLoading: false, error: null });
  });

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
  beforeEach(() => {
    mockUseHarnessRuns.mockReturnValue(emptyRunsState);
    mockUseHarnessRun.mockReturnValue({ data: undefined, isLoading: false, error: null });
  });

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
  beforeEach(() => {
    mockUseHarnessRuns.mockReturnValue(emptyRunsState);
    mockUseHarnessRun.mockReturnValue({ data: undefined, isLoading: false, error: null });
  });

  it('clicking Build Driver Tree calls setCurrentStep', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /Build Driver Tree/i }));
    expect(mockSetCurrentStep).toHaveBeenCalled();
  });
});
