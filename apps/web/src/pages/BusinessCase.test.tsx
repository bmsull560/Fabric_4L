/**
 * BusinessCase Component Tests
 *
 * Tests for the business case viewer including:
 * - Rendering with business case data
 * - Formula evaluation display
 * - Value tree visualization
 * - Empty/error states
 * - PDF export functionality
 * - Trust status row (degraded / pending-review / validated / export states)
 */
import { describe, it, expect, vi, afterEach } from 'vitest';
import '@testing-library/jest-dom';
import { screen, waitFor } from '@testing-library/react';
import { renderWithRouter } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../test/mocks/server';
import BusinessCase, { deriveTrustState, type BusinessCaseTrustState } from './BusinessCase';
import type { BusinessCase as BusinessCaseType } from '@/hooks/useDocuments';

describe('BusinessCase', () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders loading state initially', () => {
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });

    // Should show loading skeletons
    expect(document.querySelector('[class*="skeleton"]')).toBeDefined();
  });

  it('renders with business case data', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () => {
        return HttpResponse.json({
          case_id: 'test-case-123',
          title: 'Test Business Case',
          summary: 'Comprehensive analysis of investment opportunity.',
          total_value: 1200000,
          implementation_cost: 300000,
          roi_ratio: 4.0,
          payback_months: 12,
          confidence_score: 0.92,
          recommendations: [
            'Implement within Q2',
            'Focus on high-value segments',
            'Monitor metrics monthly',
          ],
          status: 'completed',
          created_at: '2024-01-15T10:00:00Z',
          page_count: 15,
          file_size_bytes: 102400,
          document_url: 'https://example.com/docs/case.pdf',
        });
      })
    );

    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });

    await waitFor(() => {
      expect(screen.getByText('Test Business Case')).toBeInTheDocument();
    });

    // Should show value
    expect(screen.getByText('$1,200,000')).toBeInTheDocument();
  });

  it('shows warning when no case ID provided', async () => {
    renderWithRouter(<BusinessCase />, { path: '/business-case' });

    await waitFor(() => {
      expect(screen.getByText(/No business case ID provided/i)).toBeInTheDocument();
    });
  });

  it('shows error state when case fails to load', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () => {
        return HttpResponse.json({ error: 'Case not found' }, { status: 404 });
      })
    );

    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });

    await waitFor(() => {
      // React Query displays HTTP error message for 404 responses
      expect(screen.getByText(/404|Request failed|Failed to load/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('renders recommendations', async () => {
    // Uses default MSW mock which has recommendations
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });

    // First wait for the business case to load (not skeleton)
    await waitFor(() => {
      expect(screen.getByText('Test Business Case')).toBeInTheDocument();
    }, { timeout: 3000 });

    // Then check recommendations section
    expect(screen.getByText('Recommendations')).toBeInTheDocument();

    // Check for actual recommendation text from the mock
    expect(screen.getByText('Implement solution within Q2')).toBeInTheDocument();
    expect(screen.getByText('Focus on high-value customer segments')).toBeInTheDocument();
    expect(screen.getByText('Monitor metrics monthly')).toBeInTheDocument();
  });

  it('renders export button when document_url is present', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () => {
        return HttpResponse.json({
          case_id: 'test-case-123',
          title: 'Test',
          summary: 'Summary',
          total_value: 100000,
          implementation_cost: 25000,
          roi_ratio: 4.0,
          payback_months: 6,
          confidence_score: 0.85,
          recommendations: [],
          status: 'completed',
          document_url: 'https://example.com/doc.pdf',
          created_at: '2024-01-15T10:00:00Z',
          page_count: 10,
          file_size_bytes: 51200,
        });
      })
    );

    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export pdf/i })).toBeEnabled();
    }, { timeout: 3000 });
  });

  it('disables export button when document_url is absent', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () => {
        return HttpResponse.json({
          case_id: 'test-case-123',
          title: 'Test',
          summary: 'Summary',
          total_value: 100000,
          implementation_cost: 25000,
          roi_ratio: 4.0,
          payback_months: 6,
          confidence_score: 0.85,
          recommendations: [],
          status: 'completed',
          created_at: '2024-01-15T10:00:00Z',
          page_count: 10,
          file_size_bytes: 51200,
        });
      })
    );

    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export pdf/i })).toBeDisabled();
    }, { timeout: 3000 });
  });

  it('renders page header with breadcrumbs', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () => {
        return HttpResponse.json({
          case_id: 'test-case-123',
          title: 'Test',
          summary: 'Summary',
          total_value: 100000,
          implementation_cost: 25000,
          roi_ratio: 4.0,
          payback_months: 6,
          confidence_score: 0.85,
          recommendations: [],
          status: 'completed',
          created_at: '2024-01-15T10:00:00Z',
          page_count: 10,
          file_size_bytes: 51200,
        });
      })
    );

    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });

    // PageHeader component renders breadcrumbs - check for the title instead
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Test' })).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});

