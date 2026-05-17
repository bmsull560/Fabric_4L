import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import Evidence from './Evidence';

vi.mock('../components/WorkflowLayout', () => ({
  WorkflowLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockSetCurrentStep = vi.fn();
const mockSetEnrichedEntities = vi.fn();

vi.mock('../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    setCurrentStep: mockSetCurrentStep,
    setEnrichedEntities: mockSetEnrichedEntities,
  }),
}));

vi.mock('@/hooks/useNavigation', () => ({
  useNavigation: () => ({ navigateTo: vi.fn() }),
}));

// Mock the hook directly to avoid api-client deduplication interference
const mockUseCaseStudies = vi.fn();
vi.mock('@/hooks/useEvidence', () => ({
  useCaseStudies: (...args: unknown[]) => mockUseCaseStudies(...args),
}));

const caseStudiesData = {
  total: 2,
  case_studies: [
    { id: 'cs1', title: 'Automotive Cobot ROI Study', industry: 'Manufacturing', published_date: '2024-03-01' },
    { id: 'cs2', title: 'Quality Defect Reduction at Scale', industry: 'Automotive', published_date: '2023-11-15' },
  ],
};

function renderPage() {
  return render(
    <MemoryRouter>
      <Evidence />
    </MemoryRouter>
  );
}

describe('Evidence page — render', () => {
  it('renders the page heading', () => {
    mockUseCaseStudies.mockReturnValue({ data: caseStudiesData, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Evidence Match')).toBeInTheDocument();
  });

  it('renders the continue button', () => {
    mockUseCaseStudies.mockReturnValue({ data: undefined, isLoading: false, error: null });
    renderPage();
    expect(screen.getByRole('button', { name: /Value Calculator/i })).toBeInTheDocument();
  });

  it('renders the search input', () => {
    mockUseCaseStudies.mockReturnValue({ data: undefined, isLoading: false, error: null });
    renderPage();
    expect(screen.getByPlaceholderText(/Search evidence/i)).toBeInTheDocument();
  });

  it('passes search query to useCaseStudies when user types', async () => {
    const user = userEvent.setup();
    mockUseCaseStudies.mockReturnValue({ data: caseStudiesData, isLoading: false, error: null });
    renderPage();
    await user.type(screen.getByPlaceholderText(/Search evidence/i), 'cobot');
    expect(mockUseCaseStudies).toHaveBeenCalledWith(
      expect.objectContaining({ search: 'cobot' })
    );
  });
});

describe('Evidence page — success state', () => {
  it('renders case study titles from API response', () => {
    mockUseCaseStudies.mockReturnValue({ data: caseStudiesData, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Automotive Cobot ROI Study')).toBeInTheDocument();
    expect(screen.getByText('Quality Defect Reduction at Scale')).toBeInTheDocument();
  });

  it('renders industry labels for case studies', () => {
    mockUseCaseStudies.mockReturnValue({ data: caseStudiesData, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText('Manufacturing')).toBeInTheDocument();
    expect(screen.getByText('Automotive')).toBeInTheDocument();
  });
});

describe('Evidence page — loading state', () => {
  it('renders loading text while fetching', () => {
    mockUseCaseStudies.mockReturnValue({ data: undefined, isLoading: true, error: null });
    renderPage();
    expect(screen.getByText(/Loading evidence library/i)).toBeInTheDocument();
  });
});

describe('Evidence page — error state', () => {
  it('renders error message on API failure', () => {
    mockUseCaseStudies.mockReturnValue({ data: undefined, isLoading: false, error: new Error('500') });
    renderPage();
    expect(screen.getByText(/Failed to load evidence/i)).toBeInTheDocument();
  });
});

describe('Evidence page — empty state', () => {
  it('renders empty state when no case studies are returned', () => {
    mockUseCaseStudies.mockReturnValue({ data: { total: 0, case_studies: [] }, isLoading: false, error: null });
    renderPage();
    expect(screen.getByText(/No evidence found/i)).toBeInTheDocument();
  });
});

describe('Evidence page — optional step (continue always available)', () => {
  it('continue button is present even with no evidence loaded', () => {
    mockUseCaseStudies.mockReturnValue({ data: { total: 0, case_studies: [] }, isLoading: false, error: null });
    renderPage();
    expect(screen.getByRole('button', { name: /Value Calculator/i })).toBeInTheDocument();
  });

  it('clicking continue calls setCurrentStep', async () => {
    const user = userEvent.setup();
    mockUseCaseStudies.mockReturnValue({ data: { total: 0, case_studies: [] }, isLoading: false, error: null });
    renderPage();
    await user.click(screen.getByRole('button', { name: /Value Calculator/i }));
    expect(mockSetCurrentStep).toHaveBeenCalled();
  });
});
