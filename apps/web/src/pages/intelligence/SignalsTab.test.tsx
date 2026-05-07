import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { createWrapperWithRouterPath } from '@/test-utils';
import SignalsTab from './SignalsTab';

const mutate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return { ...(actual as object), useParams: () => ({ accountId: 'acc-123' }) };
});

vi.mock('@/hooks/useAccounts', () => ({
  useAccount: () => ({ data: { name: 'Acme', industry: 'Tech', annual_revenue: 1234 }, isLoading: false, error: null }),
}));

vi.mock('@/agui', () => ({
  useAgentEvents: () => ({ messages: [], sendMessage: vi.fn(), suggestedActions: [], steps: [], isStreaming: false, metadata: undefined }),
}));

vi.mock('@/hooks/useHypotheses', () => ({ usePromoteSignal: () => ({ isPending: false, isSuccess: false, mutateAsync: vi.fn() }) }));
vi.mock('@/hooks', () => ({ useNavigation: () => ({ navigateTo: vi.fn() }) }));

vi.mock('@/hooks/useWorkspaceCase', () => ({
  useCanonicalCaseId: () => ({ data: 'case-123', isLoading: false, error: null, refetch: vi.fn() }),
  useWorkspaceTabQuery: () => ({ data: { signals: [{ id: 's1', name: 'Signal 1', category: 'Cost', confidence: 80, impact: 'High' }] }, isLoading: false, error: null, refetch: vi.fn() }),
  usePersistWorkspaceTab: () => ({ mutate, persistState: 'failed' as const }),
  useGenerateWorkspaceIntelligence: () => ({ isPending: false, isError: false, mutate: vi.fn() }),
  useSignalReview: () => ({ isPending: false, mutateAsync: vi.fn() }),
}));

describe('SignalsTab persistence UX', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('surfaces failed persistence and allows retry', () => {
    const wrapper = createWrapperWithRouterPath('/intelligence/acc-123/signals');
    render(<SignalsTab />, { wrapper });

    expect(screen.getByText(/Could not persist this tab/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: /Retry save/i }));
    expect(mutate).toHaveBeenCalled();
  });
});
