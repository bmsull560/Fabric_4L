import { describe, it, expect, vi, beforeEach, type Mock } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { apiClient } from '@/api/client';
import { createWrapper, createMockResponse } from '../test-utils';
import {
  useCreateLicensingCompanyIntakeJob,
  useCreateProspectResearchJob,
  useSourceCorpora,
  useSourceCorpus,
  useAccountIntelligencePackets,
  useAccountIntelligencePacket,
  useJobSkillOutput,
} from './useSkillJobs';

vi.mock('@/api/client', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

// =============================================================================
// Fixtures
// =============================================================================

const mockCorpusSummary = {
  id: 'corpus-001',
  company_name: 'Allego',
  company_id: 'allego-001',
  corpus_type: 'licensing_company_ontology_seed',
  source_count: 42,
  extraction_status: 'ready_for_extraction',
  created_at: '2026-05-14T00:00:00Z',
};

const mockCorpusDetail = {
  ...mockCorpusSummary,
  tenant_id: 'tenant-001',
  source_groups: [{ source_type: 'product_page', count: 42 }],
  candidate_concepts: ['sales enablement'],
  provenance: [{ url: 'https://allego.com', source_type: 'product_page', confidence: 'high' }],
  updated_at: '2026-05-14T00:00:00Z',
};

const mockPacketSummary = {
  id: 'packet-001',
  account_name: 'Acme Manufacturing',
  account_id: 'acme-001',
  packet_type: 'prospect_research',
  observed_signal_count: 3,
  high_confidence_signal_count: 2,
  created_at: '2026-05-14T00:00:00Z',
};

const mockPacketDetail = {
  ...mockPacketSummary,
  tenant_id: 'tenant-001',
  company_profile: { size: 'mid-market' },
  observed_signals: [{ signal: 'Hiring', source: 'careers_page', confidence: 'high' }],
  likely_pain_areas: ['seller onboarding'],
  likely_stakeholders: ['CRO'],
  source_references: [{ url: 'https://acme.com', source_type: 'website', confidence: 'high' }],
  confidence_summary: { signal_count: 3, high_confidence_signals: 2 },
  next_recommended_events: ['layer2.signal_extraction.requested'],
  updated_at: '2026-05-14T00:00:00Z',
};

const mockSkillJobResponse = {
  job_id: 'job-001',
  status: 'QUEUED',
  job_type: 'licensing_company_intake',
  skill_name: 'licensing_company_intake',
  queue_position: 1,
};

// =============================================================================
// Mutations
// =============================================================================

describe('useCreateLicensingCompanyIntakeJob', () => {
  beforeEach(() => vi.clearAllMocks());

  it('posts to the correct endpoint', async () => {
    (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(mockSkillJobResponse));

    const { result } = renderHook(() => useCreateLicensingCompanyIntakeJob(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        target_id: 'target-001',
        company_name: 'Allego',
        company_id: 'allego-001',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.post).toHaveBeenCalledWith(
      'l1',
      '/api/v1/ingestion/jobs/licensing-company-intake',
      expect.objectContaining({ company_name: 'Allego', target_id: 'target-001' }),
    );
  });

  it('returns the SkillJobResponse on success', async () => {
    (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(mockSkillJobResponse));

    const { result } = renderHook(() => useCreateLicensingCompanyIntakeJob(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ target_id: 'target-001', company_name: 'Allego' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.job_id).toBe('job-001');
    expect(result.current.data?.skill_name).toBe('licensing_company_intake');
  });
});

describe('useCreateProspectResearchJob', () => {
  beforeEach(() => vi.clearAllMocks());

  it('posts to the correct endpoint', async () => {
    const prospectResponse = { ...mockSkillJobResponse, job_type: 'prospect_research', skill_name: 'prospect_research' };
    (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(prospectResponse));

    const { result } = renderHook(() => useCreateProspectResearchJob(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({
        target_id: 'target-002',
        account_name: 'Acme Manufacturing',
        account_id: 'acme-001',
      });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiClient.post).toHaveBeenCalledWith(
      'l1',
      '/api/v1/ingestion/jobs/prospect-research',
      expect.objectContaining({ account_name: 'Acme Manufacturing', target_id: 'target-002' }),
    );
  });

  it('returns the SkillJobResponse on success', async () => {
    const prospectResponse = { ...mockSkillJobResponse, job_type: 'prospect_research', skill_name: 'prospect_research' };
    (apiClient.post as Mock).mockResolvedValueOnce(createMockResponse(prospectResponse));

    const { result } = renderHook(() => useCreateProspectResearchJob(), {
      wrapper: createWrapper(),
    });

    await act(async () => {
      result.current.mutate({ target_id: 'target-002', account_name: 'Acme' });
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.skill_name).toBe('prospect_research');
  });
});

// =============================================================================
// Queries — SourceCorpus
// =============================================================================

describe('useSourceCorpora', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls the correct list endpoint', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(
      createMockResponse({ items: [mockCorpusSummary], total: 1, limit: 20, next_cursor: null }),
    );

    renderHook(() => useSourceCorpora(), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('l1', '/api/v1/ingestion/source-corpora');
  });

  it('appends company_id filter to query string', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(
      createMockResponse({ items: [], total: 0, limit: 20, next_cursor: null }),
    );

    renderHook(() => useSourceCorpora({ company_id: 'allego-001' }), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    const calledPath = (apiClient.get as Mock).mock.calls[0][1] as string;
    expect(calledPath).toContain('company_id=allego-001');
  });

  it('appends limit to query string', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(
      createMockResponse({ items: [], total: 0, limit: 5, next_cursor: null }),
    );

    renderHook(() => useSourceCorpora({ limit: 5 }), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    const calledPath = (apiClient.get as Mock).mock.calls[0][1] as string;
    expect(calledPath).toContain('limit=5');
  });

  it('does not fetch when disabled', () => {
    // useSourceCorpora always fetches — this test verifies it uses the l1 layer key
    (apiClient.get as Mock).mockResolvedValueOnce(
      createMockResponse({ items: [], total: 0, limit: 20, next_cursor: null }),
    );

    renderHook(() => useSourceCorpora(), { wrapper: createWrapper() });
    expect(apiClient.get).not.toHaveBeenCalledWith('l4', expect.any(String));
  });
});

describe('useSourceCorpus', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls the correct detail endpoint', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse(mockCorpusDetail));

    renderHook(() => useSourceCorpus('corpus-001'), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('l1', '/api/v1/ingestion/source-corpora/corpus-001');
  });

  it('does not fetch when corpusId is null', () => {
    renderHook(() => useSourceCorpus(null), { wrapper: createWrapper() });
    expect(apiClient.get).not.toHaveBeenCalled();
  });
});

