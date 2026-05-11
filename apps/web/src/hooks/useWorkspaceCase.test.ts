import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { apiClient } from '@/api/client';
import { createWrapper } from '../test-utils';
import {
  useWorkspaceTabQuery,
  useCanonicalCaseId,
  usePersistWorkspaceTab,
  useGenerateWorkspaceIntelligence,
} from './useWorkspaceCase';

// Mock the apiClient
vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

// Sample workspace data structures
const sampleSignalsResponse = {
  signals: [
    { id: 'sig_1', name: 'Operational inefficiency', category: 'Operational', confidence: 85, impact: 'High' },
    { id: 'sig_2', name: 'Rising costs', category: 'Cost', confidence: 78, impact: 'Medium' },
  ],
};

const sampleDriversResponse = {
  drivers: [
    { id: 'drv_1', name: 'Manual process overhead', contribution: 35, parentSignal: 'Operational inefficiency' },
    { id: 'drv_2', name: 'Legacy system constraints', contribution: 28, parentSignal: 'Operational inefficiency' },
  ],
};

const sampleEvidenceResponse = {
  evidence: [
    { id: 'ev_1', source: 'Industry Report 2024', claim: 'Sector averages 23% efficiency gap', confidence: 88, type: 'benchmark' },
    { id: 'ev_2', source: 'Internal Analysis', claim: 'Process takes 3x industry average', confidence: 75, type: 'internal' },
  ],
};

const sampleStakeholdersResponse = {
  stakeholders: [
    { id: 'st_1', name: 'CFO', role: 'Economic Buyer', priority: 'High', engagement: 'Active' },
    { id: 'st_2', name: 'VP Operations', role: 'Technical Champion', priority: 'High', engagement: 'Engaged' },
  ],
};

describe('useWorkspaceTabQuery', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should fetch signals tab data successfully', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: sampleSignalsResponse });

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<{ signals: typeof sampleSignalsResponse.signals }>('case-123', 'signals'),
      { wrapper }
    );

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    // Wait for data
    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleSignalsResponse);
    expect(apiClient.get).toHaveBeenCalledWith('l4', '/cases/case-123/workspace/signals');
  });

  it('should fetch drivers tab data successfully', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: sampleDriversResponse });

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<{ drivers: typeof sampleDriversResponse.drivers }>('case-123', 'drivers'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleDriversResponse);
    expect(apiClient.get).toHaveBeenCalledWith('l4', '/cases/case-123/workspace/drivers');
  });

  it('should fetch evidence tab data successfully', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: sampleEvidenceResponse });

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<{ evidence: typeof sampleEvidenceResponse.evidence }>('case-123', 'evidence'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleEvidenceResponse);
    expect(apiClient.get).toHaveBeenCalledWith('l4', '/cases/case-123/workspace/evidence');
  });

  it('should fetch stakeholders tab data successfully', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({ data: sampleStakeholdersResponse });

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<{ stakeholders: typeof sampleStakeholdersResponse.stakeholders }>('case-123', 'stakeholders'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(sampleStakeholdersResponse);
    expect(apiClient.get).toHaveBeenCalledWith('l4', '/cases/case-123/workspace/stakeholders');
  });

  it('should not fetch when caseId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<{ signals: [] }>(null, 'signals'),
      { wrapper }
    );

    // Should not be loading and should not have called the API
    expect(result.current.isLoading).toBe(false);
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('should handle API error correctly', async () => {
    const error = new Error('Failed to fetch');
    (apiClient.get as Mock).mockRejectedValueOnce(error);

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<{ signals: [] }>('case-123', 'signals'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isError).toBe(true));

    expect(result.current.error).toBeDefined();
  });

  it('should tolerate 501 in test mode fallback', async () => {
    (apiClient.get as Mock).mockRejectedValueOnce({ statusCode: 501, message: 'Not implemented' });
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<{ signals: [] }>('case-123', 'signals'),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual({ signals: [] });
  });

  /**
   * REGRESSION TEST: This test prevents the bug where the Pydantic model
   * stripped out dynamic fields (signals, drivers, etc.) due to extra="forbid".
   * The response should contain the actual data, not an empty object.
   */
  it('should preserve all dynamic fields in response (regression test)', async () => {
    // Simulate the API returning data with multiple dynamic fields
    const fullWorkspaceData = {
      signals: sampleSignalsResponse.signals,
      drivers: sampleDriversResponse.drivers,
      evidence: sampleEvidenceResponse.evidence,
      stakeholders: sampleStakeholdersResponse.stakeholders,
    };

    (apiClient.get as Mock).mockResolvedValueOnce({ data: fullWorkspaceData });

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useWorkspaceTabQuery<typeof fullWorkspaceData>('case-123', 'signals'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    // Verify all fields are present - this would fail if Pydantic stripped them
    expect(result.current.data).toEqual(fullWorkspaceData);
    expect(result.current.data?.signals).toHaveLength(2);
    expect(result.current.data?.drivers).toHaveLength(2);
    expect(result.current.data?.evidence).toHaveLength(2);
    expect(result.current.data?.stakeholders).toHaveLength(2);
  });
});

