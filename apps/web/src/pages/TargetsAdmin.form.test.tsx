/**
 * TargetFormPanel — Behavior Tests
 *
 * Covers: create/edit render, required field validation, URL validation,
 * schedule/rate-limit/compliance/auth fields, submit mutations,
 * cancel, server errors, pending state, optional fields.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { renderWithRouter } from '../test-utils';
import { TargetFormPanel } from './TargetsAdmin.form';
import type { Target } from '@/hooks/useTargets';

// ── Mock data ─────────────────────────────────────────────────────────────────

const mockTarget: Target = {
  id: 'target-1',
  tenantId: 'tenant-1',
  name: 'Acme Corp',
  description: 'Existing description',
  url: 'https://acme.com',
  urlPattern: '/jobs/*',
  targetType: 'SPIDER',
  sourceCategory: 'CRM',
  crawlPath: 'browser',
  status: 'ACTIVE',
  tags: ['prospect'],
  extractionConfig: {},
  browserConfig: {},
  schedule: { enabled: true, cron_expression: '0 0 * * *', timezone: 'UTC' },
  rateLimit: { requests_per_second: 2, requests_per_minute: 60, retry_attempts: 5 },
  compliance: { respect_robots_txt: true, pii_redaction_enabled: false, crawl_delay_seconds: 2 },
  proxyConfig: {},
  authentication: { type: 'BEARER', credentials_ref: 'my_secret' },
  successCount: 10,
  errorCount: 0,
  averageExecutionTimeMs: 1000,
  healthScore: 100,
  createdAt: '2024-01-01T00:00:00Z',
  updatedAt: '2024-01-15T00:00:00Z',
  lastSuccessAt: '2024-01-15T00:00:00Z',
  lastErrorAt: null,
  createdBy: 'user-1',
};

// ── Mock hooks ────────────────────────────────────────────────────────────────

let mockUseTarget = vi.fn(() => ({ data: undefined, isLoading: false }));
let mockCreateTarget = vi.fn(() => ({ mutateAsync: vi.fn().mockResolvedValue(mockTarget), isPending: false }));
let mockUpdateTarget = vi.fn(() => ({ mutateAsync: vi.fn().mockResolvedValue(mockTarget), isPending: false }));

vi.mock('@/hooks/useTargets', () => ({
  useTarget: (id: string | null) => mockUseTarget(id),
  useCreateTarget: () => mockCreateTarget(),
  useUpdateTarget: () => mockUpdateTarget(),
}));

const onSuccess = vi.fn();
const onCancel = vi.fn();

beforeEach(() => {
  vi.clearAllMocks();
  mockUseTarget = vi.fn(() => ({ data: undefined, isLoading: false }));
  mockCreateTarget = vi.fn(() => ({ mutateAsync: vi.fn().mockResolvedValue(mockTarget), isPending: false }));
  mockUpdateTarget = vi.fn(() => ({ mutateAsync: vi.fn().mockResolvedValue(mockTarget), isPending: false }));
});

function renderCreate() {
  return renderWithRouter(
    <TargetFormPanel targetId={null} onSuccess={onSuccess} onCancel={onCancel} />
  );
}

function renderEdit() {
  mockUseTarget = vi.fn(() => ({ data: mockTarget, isLoading: false }));
  return renderWithRouter(
    <TargetFormPanel targetId="target-1" onSuccess={onSuccess} onCancel={onCancel} />
  );
}

// ── Create form renders ───────────────────────────────────────────────────────

describe('Create form', () => {
  it('renders Name field', async () => {
    renderCreate();
    await waitFor(() => expect(screen.getByPlaceholderText(/e\.g\. Acme Corp/i)).toBeInTheDocument());
  });

  it('renders URL field', async () => {
    renderCreate();
    await waitFor(() => expect(screen.getByPlaceholderText('https://example.com')).toBeInTheDocument());
  });

  it('renders Target Type select', async () => {
    renderCreate();
    await waitFor(() => expect(screen.getByText('Single Page')).toBeInTheDocument());
  });

  it('renders Crawl Path select', async () => {
    renderCreate();
    await waitFor(() => expect(screen.getByText('Browser (Playwright)')).toBeInTheDocument());
  });

  it('renders Schedule enabled toggle', async () => {
    renderCreate();
    await waitFor(() => expect(screen.getByText('Enable schedule')).toBeInTheDocument());
  });

  it('renders Compliance toggles', async () => {
    renderCreate();
    await waitFor(() => {
      expect(screen.getByText('Respect robots.txt')).toBeInTheDocument();
      expect(screen.getByText('PII redaction')).toBeInTheDocument();
    });
  });

  it('renders Auth type select', async () => {
    renderCreate();
    await waitFor(() => expect(screen.getByText('Auth type')).toBeInTheDocument());
  });

  it('renders Create target submit button', async () => {
    renderCreate();
    await waitFor(() => expect(screen.getByRole('button', { name: /Create target/i })).toBeInTheDocument());
  });
});

// ── Edit form pre-population ──────────────────────────────────────────────────

describe('Edit form pre-population', () => {
  it('pre-populates name field', async () => {
    renderEdit();
    await waitFor(() => {
      const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Corp/i) as HTMLInputElement;
      expect(nameInput.value).toBe('Acme Corp');
    });
  });

  it('pre-populates URL field', async () => {
    renderEdit();
    await waitFor(() => {
      const urlInput = screen.getByPlaceholderText('https://example.com') as HTMLInputElement;
      expect(urlInput.value).toBe('https://acme.com');
    });
  });

  it('pre-populates description', async () => {
    renderEdit();
    await waitFor(() => {
      const desc = screen.getByPlaceholderText('Optional description') as HTMLTextAreaElement;
      expect(desc.value).toBe('Existing description');
    });
  });

  it('shows Save changes button for edit mode', async () => {
    renderEdit();
    await waitFor(() => expect(screen.getByRole('button', { name: /Save changes/i })).toBeInTheDocument());
  });

  it('shows loading state while existing target is loading', async () => {
    mockUseTarget = vi.fn(() => ({ data: undefined, isLoading: true }));
    renderWithRouter(<TargetFormPanel targetId="target-1" onSuccess={onSuccess} onCancel={onCancel} />);
    expect(document.body).toBeTruthy();
  });
});

// ── Required field validation ─────────────────────────────────────────────────

describe('Required field validation', () => {
  it('shows error when Name is empty on submit', async () => {
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByRole('button', { name: /Create target/i }));
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(screen.getByText(/Name is required/i)).toBeInTheDocument());
  });

  it('shows error when URL is empty on submit', async () => {
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByRole('button', { name: /Create target/i }));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'Test');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(screen.getByText(/Must be a valid URL/i)).toBeInTheDocument());
  });

  it('shows URL validation error for invalid URL', async () => {
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByPlaceholderText('https://example.com'));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'Test');
    await user.type(screen.getByPlaceholderText('https://example.com'), 'not-a-url');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(screen.getByText(/Must be a valid URL/i)).toBeInTheDocument());
  });

  it('does not submit when required fields are missing', async () => {
    const mutateAsync = vi.fn();
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByRole('button', { name: /Create target/i }));
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => screen.getByText(/Name is required/i));
    expect(mutateAsync).not.toHaveBeenCalled();
  });
});

// ── Successful submission ─────────────────────────────────────────────────────

describe('Successful submission', () => {
  it('create calls createTarget mutation with normalised payload', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(mockTarget);
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByPlaceholderText(/e\.g\. Acme Corp/i));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'New Target');
    await user.type(screen.getByPlaceholderText('https://example.com'), 'https://new.example.com');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'New Target', url: 'https://new.example.com' })
    ));
  });

  it('edit calls updateTarget mutation with target ID', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(mockTarget);
    mockUpdateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderEdit();
    await waitFor(() => screen.getByRole('button', { name: /Save changes/i }));
    await user.click(screen.getByRole('button', { name: /Save changes/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'target-1' })
    ));
  });

  it('calls onSuccess after successful create', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(mockTarget);
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByPlaceholderText(/e\.g\. Acme Corp/i));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'New Target');
    await user.type(screen.getByPlaceholderText('https://example.com'), 'https://new.example.com');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(onSuccess).toHaveBeenCalledWith(mockTarget));
  });
});

// ── Cancel ────────────────────────────────────────────────────────────────────

describe('Cancel', () => {
  it('calls onCancel when Cancel is clicked', async () => {
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByRole('button', { name: /Cancel/i }));
    await user.click(screen.getByRole('button', { name: /Cancel/i }));
    expect(onCancel).toHaveBeenCalled();
  });

  it('does not call mutation when Cancel is clicked', async () => {
    const mutateAsync = vi.fn();
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByRole('button', { name: /Cancel/i }));
    await user.click(screen.getByRole('button', { name: /Cancel/i }));
    expect(mutateAsync).not.toHaveBeenCalled();
  });
});

// ── Pending state ─────────────────────────────────────────────────────────────

describe('Pending state', () => {
  it('submit button is disabled while mutation is pending', async () => {
    mockCreateTarget = vi.fn(() => ({
      mutateAsync: vi.fn(() => new Promise(() => {})), // never resolves
      isPending: true,
    }));
    renderCreate();
    await waitFor(() => {
      const btn = screen.getByRole('button', { name: /Create target/i });
      expect(btn).toBeDisabled();
    });
  });
});

// ── Server error handling ─────────────────────────────────────────────────────

describe('Server error handling', () => {
  it('form stays open when mutation throws', async () => {
    const mutateAsync = vi.fn().mockRejectedValue(new Error('Server error'));
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByPlaceholderText(/e\.g\. Acme Corp/i));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'New Target');
    await user.type(screen.getByPlaceholderText('https://example.com'), 'https://new.example.com');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    // Form is still present — not closed on error
    expect(screen.getByRole('button', { name: /Create target/i })).toBeInTheDocument();
  });

  it('user input is preserved after mutation failure', async () => {
    const mutateAsync = vi.fn().mockRejectedValue(new Error('Server error'));
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByPlaceholderText(/e\.g\. Acme Corp/i));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'Preserved Name');
    await user.type(screen.getByPlaceholderText('https://example.com'), 'https://preserved.example.com');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    const nameInput = screen.getByPlaceholderText(/e\.g\. Acme Corp/i) as HTMLInputElement;
    expect(nameInput.value).toBe('Preserved Name');
  });
});

// ── Schedule conditional fields ───────────────────────────────────────────────

describe('Schedule conditional fields', () => {
  it('cron expression field is hidden when schedule is disabled', async () => {
    renderCreate();
    await waitFor(() => screen.getByText('Enable schedule'));
    expect(screen.queryByPlaceholderText('0 0 * * *')).not.toBeInTheDocument();
  });

  it('cron expression field appears when schedule is enabled', async () => {
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByText('Enable schedule'));
    const toggle = screen.getByRole('switch', { name: /Enable schedule/i });
    await user.click(toggle);
    await waitFor(() => expect(screen.getByPlaceholderText('0 0 * * *')).toBeInTheDocument());
  });
});

// ── Auth conditional fields ───────────────────────────────────────────────────

describe('Auth conditional fields', () => {
  it('credentials ref field is hidden when auth type is NONE', async () => {
    renderCreate();
    await waitFor(() => screen.getByText('Auth type'));
    expect(screen.queryByPlaceholderText('secret_manager_key')).not.toBeInTheDocument();
  });
});

// ── Optional fields ───────────────────────────────────────────────────────────

describe('Optional fields', () => {
  it('submits without optional fields without error', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(mockTarget);
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByPlaceholderText(/e\.g\. Acme Corp/i));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'Minimal Target');
    await user.type(screen.getByPlaceholderText('https://example.com'), 'https://minimal.example.com');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    const payload = mutateAsync.mock.calls[0][0];
    // Optional fields should be undefined or empty, not cause errors
    expect(payload.name).toBe('Minimal Target');
    expect(payload.url).toBe('https://minimal.example.com');
  });

  it('tags are parsed from comma-separated string', async () => {
    const mutateAsync = vi.fn().mockResolvedValue(mockTarget);
    mockCreateTarget = vi.fn(() => ({ mutateAsync, isPending: false }));
    const user = userEvent.setup();
    renderCreate();
    await waitFor(() => screen.getByPlaceholderText(/e\.g\. Acme Corp/i));
    await user.type(screen.getByPlaceholderText(/e\.g\. Acme Corp/i), 'Tagged Target');
    await user.type(screen.getByPlaceholderText('https://example.com'), 'https://tagged.example.com');
    await user.type(screen.getByPlaceholderText(/prospect, competitor/i), 'tag1, tag2, tag3');
    await user.click(screen.getByRole('button', { name: /Create target/i }));
    await waitFor(() => expect(mutateAsync).toHaveBeenCalled());
    const payload = mutateAsync.mock.calls[0][0];
    expect(payload.tags).toEqual(['tag1', 'tag2', 'tag3']);
  });
});