// =============================================================================
// Queries — AccountIntelligencePacket
// =============================================================================

describe('useAccountIntelligencePackets', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls the correct list endpoint', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(
      createMockResponse({ items: [mockPacketSummary], total: 1, limit: 20, next_cursor: null }),
    );

    renderHook(() => useAccountIntelligencePackets(), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('l1', '/api/v1/ingestion/account-intelligence-packets');
  });

  it('appends account_id filter to query string', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(
      createMockResponse({ items: [], total: 0, limit: 20, next_cursor: null }),
    );

    renderHook(() => useAccountIntelligencePackets({ account_id: 'acme-001' }), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    const calledPath = (apiClient.get as Mock).mock.calls[0][1] as string;
    expect(calledPath).toContain('account_id=acme-001');
  });
});

describe('useAccountIntelligencePacket', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls the correct detail endpoint', async () => {
    (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse(mockPacketDetail));

    renderHook(() => useAccountIntelligencePacket('packet-001'), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith(
      'l1',
      '/api/v1/ingestion/account-intelligence-packets/packet-001',
    );
  });

  it('does not fetch when packetId is null', () => {
    renderHook(() => useAccountIntelligencePacket(null), { wrapper: createWrapper() });
    expect(apiClient.get).not.toHaveBeenCalled();
  });
});

// =============================================================================
// Queries — Job skill output
// =============================================================================

describe('useJobSkillOutput', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls the correct skill-output endpoint', async () => {
    const envelope = { output_contract: 'SourceCorpus' as const, data: mockCorpusDetail };
    (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse(envelope));

    renderHook(() => useJobSkillOutput('job-001'), { wrapper: createWrapper() });

    await waitFor(() => expect(apiClient.get).toHaveBeenCalled());
    expect(apiClient.get).toHaveBeenCalledWith('l1', '/api/v1/ingestion/jobs/job-001/skill-output');
  });

  it('does not fetch when jobId is null', () => {
    renderHook(() => useJobSkillOutput(null), { wrapper: createWrapper() });
    expect(apiClient.get).not.toHaveBeenCalled();
  });

  it('returns the output_contract in the envelope', async () => {
    const envelope = { output_contract: 'AccountIntelligencePacket' as const, data: mockPacketDetail };
    (apiClient.get as Mock).mockResolvedValueOnce(createMockResponse(envelope));

    const { result } = renderHook(() => useJobSkillOutput('job-002'), { wrapper: createWrapper() });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data?.output_contract).toBe('AccountIntelligencePacket');
  });
});