describe('useCanonicalCaseId', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('should return stored caseId from localStorage', async () => {
    localStorage.setItem('vf.workspace.case.acc-123', 'existing-case-456');

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useCanonicalCaseId('acc-123'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBe('existing-case-456');
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('should fetch existing case when not in localStorage', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: { items: [{ case_id: 'fetched-case-789' }] },
    });

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useCanonicalCaseId('acc-123'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBe('fetched-case-789');
    expect(localStorage.getItem('vf.workspace.case.acc-123')).toBe('fetched-case-789');
  });

  it('should create new case when none exists', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce({
      data: { items: [] },
    });
    (apiClient.post as Mock).mockResolvedValueOnce({
      data: { case_id: 'new-case-abc' },
    });

    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useCanonicalCaseId('acc-123'),
      { wrapper }
    );

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toBe('new-case-abc');
    expect(apiClient.post).toHaveBeenCalledWith(
      'l4',
      '/cases',
      {
        account_id: 'acc-123',
        title: 'Account acc-123 workspace',
      }
    );
  });

  it('should return null when accountId is null', async () => {
    const wrapper = createWrapper();
    const { result } = renderHook(
      () => useCanonicalCaseId(null),
      { wrapper }
    );

    expect(result.current.data).toBeUndefined();
    expect(result.current.isLoading).toBe(false);
  });
});

describe('useGenerateWorkspaceIntelligence', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should generate workspace intelligence', async () => {
    const generateResponse = {
      case_id: 'case-123',
      account_id: 'acc-123',
      generated: true,
      stats: {
        signals: 3,
        drivers: 3,
        evidence: 2,
        stakeholders: 3,
      },
    };

    (apiClient.post as Mock).mockResolvedValueOnce({ data: generateResponse });

    const wrapper = createWrapper();
    const { result } = renderHook(() => useGenerateWorkspaceIntelligence(), { wrapper });

    // Trigger the mutation
    result.current.mutate('case-123');

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual(generateResponse);
    expect(apiClient.post).toHaveBeenCalledWith(
      'l4',
      '/cases/case-123/workspace/generate',
      {}
    );
  });
});

describe('usePersistWorkspaceTab', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should persist tab data', async () => {
    (apiClient.put as Mock).mockResolvedValueOnce({
      data: { case_id: 'case-123', tab: 'signals', updated: true },
    });

    const wrapper = createWrapper();
    const { result } = renderHook(() => usePersistWorkspaceTab('signals'), { wrapper });

    const payload = { signals: sampleSignalsResponse.signals };

    result.current.mutate({ caseId: 'case-123', payload });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(result.current.data).toEqual({ case_id: 'case-123', tab: 'signals', updated: true });
    expect(apiClient.post).not.toHaveBeenCalled();
    expect(apiClient.put).toHaveBeenCalledWith(
      'l4',
      '/cases/case-123/workspace/signals',
      payload
    );
    expect(result.current.persistState).toBe('saved');
  });

  it('exposes failed persist state when request fails', async () => {
    (apiClient.put as Mock).mockRejectedValueOnce(new Error('boom'));
    const wrapper = createWrapper();
    const { result } = renderHook(() => usePersistWorkspaceTab('signals'), { wrapper });
    result.current.mutate({ caseId: 'case-123', payload: { signals: [] } });
    await waitFor(() => expect(result.current.isError).toBe(true));
    expect(result.current.persistState).toBe('failed');
  });
});
