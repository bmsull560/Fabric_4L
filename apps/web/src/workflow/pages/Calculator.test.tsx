import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import Calculator from './Calculator';

// Mutable state for the store mock — changed per describe block via beforeEach
const mockStoreState = {
  setCurrentStep: vi.fn(),
  setGeneratedCaseId: vi.fn(),
  prospect: null as null | {
    companyId: string;
    companyName: string;
    contactName: string;
    contactTitle: string;
    industry?: string;
    employees?: number;
  },
};

vi.mock('../store/workflowStore', () => ({
  useWorkflowStore: () => mockStoreState,
}));

vi.mock('../components/WorkflowLayout', () => ({
  WorkflowLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

// Stub ValueLeversCalculator to isolate Calculator page logic
vi.mock('@/components/calculator/ValueLeversCalculator', () => ({
  ValueLeversCalculator: ({
    accountId,
    industry,
    companySize,
    onSaved,
  }: {
    accountId: string;
    industry?: string;
    companySize?: string;
    onSaved?: (valueCase: { case_id: string }) => void;
  }) => (
    <div data-testid="value-levers-calculator">
      <span data-testid="account-id">{accountId}</span>
      {industry && <span data-testid="industry">{industry}</span>}
      {companySize && <span data-testid="company-size">{companySize}</span>}
      <button
        onClick={() => onSaved?.({ case_id: 'VC-test-001' })}
        data-testid="save-button"
      >
        Save Value Case
      </button>
    </div>
  ),
}));

vi.mock('@/hooks/useNavigation', () => ({
  useNavigation: () => ({ navigateTo: vi.fn() }),
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <Calculator />
    </MemoryRouter>
  );
}

describe('Calculator page — without prospect', () => {
  beforeEach(() => {
    mockStoreState.prospect = null;
    mockStoreState.setCurrentStep = vi.fn();
    mockStoreState.setGeneratedCaseId = vi.fn();
  });

  it('renders the page heading', () => {
    renderPage();
    expect(screen.getByText('Value Calculator')).toBeInTheDocument();
  });

  it('renders the ValueLeversCalculator component', () => {
    renderPage();
    expect(screen.getByTestId('value-levers-calculator')).toBeInTheDocument();
  });

  it('passes empty accountId when prospect is null', () => {
    renderPage();
    expect(screen.getByTestId('account-id').textContent).toBe('');
  });
});

describe('Calculator page — with prospect', () => {
  beforeEach(() => {
    mockStoreState.prospect = {
      companyId: 'acct-001',
      companyName: 'Meridian Automotive',
      contactName: 'Alice',
      contactTitle: 'VP Ops',
      industry: 'Manufacturing',
      employees: 8000,
    };
    mockStoreState.setCurrentStep = vi.fn();
    mockStoreState.setGeneratedCaseId = vi.fn();
  });

  it('passes accountId from prospect to ValueLeversCalculator', () => {
    renderPage();
    expect(screen.getByTestId('account-id').textContent).toBe('acct-001');
  });

  it('passes industry from prospect to ValueLeversCalculator', () => {
    renderPage();
    expect(screen.getByTestId('industry').textContent).toBe('Manufacturing');
  });

  it('passes Enterprise companySize for employees > 5000', () => {
    renderPage();
    expect(screen.getByTestId('company-size').textContent).toBe('Enterprise');
  });
});

describe('Calculator page — onSaved callback', () => {
  beforeEach(() => {
    mockStoreState.prospect = {
      companyId: 'acct-001',
      companyName: 'Meridian Automotive',
      contactName: 'Alice',
      contactTitle: 'VP Ops',
      industry: 'Manufacturing',
      employees: 8000,
    };
    mockStoreState.setCurrentStep = vi.fn();
    mockStoreState.setGeneratedCaseId = vi.fn();
  });

  it('calls setGeneratedCaseId with the saved case_id', () => {
    renderPage();
    screen.getByTestId('save-button').click();
    expect(mockStoreState.setGeneratedCaseId).toHaveBeenCalledWith('VC-test-001');
  });

  it('calls setCurrentStep after save', () => {
    renderPage();
    screen.getByTestId('save-button').click();
    expect(mockStoreState.setCurrentStep).toHaveBeenCalled();
  });
});
