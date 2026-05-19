import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Intelligence from './Intelligence';

vi.mock('../components/WorkflowLayout', () => ({
  WorkflowLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockSetEnrichedEntities = vi.fn();
const mockSetCurrentStep = vi.fn();

beforeEach(() => {
  mockSetEnrichedEntities.mockClear();
  mockSetCurrentStep.mockClear();
});

vi.mock('../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    prospect: { companyId: 'acct-001', companyName: 'Meridian Automotive' },
    setCurrentStep: mockSetCurrentStep,
    setEnrichedEntities: mockSetEnrichedEntities,
  }),
}));

vi.mock('@/hooks/useNavigation', () => ({
  useNavigation: () => ({ navigateTo: vi.fn() }),
}));

// Mock the hook directly to avoid api-client deduplication interference
const mockUseAccountBriefing = vi.fn();
vi.mock('@/hooks/useIntelligence', () => ({
  useAccountBriefing: (...args: unknown[]) => mockUseAccountBriefing(...args),
}));

const briefingData = {
  account_id: 'acct-001',
  account_name: 'Meridian Automotive',
  generated_at: '2026-05-01T00:00:00Z',
  enrichment: { sources_used: ['crm'] },
  signals: {
    total: 2,
    by_category: { operational: 2 },
    recent: [
      { id: 's1', text: 'Hiring freeze in Q2', category: 'operational', detected_at: '2026-04-01T00:00:00Z' },
      { id: 's2', text: 'Supply chain disruption', category: 'operational', detected_at: '2026-04-15T00:00:00Z' },
    ],
  },
  hypotheses: { total: 3, by_status: {}, top_hypotheses: [] },
  competitive: { competitors: [] },
  evidence: { matching_case_studies: 4 },
  roi: {},
};

function renderPage() {
  return render(
    <MemoryRouter>
      <Intelligence />
    </MemoryRouter>
  );
}

describe('Intelligence page — success state', () => {
  it('renders signal text from API response', () => {
    mockUseAccountBriefing.mockReturnValue({ data: briefingData, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Hiring freeze in Q2')).toBeInTheDocument();
    expect(screen.getByText('Supply chain disruption')).toBeInTheDocument();
  });

  it('renders the page heading', () => {
    mockUseAccountBriefing.mockReturnValue({ data: briefingData, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Prospect Intelligence')).toBeInTheDocument();
  });

  it('renders the continue button', () => {
    mockUseAccountBriefing.mockReturnValue({ data: briefingData, isLoading: false, error: null });
    renderPage();
    expect(screen.getByRole('button', { name: /Generate AI Value Model/i })).toBeInTheDocument();
  });

  it('clicking continue maps signals to enriched entities and calls setEnrichedEntities', async () => {
    const user = userEvent.setup();
    mockUseAccountBriefing.mockReturnValue({ data: briefingData, isLoading: false, error: null });
    renderPage();
    await user.click(screen.getByRole('button', { name: /Generate AI Value Model/i }));
    expect(mockSetEnrichedEntities).toHaveBeenCalledWith(
      expect.arrayContaining([
        expect.objectContaining({ id: 's1', name: 'Hiring freeze in Q2', type: 'pain_signal' }),
        expect.objectContaining({ id: 's2', name: 'Supply chain disruption', type: 'pain_signal' }),
      ])
    );
  });
});

describe('Intelligence page — loading state', () => {
  it('renders loading text while fetching', () => {
    mockUseAccountBriefing.mockReturnValue({ data: undefined, isLoading: true, error: null });
    renderPage();
    expect(screen.getByText(/Loading account briefing/i)).toBeInTheDocument();
  });
});

describe('Intelligence page — error state', () => {
  it('renders error message on API failure', () => {
    mockUseAccountBriefing.mockReturnValue({ data: undefined, isLoading: false, error: new Error('500') });
    renderPage();
    expect(screen.getByText(/Failed to load intelligence data/i)).toBeInTheDocument();
  });
});

describe('Intelligence page — empty state', () => {
  it('renders empty state when no signals are returned', () => {
    mockUseAccountBriefing.mockReturnValue({
      data: { ...briefingData, signals: { total: 0, by_category: {}, recent: [] } },
      isLoading: false,
      error: null,
    });
    renderPage();
    expect(screen.getByText(/No pain signals detected/i)).toBeInTheDocument();
  });
});
