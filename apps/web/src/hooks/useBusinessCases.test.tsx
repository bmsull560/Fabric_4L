import { renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi, type Mock } from 'vitest';
import { apiGet } from '@/api/typedClient';
import { createMockResponse, createWrapper } from '../test-utils';
import { useBusinessCases } from './useBusinessCases';

vi.mock('@/api/typedClient', () => ({
  apiGet: vi.fn(),
  apiPost: vi.fn(),
}));

describe('useBusinessCases', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches business-case workflows with completed cases explicitly included', async () => {
    (apiGet as Mock).mockResolvedValueOnce(createMockResponse({
      items: [
        {
          workflow_id: 'case-e2e-approved-001',
          workflow_type: 'business_case',
          lifecycle_status: 'approved',
          company_name: 'Meridian Manufacturing',
          total_value: 1250000,
          confidence: 0.92,
        },
      ],
    }));

    const { result } = renderHook(() => useBusinessCases({ status: 'approved' }), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(apiGet).toHaveBeenCalledWith(
      'l4',
      '/workflows?type=business_case&status=approved&include_completed=true',
    );
    expect(result.current.data?.[0]).toMatchObject({
      id: 'case-e2e-approved-001',
      company: 'Meridian Manufacturing',
      status: 'approved',
    });
  });
});
