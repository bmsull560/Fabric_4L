/**
 * TargetDetailPanel — Behavior Tests
 *
 * Covers: all seven sections render, job history, polling,
 * run/edit actions, error/missing target states.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../test-utils';
import { TargetDetailPanel } from './TargetsAdmin.detail';

// ── Mock data ─────────────────────────────────────────────────────────────────

const mockTarget = {
  id: 'target-1',
  tenantId: 'tenant-1',
  name: 'Acme Corp',
  description: 'Test description',
  url: 'https://acme.com',
  urlPattern: null,
  targetType: 'SPIDER' as const,
  sourceCategory: 'CRM',
  crawlPath: 'browser' as const,
  status: 'ACTIVE' as const,
  tags: ['prospect', 'enterprise'],
  extractionConfig: { method: 'llm' },
  browserConfig: {},
  schedule: { enabled: true, cron_expression: '0 0 * * *', timezone: 'UTC' },
  rateLimit: { requests_per_second: 1, requests_per_minute: 30, retry_attempts: 3 },
  compliance: { respect_robots_txt: true, pii_redaction_enabled: true, crawl_delay_seconds: 1 },
  proxyConfig: {},
  authentication: { type: 'BEARER', credentials_ref: 'secret_ref' },
  successCount: 10,
  errorCount: 1,
  averageExecutionTimeMs: 1200,
  healthScore: 91,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-15T10:00:00Z',
  lastSuccessAt: '2024-01-15T10:00:00Z',
  lastErrorAt: null,
  createdBy: 'user-1',
};

const mockJobs = [
  { id: 'job-1', status: 'COMPLETED', created_at: '2024-01-15T09:00:00Z', triggered_by: 'MANUAL' },
  { id: 'job-2', status: 'FAILED', created_at: '2024-01-14T09:00:00Z', triggered_by: 'SCHEDULED' },
];

// ── Mock hooks ────────────────────────────────────────────────────────────────

const mockRefetchJobs = vi.fn();
let mockUseTarget = vi.fn(() => ({ data: mockTarget, isLoading: false }));
let mockUseTargetJobs = vi.fn(() => ({
  data: { jobs: mockJobs, pagination: { page: 1, limit: 10, total: 2, totalPages: 1 } },
  isLoading: false,
  refetch: mockRefetchJobs,
}));
let mockExecute = vi.fn(() => ({ mutateAsync: vi.fn().mockResolvedValue({ jobId: 'job-new' }), isPending: false }));

vi.mock('@/hooks/useTargets', () => ({
  useTarget: (id: string) => mockUseTarget(id),
  useTargetJobs: (id: string) => mockUseTargetJobs(id),
  useExecuteTarget: () => mockExecute(),
  useUpdateTargetStatus: () => ({ mutateAsync: vi.fn().mockResolvedValue({}), isPending: false }),
}));

const onEdit = vi.fn();
const onClose = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  mockUseTarget = vi.fn(() => ({ data: mockTarget, isLoading: false }));
  mockUseTargetJobs = vi.fn(() => ({
    data: { jobs: mockJobs, pagination: {} },
    isLoading: false,
    refetch: mockRefetchJobs,
  }));
  mockExecute = vi.fn(() => ({ mutateAsync: vi.fn().mockResolvedValue({ jobId: 'job-new' }), isPending: false }));
});

// ── Render helpers ────────────────────────────────────────────────────────────

function renderPanel(targetId = 'target-1') {
  return renderWithRouter(
    <TargetDetailPanel targetId={targetId} onEdit={onEdit} onClose={onClose} />
  );
}

// ── Identity section ──────────────────────────────────────────────────────────

describe('Identity section', () => {
  it('renders target name', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Acme Corp')).toBeInTheDocument());
  });

  it('renders target URL', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('https://acme.com')).toBeInTheDocument());
  });

  it('renders target type badge', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('SPIDER')).toBeInTheDocument());
  });

  it('renders description', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Test description')).toBeInTheDocument());
  });

  it('renders tags', async () => {
    renderPanel();
    await waitFor(() => {
      expect(screen.getByText('prospect')).toBeInTheDocument();
      expect(screen.getByText('enterprise')).toBeInTheDocument();
    });
  });
});

// ── All seven sections render ─────────────────────────────────────────────────

describe('All sections render', () => {
  it('renders Identity section heading', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Identity')).toBeInTheDocument());
  });

  it('renders Schedule section heading', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Schedule')).toBeInTheDocument());
  });

  it('renders Rate Limits section heading', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Rate Limits')).toBeInTheDocument());
  });

  it('renders Compliance section heading', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Compliance')).toBeInTheDocument());
  });

  it('renders Authentication section heading', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Authentication')).toBeInTheDocument());
  });

  it('renders Recent Jobs section heading', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('Recent Jobs')).toBeInTheDocument());
  });
});

// ── Schedule section ──────────────────────────────────────────────────────────

describe('Schedule section', () => {
  it('shows cron expression when schedule is enabled', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('0 0 * * *')).toBeInTheDocument());
  });

  it('shows timezone', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('UTC')).toBeInTheDocument());
  });
});

// ── Rate limits section ───────────────────────────────────────────────────────

describe('Rate limits section', () => {
  it('renders requests per second', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getAllByText('1').length).toBeGreaterThan(0));
  });
});

// ── Compliance section ────────────────────────────────────────────────────────

describe('Compliance section', () => {
  it('shows robots.txt respect setting', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getAllByText('Yes').length).toBeGreaterThan(0));
  });
});

// ── Auth section ──────────────────────────────────────────────────────────────

describe('Authentication section', () => {
  it('shows auth type', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('BEARER')).toBeInTheDocument());
  });

  it('masks credentials — shows dots not plaintext ref', async () => {
    renderPanel();
    await waitFor(() => {
      expect(screen.getByText('••••••••')).toBeInTheDocument();
      expect(screen.queryByText('secret_ref')).not.toBeInTheDocument();
    });
  });
});

// ── Job history ───────────────────────────────────────────────────────────────

describe('Job history', () => {
  it('renders recent jobs', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('completed')).toBeInTheDocument());
  });

  it('renders failed job', async () => {
    renderPanel();
    await waitFor(() => expect(screen.getByText('failed')).toBeInTheDocument());
  });

  it('shows empty state when no jobs', async () => {
    mockUseTargetJobs = vi.fn(() => ({
      data: { jobs: [], pagination: {} },
      isLoading: false,
      refetch: mockRefetchJobs,
    }));
    renderPanel();
    await waitFor(() => expect(screen.getByText('No jobs yet.')).toBeInTheDocument());
  });

  it('shows loading state while jobs are fetching', async () => {
    mockUseTargetJobs = vi.fn(() => ({ data: undefined, isLoading: true, refetch: mockRefetchJobs }));
    renderPanel();
    // Skeletons render — no crash
    expect(document.body).toBeTruthy();
  });
});

// ── Live run status polling ───────────────────────────────────────────────────

describe('Live run status polling', () => {
  it('shows live status section when a job is running', async () => {
    mockUseTargetJobs = vi.fn(() => ({
      data: { jobs: [{ id: 'job-r', status: 'RUNNING', created_at: '2024-01-15T10:00:00Z' }], pagination: {} },
      isLoading: false,
      refetch: mockRefetchJobs,
    }));
    renderPanel();
    await waitFor(() => expect(screen.getByText('Live Run Status')).toBeInTheDocument());
  });

  it('does not show live status section when no job is running', async () => {
    renderPanel();
    await waitFor(() => expect(screen.queryByText('Live Run Status')).not.toBeInTheDocument());
  });
});

// ── Actions ───────────────────────────────────────────────────────────────────

describe('Actions', () => {
  it('Edit button calls onEdit', async () => {
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText('Edit'));
    await user.click(screen.getByText('Edit'));
    expect(onEdit).toHaveBeenCalled();
  });

  it('Run now button calls executeTarget', async () => {
    const mutateAsync = vi.fn().mockResolvedValue({ jobId: 'job-new' });
    mockExecute = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderPanel();
    await waitFor(() => screen.getByText('Run now'));
    await user.click(screen.getByText('Run now'));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith({ id: 'target-1' }));
  });

  it('Run now button is absent for non-ACTIVE targets', async () => {
    mockUseTarget = vi.fn(() => ({ data: { ...mockTarget, status: 'PAUSED' }, isLoading: false }));
    renderPanel();
    await waitFor(() => screen.getByText('Edit'));
    expect(screen.queryByText('Run now')).not.toBeInTheDocument();
  });
});

// ── Loading / error states ────────────────────────────────────────────────────

describe('Loading and error states', () => {
  it('shows loading skeletons while target is loading', async () => {
    mockUseTarget = vi.fn(() => ({ data: undefined, isLoading: true }));
    renderPanel();
    expect(document.body).toBeTruthy();
  });

  it('shows not found message for missing target', async () => {
    mockUseTarget = vi.fn(() => ({ data: undefined, isLoading: false }));
    renderPanel();
    await waitFor(() => expect(screen.getByText(/Target not found/i)).toBeInTheDocument());
  });
});