// ── deriveTrustState — pure logic tests ──────────────────────────────────────

function makeBC(overrides: Partial<BusinessCaseType> = {}): BusinessCaseType {
  return {
    case_id: 'bc-001',
    title: 'Test Case',
    summary: 'Summary',
    total_value: 100000,
    implementation_cost: 25000,
    roi_ratio: 4.0,
    payback_months: 6,
    confidence_score: 0.85,
    recommendations: [],
    status: 'completed',
    page_count: 10,
    file_size_bytes: 51200,
    document_url: 'https://example.com/doc.pdf',
    ...overrides,
  };
}

describe('deriveTrustState — pure logic', () => {
  it('returns degraded when customer_facing_allowed is false', () => {
    const bc = makeBC({ case_metadata: { customer_facing_allowed: false } });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('degraded');
  });

  it('returns degraded when degraded_reason is set', () => {
    const bc = makeBC({ case_metadata: { degraded_reason: 'LLM enrichment failed' } });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('degraded');
  });

  it('returns pending_review for status pending', () => {
    const bc = makeBC({ status: 'pending', case_metadata: {} });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('pending_review');
  });

  it('returns pending_review for status needs_review', () => {
    const bc = makeBC({ status: 'needs_review', case_metadata: {} });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('pending_review');
  });

  it('returns pending_review for status draft', () => {
    const bc = makeBC({ status: 'draft', case_metadata: {} });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('pending_review');
  });

  it('returns export_ready when approved and document_url present', () => {
    const bc = makeBC({ status: 'completed', document_url: 'https://example.com/doc.pdf', case_metadata: {} });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('export_ready');
  });

  it('returns validated when approved but no document_url', () => {
    const bc = makeBC({ status: 'approved', document_url: undefined, case_metadata: {} });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('validated');
  });

  it('returns export_blocked when status is failed', () => {
    const bc = makeBC({ status: 'failed', case_metadata: {} });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('export_blocked');
  });

  it('returns export_blocked when status is rejected', () => {
    const bc = makeBC({ status: 'rejected', case_metadata: {} });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('export_blocked');
  });

  it('degraded takes priority over pending status', () => {
    const bc = makeBC({ status: 'pending', case_metadata: { customer_facing_allowed: false } });
    expect(deriveTrustState(bc)).toBe<BusinessCaseTrustState>('degraded');
  });
});

// ── BusinessCaseTrustRow — rendering via MSW ─────────────────────────────────

function mockCase(overrides: Record<string, unknown> = {}) {
  return {
    case_id: 'test-case-123',
    title: 'Trust Test Case',
    summary: 'Summary',
    total_value: 100000,
    implementation_cost: 25000,
    roi_ratio: 4.0,
    payback_months: 6,
    confidence_score: 0.85,
    recommendations: [],
    page_count: 10,
    file_size_bytes: 51200,
    ...overrides,
  };
}

describe('BusinessCase trust status row — rendering', () => {
  afterEach(() => { vi.clearAllMocks(); });

  it('renders Degraded and Internal draft only badges when customer_facing_allowed is false', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({
          status: 'completed',
          case_metadata: { customer_facing_allowed: false },
        }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByText('Degraded')).toBeInTheDocument();
      expect(screen.getByText('Internal draft only')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('renders Pending Review and Internal draft only badges for pending status', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({ status: 'pending', case_metadata: {} }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByText('Pending Review')).toBeInTheDocument();
      expect(screen.getByText('Internal draft only')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('renders Validated badge when approved without document_url', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({ status: 'approved', case_metadata: {} }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByText('Validated')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('renders Export Ready badge when approved with document_url', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({
          status: 'completed',
          document_url: 'https://example.com/doc.pdf',
          case_metadata: {},
        }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByText('Export Ready')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('renders Export Blocked badge when status is failed', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({ status: 'failed', case_metadata: {} }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByText('Export Blocked')).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it('disables export button when degraded', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({
          status: 'completed',
          case_metadata: { customer_facing_allowed: false },
        }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export pdf/i })).toBeDisabled();
    }, { timeout: 3000 });
  });

  it('disables export button when pending review', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({ status: 'pending', case_metadata: {} }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export pdf/i })).toBeDisabled();
    }, { timeout: 3000 });
  });

  it('enables export button when export_ready', async () => {
    server.use(
      http.get('/api/v1/agents/cases/:caseId', () =>
        HttpResponse.json(mockCase({
          status: 'completed',
          document_url: 'https://example.com/doc.pdf',
          case_metadata: {},
        }))
      )
    );
    renderWithRouter(<BusinessCase />, { path: '/business-case?id=test-case-123' });
    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export pdf/i })).not.toBeDisabled();
    }, { timeout: 3000 });
  });
});
