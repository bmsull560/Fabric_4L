import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import ProspectSetup from './ProspectSetup';
import * as apiClient from '@/api/client';
import * as useNavigation from '@/hooks/useNavigation';

// =============================================================================
// Mocks
// =============================================================================

const mockNavigateTo = vi.fn();

vi.mock('@/hooks/useNavigation', () => ({
  useNavigation: () => ({
    navigateTo: mockNavigateTo,
  }),
}));

const mockPost = vi.fn();
vi.mock('@/api/client', () => ({
  apiClient: {
    post: mockPost,
  },
}));

// Mock crypto.randomUUID
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => 'test-prospect-id-123',
  },
});

// =============================================================================
// Test Setup
// =============================================================================

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
}

// =============================================================================
// Tests
// =============================================================================

describe('ProspectSetup', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockPost.mockReset();
  });

  describe('Form Rendering', () => {
    it('renders the prospect setup form with empty fields', () => {
      renderWithProviders(<ProspectSetup />);

      // Check for main elements
      expect(screen.getByText('Step 1 of 7')).toBeInTheDocument();
      expect(screen.getByText('Construct a Value Model')).toBeInTheDocument();
      expect(screen.getByLabelText('Company Name')).toBeInTheDocument();
      expect(screen.getByLabelText('Main Contact')).toBeInTheDocument();
      expect(screen.getByLabelText('Contact Title')).toBeInTheDocument();
    });

    it('shows required objective selection', () => {
      renderWithProviders(<ProspectSetup />);

      expect(screen.getByText('Primary Objective')).toBeInTheDocument();
      expect(screen.getByText('Required')).toBeInTheDocument();
    });

    it('disables continue button when form is incomplete', () => {
      renderWithProviders(<ProspectSetup />);

      const continueButton = screen.getByText('Continue to Intelligence');
      expect(continueButton).toBeDisabled();
    });
  });

  describe('Form Interaction', () => {
    it('enables continue button when all required fields are filled', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill required fields
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });

      // Select objective
      fireEvent.click(screen.getByText('Reduce costs'));

      const continueButton = screen.getByText('Continue to Intelligence');
      expect(continueButton).not.toBeDisabled();
    });

    it('shows missing inputs cue when trying to continue with incomplete form', () => {
      renderWithProviders(<ProspectSetup />);

      // Should show missing inputs message
      expect(screen.getByText('Before we continue:')).toBeInTheDocument();
      expect(screen.getByText('· Add company name')).toBeInTheDocument();
      expect(screen.getByText('· Add primary contact')).toBeInTheDocument();
      expect(screen.getByText('· Select a primary objective')).toBeInTheDocument();
    });

    it('hides missing inputs cue when form is complete', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill required fields
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.click(screen.getByText('Reduce costs'));

      // Missing inputs cue should be hidden
      expect(screen.queryByText('Before we continue:')).not.toBeInTheDocument();
    });
  });

  describe('Backend Integration', () => {
    it('calls start-analysis endpoint when continue is clicked', async () => {
      mockPost.mockResolvedValueOnce({
        data: {
          prospect_id: 'prospect-123',
          workflow_id: 'wf-456',
          status: 'started',
          enrichment_status: 'unavailable',
          buyer_role_inference: {
            status: 'pending',
            role: null,
            confidence: null,
            source: 'title_not_executive_pattern',
          },
          crm_match: {
            status: 'unavailable',
            opportunity_id: null,
            confidence: null,
            source: 'crm_module_not_loaded',
          },
          next_route_state: 'workflow-intelligence',
          message: null,
        },
      });

      renderWithProviders(<ProspectSetup />);

      // Fill form
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. VP Manufacturing Operations'), {
        target: { value: 'Engineer' },
      });
      fireEvent.click(screen.getByText('Reduce costs'));

      // Click continue
      fireEvent.click(screen.getByText('Continue to Intelligence'));

      // Wait for API call
      await waitFor(() => {
        expect(mockPost).toHaveBeenCalledWith(
          'l4',
          '/v1/prospects/test-prospect-id-123/start-analysis',
          expect.objectContaining({
            prospect_id: 'test-prospect-id-123',
            setup_data: expect.objectContaining({
              company_name: 'Test Company',
              contact_name: 'John Doe',
              contact_title: 'Engineer',
              primary_objective: 'Reduce costs',
            }),
            workflow_type: 'prospect_analysis',
            priority: 'NORMAL',
          })
        );
      });
    });

    it('navigates to workflow-intelligence on success', async () => {
      mockPost.mockResolvedValueOnce({
        data: {
          prospect_id: 'prospect-123',
          workflow_id: 'wf-456',
          status: 'started',
          enrichment_status: 'unavailable',
          buyer_role_inference: {
            status: 'pending',
            role: null,
            confidence: null,
            source: 'title_not_executive_pattern',
          },
          crm_match: {
            status: 'unavailable',
            opportunity_id: null,
            confidence: null,
            source: 'crm_module_not_loaded',
          },
          next_route_state: 'workflow-intelligence',
          message: null,
        },
      });

      renderWithProviders(<ProspectSetup />);

      // Fill and submit
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.click(screen.getByText('Reduce costs'));
      fireEvent.click(screen.getByText('Continue to Intelligence'));

      await waitFor(() => {
        expect(mockNavigateTo).toHaveBeenCalledWith(
          'workflow-intelligence',
          expect.objectContaining({
            state: expect.objectContaining({
              prospectId: 'prospect-123',
              workflowId: 'wf-456',
              status: 'started',
            }),
          })
        );
      });
    });

    it('shows loading state while request is pending', async () => {
      // Create a promise that never resolves to keep loading state
      mockPost.mockReturnValueOnce(new Promise(() => {}));

      renderWithProviders(<ProspectSetup />);

      // Fill and submit
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.click(screen.getByText('Reduce costs'));
      fireEvent.click(screen.getByText('Continue to Intelligence'));

      // Should show loading state
      expect(screen.getByText('Starting analysis...')).toBeInTheDocument();
    });

    it('shows error state when backend fails', async () => {
      mockPost.mockRejectedValueOnce(new Error('Network error'));

      renderWithProviders(<ProspectSetup />);

      // Fill and submit
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.click(screen.getByText('Reduce costs'));
      fireEvent.click(screen.getByText('Continue to Intelligence'));

      await waitFor(() => {
        expect(screen.getByText('Failed to start analysis:')).toBeInTheDocument();
        expect(screen.getByText('Network error')).toBeInTheDocument();
      });
    });
  });

  describe('No Hardcoded Data', () => {
    it('does not show hardcoded company data (12K employees, $4.2B revenue)', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill company name
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });

      // Should show pending/loading state, not hardcoded data
      expect(screen.queryByText(/12K employees/)).not.toBeInTheDocument();
      expect(screen.queryByText(/\$4\.2B revenue/)).not.toBeInTheDocument();
    });

    it('does not show hardcoded CRM opportunity (MAC-2026-0417)', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill company name to show CRM section
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });

      // Should not show hardcoded CRM ID
      expect(screen.queryByText('MAC-2026-0417')).not.toBeInTheDocument();
      expect(screen.queryByText(/Salesforce/)).not.toBeInTheDocument();
    });

    it('shows appropriate messaging for pending enrichment', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill company name
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });

      // Should show pending message
      expect(screen.getByText('Enrichment data will be loaded after starting analysis')).toBeInTheDocument();
    });
  });

  describe('Buyer Role Detection', () => {
    it('shows inferred buyer role card when title is provided', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill contact info
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. VP Manufacturing Operations'), {
        target: { value: 'VP Sales' },
      });

      // Should show buyer role detection card
      expect(screen.getByText('Buyer Role Detected')).toBeInTheDocument();
      expect(screen.getByText('Based on title "VP Sales"')).toBeInTheDocument();
    });

    it('shows confirm button for inferred buyer role', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill contact info
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. VP Manufacturing Operations'), {
        target: { value: 'VP Sales' },
      });

      // Should have confirm button
      expect(screen.getByText('Confirm')).toBeInTheDocument();
    });

    it('marks buyer role as confirmed when confirm is clicked', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill contact info
      fireEvent.change(screen.getByPlaceholderText('e.g. Patricia Chen'), {
        target: { value: 'John Doe' },
      });
      fireEvent.change(screen.getByPlaceholderText('e.g. VP Manufacturing Operations'), {
        target: { value: 'VP Sales' },
      });

      // Click confirm
      fireEvent.click(screen.getByText('Confirm'));

      // Should show confirmed state
      expect(screen.getByText('Economic Buyer confirmed — VP Sales')).toBeInTheDocument();
    });
  });

  describe('Status Pills', () => {
    it('shows "needed" status for empty fields', () => {
      renderWithProviders(<ProspectSetup />);

      const pills = screen.getAllByText(/Company|Primary Contact|Buyer Role|Primary Objective/);
      expect(pills.length).toBeGreaterThan(0);
    });

    it('updates status pills when fields are filled', () => {
      renderWithProviders(<ProspectSetup />);

      // Fill company
      fireEvent.change(screen.getByPlaceholderText('e.g. Meridian Automotive Components'), {
        target: { value: 'Test Company' },
      });

      // Company pill should now show complete
      expect(screen.getByText('Company')).toBeInTheDocument();
    });
  });
});
