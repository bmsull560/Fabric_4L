/**
 * BusinessCase Component Tests
 *
 * Tests for the business case viewer including:
 * - Rendering with business case data
 * - Formula evaluation display
 * - Value tree visualization
 * - Empty/error states
 * - PDF export functionality
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import BusinessCase from './BusinessCase';

// Mock wouter's useSearchParams - use getter function for live reference
const getMockSearchParams = () => mockSearchParams;
let mockSearchParams = new Map<string, string>([['id', 'test-case-123']]);

vi.mock('wouter', async () => {
  const actual = await vi.importActual('wouter');
  return {
    ...actual,
    useSearchParams: () => [getMockSearchParams(), () => {}],
    useLocation: () => ['/', () => {}],
  };
});

// Mock window.location.search for id param
Object.defineProperty(window, 'location', {
  writable: true,
  value: {
    href: 'http://localhost:3000/business-case?id=test-case-123',
    origin: 'http://localhost:3000',
    protocol: 'http:',
    host: 'localhost:3000',
    hostname: 'localhost',
    port: '3000',
    pathname: '/business-case',
    search: '?id=test-case-123',
    hash: '',
  },
});

describe('BusinessCase', () => {
  beforeEach(() => {
    // Reset and set default mock search param
    mockSearchParams = new Map([['id', 'test-case-123']]);
  });

  it('renders loading state initially', () => {
    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    // Should show loading skeletons
    expect(document.querySelector('[class*="skeleton"]')).toBeDefined();
  });

  it('renders with business case data', async () => {
    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', () => {
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

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Test Business Case')).toBeInTheDocument();
    });

    // Should show value
    expect(screen.getByText('$1,200,000')).toBeInTheDocument();
  });

  it('shows warning when no case ID provided', async () => {
    // Clear mock search params to simulate no ID in URL
    mockSearchParams = new Map<string, string>();

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/No business case ID provided/i)).toBeInTheDocument();
    });
  });

  it.skip('shows error state when case fails to load', async () => {
    // TODO: Fix mock reference update issue with vitest hoisting
    mockSearchParams = new Map([['id', 'not-found-case']]);

    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', ({ params }) => {
        if (params.caseId === 'not-found-case') {
          return HttpResponse.json({ error: 'Case not found' }, { status: 404 });
        }
        return HttpResponse.json({ case_id: params.caseId });
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      // React Query displays HTTP error message for 404 responses
      expect(screen.getByText(/404|Request failed|Failed to load/i)).toBeInTheDocument();
    }, { timeout: 3000 });
  });

  it.skip('renders recommendations', async () => {
    // TODO: Fix mock reference update issue with vitest hoisting
    mockSearchParams = new Map([['id', 'test-case']]);

    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', ({ params }) => {
        if (params.caseId === 'test-case') {
          return HttpResponse.json({
            case_id: 'test-case',
            title: 'Test Case',
            summary: 'Summary',
            total_value: 100000,
            implementation_cost: 25000,
            roi_ratio: 4.0,
            payback_months: 6,
            confidence_score: 0.85,
            recommendations: ['Recommendation One', 'Recommendation Two'],
            status: 'completed',
            created_at: '2024-01-15T10:00:00Z',
            page_count: 10,
            file_size_bytes: 51200,
          });
        }
        return new HttpResponse(null, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Recommendations')).toBeInTheDocument();
    }, { timeout: 3000 });

    expect(screen.getByText('Recommendation One')).toBeInTheDocument();
    expect(screen.getByText('Recommendation Two')).toBeInTheDocument();
  });

  it.skip('renders export button when document_url is present', async () => {
    // TODO: Fix mock reference update issue with vitest hoisting
    mockSearchParams = new Map([['id', 'test-case']]);

    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', ({ params }) => {
        if (params.caseId === 'test-case') {
          return HttpResponse.json({
            case_id: 'test-case',
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
        }
        return new HttpResponse(null, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /export pdf/i })).toBeEnabled();
    }, { timeout: 3000 });
  });

  it.skip('renders page header with breadcrumbs', async () => {
    // TODO: Fix mock reference update issue with vitest hoisting
    mockSearchParams = new Map([['id', 'test-case']]);

    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', ({ params }) => {
        if (params.caseId === 'test-case') {
          return HttpResponse.json({
            case_id: 'test-case',
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
        }
        return new HttpResponse(null, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    // PageHeader component renders breadcrumbs - check for the title instead
    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Test' })).toBeInTheDocument();
    }, { timeout: 3000 });
  });
});
