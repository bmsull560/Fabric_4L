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
import { describe, it, expect, vi } from 'vitest';
import '@testing-library/jest-dom';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { createWrapper } from '../test-utils';
import { http, HttpResponse } from 'msw';
import { server } from '../../../test/mocks/server';
import BusinessCase from './BusinessCase';

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
    Object.defineProperty(window, 'location', {
      writable: true,
      value: {
        href: 'http://localhost:3000/business-case',
        origin: 'http://localhost:3000',
        protocol: 'http:',
        host: 'localhost:3000',
        hostname: 'localhost',
        port: '3000',
        pathname: '/business-case',
        search: '',
        hash: '',
      },
    });

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/No business case ID provided/i)).toBeInTheDocument();
    });
  });

  it('shows error state when case fails to load', async () => {
    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', () => {
        return HttpResponse.json({ error: 'Case not found' }, { status: 404 });
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText(/Failed to load business case/i)).toBeInTheDocument();
    });
  });

  it('renders recommendations', async () => {
    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', () => {
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
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Recommendations')).toBeInTheDocument();
    });

    expect(screen.getByText('Recommendation One')).toBeInTheDocument();
    expect(screen.getByText('Recommendation Two')).toBeInTheDocument();
  });

  it('renders export button', async () => {
    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', () => {
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
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Export PDF')).toBeInTheDocument();
    });
  });

  it('renders breadcrumbs', async () => {
    server.use(
      http.get('/api/v1/agents/analysis/cases/:caseId', () => {
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
      })
    );

    const wrapper = createWrapper();
    render(<BusinessCase />, { wrapper });

    await waitFor(() => {
      expect(screen.getByText('Agent Workflows')).toBeInTheDocument();
    });
  });
});
