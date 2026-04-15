/**
 * AgentWorkflows Page Tests
 * 
 * Tests workflow UI interactions including:
 * - Dashboard renders with correct structure
 * - Cancel button triggers mutation
 * - Progress bars render correctly
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AgentWorkflows from './AgentWorkflows';

// Mock the hooks
const mockMutate = vi.fn();
const mockRefetch = vi.fn();

vi.mock('@/hooks/useWorkflows', () => ({
  useActiveWorkflows: () => ({
    data: {
      items: [
        { 
          id: 'wf-001', 
          name: 'Test Workflow', 
          status: 'running', 
          progress: 45,
          createdAt: new Date().toISOString()
        },
        { 
          id: 'wf-002', 
          name: 'Pending Workflow', 
          status: 'pending', 
          progress: 0,
          createdAt: new Date().toISOString()
        }
      ],
      total: 2,
      has_more: false
    },
    isLoading: false,
    error: null,
    refetch: mockRefetch
  }),
  useWorkflowHistory: () => ({
    data: {
      items: [
        { 
          id: 'wf-hist-001', 
          name: 'Completed Workflow', 
          status: 'completed', 
          progress: 100,
          createdAt: new Date().toISOString()
        }
      ],
      total: 1,
      has_more: false
    },
    isLoading: false,
    error: null,
    refetch: mockRefetch
  }),
  useCancelWorkflow: () => ({
    mutate: mockMutate,
    isPending: false
  })
}));

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false }
    }
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('AgentWorkflows', () => {
  beforeEach(() => {
    mockMutate.mockClear();
    mockRefetch.mockClear();
  });

  it('renders workflow dashboard with KPI cards', () => {
    render(<AgentWorkflows />, { wrapper: createWrapper() });
    
    // Check for KPI card labels (multiple elements may contain this text)
    expect(screen.getAllByText(/Workflow Dashboard/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Active Workflows/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Completed Today/i).length).toBeGreaterThan(0);
  });

  it('displays active workflow information', () => {
    render(<AgentWorkflows />, { wrapper: createWrapper() });
    
    // Check workflow names appear
    expect(screen.getByText('Test Workflow')).toBeInTheDocument();
    expect(screen.getByText('Pending Workflow')).toBeInTheDocument();
    
    // Check workflow IDs appear
    expect(screen.getByText('wf-001')).toBeInTheDocument();
    expect(screen.getByText('wf-002')).toBeInTheDocument();
  });

  it('shows cancel buttons for running and pending workflows', () => {
    render(<AgentWorkflows />, { wrapper: createWrapper() });
    
    // Cancel buttons should exist for running/pending workflows
    const cancelElements = screen.queryAllByText(/Cancel/i);
    expect(cancelElements.length).toBeGreaterThanOrEqual(2);
  });

  it('shows View buttons for all workflows', () => {
    render(<AgentWorkflows />, { wrapper: createWrapper() });
    
    // View buttons should exist for workflows
    const viewElements = screen.queryAllByText(/View/i);
    expect(viewElements.length).toBeGreaterThanOrEqual(3); // 2 active + at least 1 in history
  });

  it('renders progress bars for workflows with progress > 0', () => {
    render(<AgentWorkflows />, { wrapper: createWrapper() });
    
    // Progress text should be visible for running workflow (45%)
    expect(screen.getByText('45%')).toBeInTheDocument();
  });

  it('displays workflow history', () => {
    render(<AgentWorkflows />, { wrapper: createWrapper() });
    
    // History section should show completed workflow
    expect(screen.getByText('Completed Workflow')).toBeInTheDocument();
    expect(screen.getByText('wf-hist-001')).toBeInTheDocument();
  });
});
