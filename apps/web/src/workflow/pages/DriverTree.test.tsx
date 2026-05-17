import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import DriverTree from './DriverTree';

vi.mock('../components/WorkflowLayout', () => ({
  WorkflowLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

const mockSetCurrentStep = vi.fn();
const mockSetSelectedTreeId = vi.fn();

beforeEach(() => {
  mockSetCurrentStep.mockClear();
  mockSetSelectedTreeId.mockClear();
});

vi.mock('../store/workflowStore', () => ({
  useWorkflowStore: () => ({
    setCurrentStep: mockSetCurrentStep,
    setSelectedTreeId: mockSetSelectedTreeId,
  }),
}));

vi.mock('@/hooks/useNavigation', () => ({
  useNavigation: () => ({ navigateTo: vi.fn() }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <DriverTree />
    </MemoryRouter>
  );
}

describe('DriverTree page — render', () => {
  it('renders the page heading', () => {
    renderPage();
    expect(screen.getByText('Value Driver Tree')).toBeInTheDocument();
  });

  it('renders the root goal node', () => {
    renderPage();
    expect(screen.getByText('Total Annual Value Impact')).toBeInTheDocument();
  });

  it('renders top-level driver nodes', () => {
    renderPage();
    expect(screen.getByText('Labor Cost Reduction')).toBeInTheDocument();
    expect(screen.getByText('Quality Improvement')).toBeInTheDocument();
    expect(screen.getByText('Throughput Gain')).toBeInTheDocument();
    expect(screen.getByText('Safety / Ergonomics')).toBeInTheDocument();
    expect(screen.getByText('Mixed-Model Flexibility')).toBeInTheDocument();
  });

  it('renders the total value label', () => {
    renderPage();
    expect(screen.getByText('$14.87M')).toBeInTheDocument();
  });

  it('renders the validation banner', () => {
    renderPage();
    expect(screen.getByText(/Tree validated/i)).toBeInTheDocument();
  });

  it('renders the continue button', () => {
    renderPage();
    expect(screen.getByRole('button', { name: /Match Evidence/i })).toBeInTheDocument();
  });
});

describe('DriverTree page — tree interaction', () => {
  it('renders leaf nodes when a driver is expanded', () => {
    renderPage();
    // Labor Cost Reduction is expanded by default — its children should be visible
    // Text may appear in multiple elements (tree node + detail panel), use getAllByText
    expect(screen.getAllByText('Avoided New Hires (85 positions)').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Overtime Elimination').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Reduced Turnover Cost').length).toBeGreaterThan(0);
  });

  it('collapses a driver node when its toggle is clicked', async () => {
    const user = userEvent.setup();
    renderPage();

    // Root node is expanded by default — collapse it via its aria-label
    await user.click(screen.getByRole('button', { name: /Collapse Total Annual Value Impact/i }));

    // After collapsing root, driver nodes should no longer be visible
    expect(screen.queryByText('Labor Cost Reduction')).not.toBeInTheDocument();
  });
});

describe('DriverTree page — right panel', () => {
  it('renders the Formula Inspector panel by default', () => {
    renderPage();
    expect(screen.getByText('Formula Inspector')).toBeInTheDocument();
  });

  it('switches to Validate panel when Validate tab is clicked', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /Validate/i }));
    expect(screen.getByText('Driver Validation')).toBeInTheDocument();
  });

  it('renders validation checks in the Validate panel', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /Validate/i }));
    expect(screen.getByText('Platform-controllable')).toBeInTheDocument();
    expect(screen.getByText('Formula completeness')).toBeInTheDocument();
    expect(screen.getByText('Evidence coverage')).toBeInTheDocument();
    expect(screen.getByText('Math consistency')).toBeInTheDocument();
  });
});

describe('DriverTree page — navigation', () => {
  it('clicking Match Evidence calls setSelectedTreeId with the root tree id', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /Match Evidence/i }));
    expect(mockSetSelectedTreeId).toHaveBeenCalledWith('root');
  });

  it('clicking Match Evidence calls setCurrentStep', async () => {
    const user = userEvent.setup();
    renderPage();

    await user.click(screen.getByRole('button', { name: /Match Evidence/i }));
    expect(mockSetCurrentStep).toHaveBeenCalled();
  });
});
