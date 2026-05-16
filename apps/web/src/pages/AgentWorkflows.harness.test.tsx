/**
 * AgentWorkflows — Harness Runs tab regression tests.
 *
 * Guards against:
 *   - Harness Runs tab not rendering (tab label missing)
 *   - Run rows not appearing when data is present
 *   - Cancel action calling useCancelHarnessRun
 *   - HarnessRunDetail sheet opening on View click
 *   - Empty state rendering when no runs exist
 *   - Error state rendering when the query fails
 *
 * All hooks are mocked at the module boundary. This test does not exercise
 * the hooks themselves — useHarness.test.ts covers that.
 *
 * Note: WfPrimitives.Tabs renders tab buttons with role="tab" inside a
 * role="tablist". Selectors use getByRole('tab', ...) accordingly.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { createWrapperWithRouterPath } from '@/test-utils';
import AgentWorkflows from './AgentWorkflows';

// ── Hook mocks ────────────────────────────────────────────────────────────────

const mockUseHarnessRuns = vi.fn();
const mockUseHarnessGates = vi.fn();
const mockUseTransitionHarnessRun = vi.fn();
const mockUseCancelHarnessRun = vi.fn();

vi.mock('@/hooks/useHarness', () => ({
  useHarnessRuns: (...args: unknown[]) => mockUseHarnessRuns(...args),
  useHarnessGates: (...args: unknown[]) => mockUseHarnessGates(...args),
  useTransitionHarnessRun: () => mockUseTransitionHarnessRun(),
  useCancelHarnessRun: () => mockUseCancelHarnessRun(),
}));

const mockUseActiveWorkflows = vi.fn();
const mockUseWorkflowHistory = vi.fn();
const mockUseCancelWorkflow = vi.fn();
const mockUsePauseWorkflow = vi.fn();
const mockUseResumeWorkflow = vi.fn();
const mockUseCreateWorkflow = vi.fn();
const mockUseWorkflowTypes = vi.fn();

vi.mock('@/hooks/useWorkflows', () => ({
  useActiveWorkflows: () => mockUseActiveWorkflows(),
  useWorkflowHistory: () => mockUseWorkflowHistory(),
  useCancelWorkflow: () => mockUseCancelWorkflow(),
  usePauseWorkflow: () => mockUsePauseWorkflow(),
  useResumeWorkflow: () => mockUseResumeWorkflow(),
  useCreateWorkflow: () => mockUseCreateWorkflow(),
  useWorkflowTypes: () => mockUseWorkflowTypes(),
}));

vi.mock('@/components/HarnessRunDetail', () => ({
  HarnessRunDetail: ({ isOpen, runId }: { isOpen: boolean; runId: string | null }) => (
    <div data-testid="harness-run-detail" data-open={String(isOpen)} data-run-id={runId ?? ''} />
  ),
}));

// ── Fixtures ──────────────────────────────────────────────────────────────────

const makeRun = (overrides: Record<string, unknown> = {}) => ({
  id: 'run-001',
  tenant_id: 'tenant-001',
  account_id: 'acct-001',
  workflow_type: 'roi_calculator_generation',
  initiated_by: 'user',
  status: 'running',
  current_state: 'VALIDATE_CLAIMS',
  value_pack_id: null,
  trace_id: 'trace-abc',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:01:00Z',
  ...overrides,
});

const emptyWorkflowState = {
  data: { items: [], total: 0, limit: 20, offset: 0, has_more: false },
  isLoading: false,
  error: null,
};

const emptyGateState = {
  data: { items: [], total: 0 },
  isLoading: false,
  error: null,
};

const idleMutation = { mutate: vi.fn(), mutateAsync: vi.fn(), isPending: false };

function setupDefaultMocks() {
  mockUseActiveWorkflows.mockReturnValue(emptyWorkflowState);
  mockUseWorkflowHistory.mockReturnValue(emptyWorkflowState);
  mockUseCancelWorkflow.mockReturnValue(idleMutation);
  mockUsePauseWorkflow.mockReturnValue(idleMutation);
  mockUseResumeWorkflow.mockReturnValue(idleMutation);
  mockUseCreateWorkflow.mockReturnValue(idleMutation);
  mockUseWorkflowTypes.mockReturnValue({ data: [], isLoading: false });

  mockUseHarnessRuns.mockReturnValue(emptyWorkflowState);
  mockUseHarnessGates.mockReturnValue(emptyGateState);
  mockUseTransitionHarnessRun.mockReturnValue(idleMutation);
  mockUseCancelHarnessRun.mockReturnValue(idleMutation);
}

/** Click the Harness Runs tab. WfPrimitives.Tabs renders role="tab". */
async function openHarnessTab(user: ReturnType<typeof userEvent.setup>) {
  await user.click(screen.getByRole('tab', { name: /harness runs/i }));
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe('AgentWorkflows — Harness Runs tab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    setupDefaultMocks();
  });

  it('renders the Harness Runs tab label', () => {
    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    expect(screen.getByRole('tab', { name: /harness runs/i })).toBeInTheDocument();
  });

  it('shows empty state when no runs exist', async () => {
    const user = userEvent.setup();
    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    await openHarnessTab(user);
    expect(screen.getByText(/no harness runs yet/i)).toBeInTheDocument();
  });

  it('renders run rows when data is present', async () => {
    const user = userEvent.setup();
    mockUseHarnessRuns.mockReturnValue({
      data: {
        items: [
          makeRun({ id: 'run-001', workflow_type: 'roi_calculator_generation', status: 'running' }),
          makeRun({ id: 'run-002', workflow_type: 'business_case_generation', status: 'completed', current_state: 'DONE' }),
        ],
        total: 2,
        limit: 20,
        offset: 0,
        has_more: false,
      },
      isLoading: false,
      error: null,
    });

    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    await openHarnessTab(user);

    expect(screen.getByText('run-001')).toBeInTheDocument();
    expect(screen.getByText('run-002')).toBeInTheDocument();
  });

  it('opens HarnessRunDetail sheet when View is clicked', async () => {
    const user = userEvent.setup();
    mockUseHarnessRuns.mockReturnValue({
      data: { items: [makeRun()], total: 1, limit: 20, offset: 0, has_more: false },
      isLoading: false,
      error: null,
    });

    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    await openHarnessTab(user);

    await user.click(screen.getByRole('button', { name: /view/i }));

    const detail = screen.getByTestId('harness-run-detail');
    expect(detail).toHaveAttribute('data-open', 'true');
    expect(detail).toHaveAttribute('data-run-id', 'run-001');
  });

  it('calls useTransitionHarnessRun.mutate to CANCELLED when Cancel is clicked', async () => {
    const user = userEvent.setup();
    const transitionMutate = vi.fn();
    mockUseTransitionHarnessRun.mockReturnValue({ ...idleMutation, mutate: transitionMutate });
    mockUseHarnessRuns.mockReturnValue({
      data: { items: [makeRun({ status: 'running' })], total: 1, limit: 20, offset: 0, has_more: false },
      isLoading: false,
      error: null,
    });

    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    await openHarnessTab(user);

    await user.click(screen.getByRole('button', { name: /cancel/i }));

    expect(transitionMutate).toHaveBeenCalledWith({
      runId: 'run-001',
      data: { to_state: 'CANCELLED', human_override: true },
    });
  });

  it('shows loading state while runs are fetching', async () => {
    const user = userEvent.setup();
    mockUseHarnessRuns.mockReturnValue({ data: undefined, isLoading: true, error: null });

    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    await openHarnessTab(user);

    expect(screen.getByText(/loading harness runs/i)).toBeInTheDocument();
  });

  it('shows error state when runs query fails', async () => {
    const user = userEvent.setup();
    mockUseHarnessRuns.mockReturnValue({
      data: undefined,
      isLoading: false,
      error: new Error('Network error'),
    });

    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    await openHarnessTab(user);

    expect(screen.getByText(/network error/i)).toBeInTheDocument();
  });

  it('renders KPI card for human-in-loop pending on the dashboard tab', () => {
    render(<AgentWorkflows />, { wrapper: createWrapperWithRouterPath('/workflows') });
    expect(screen.getByText(/human.in.loop pending/i)).toBeInTheDocument();
  });
});
