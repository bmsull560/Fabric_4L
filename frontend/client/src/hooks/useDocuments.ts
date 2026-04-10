import { useMutation, useQuery } from '@tanstack/react-query';
import { apiClient } from '@/api/client';

export interface DocumentExportRequest {
  document_type: 'business_case' | 'audit_report';
  business_case_id: string;
  format: 'pdf' | 'html';
  include_provenance: boolean;
}

export interface DocumentExportResponse {
  export_id: string;
  status: 'pending' | 'completed' | 'failed';
  download_url?: string;
  format: string;
  expires_at?: string;
}

export interface BusinessCase {
  id: string;
  title: string;
  organization: string;
  total_value: string;
  avg_confidence: number;
  use_case_count: number;
  persona_count: number;
  driver_count: number;
  avg_payback: string;
  generator: string;
  created_at: string;
  use_cases: UseCase[];
  executive_summary: string;
  methodology?: string;
}

export interface UseCase {
  id: string;
  name: string;
  persona: string;
  driver: string;
  roi: string;
  payback: string;
  confidence: number;
  description?: string;
}

const DOCUMENT_KEYS = {
  all: ['documents'] as const,
  export: (id: string) => [...DOCUMENT_KEYS.all, 'export', id] as const,
  businessCase: (id: string) => [...DOCUMENT_KEYS.all, 'businessCase', id] as const,
};

export function useDocumentExport() {
  return useMutation({
    mutationFn: async (request: DocumentExportRequest) => {
      const response = await apiClient.post('l3', '/documents/export', request);
      return response.data as DocumentExportResponse;
    },
  });
}

export function useExportStatus(exportId: string | null) {
  return useQuery({
    queryKey: DOCUMENT_KEYS.export(exportId || ''),
    queryFn: async (): Promise<DocumentExportResponse> => {
      if (!exportId) throw new Error('No export ID provided');
      // Poll for export status - in production this would be a real endpoint
      const response = await apiClient.get('l3', `/documents/export/${exportId}/status`);
      return response.data as DocumentExportResponse;
    },
    enabled: !!exportId,
    refetchInterval: (query) => {
      // Stop polling when completed or failed
      const data = query.state.data;
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });
}

export function useBusinessCase(businessCaseId: string | null) {
  return useQuery({
    queryKey: DOCUMENT_KEYS.businessCase(businessCaseId || ''),
    queryFn: async () => {
      if (!businessCaseId) throw new Error('No business case ID provided');
      // In production this would fetch from the backend
      // For now, return mock data structure
      const response = await apiClient.get('l4', `/business-cases/${businessCaseId}`);
      return response.data as BusinessCase;
    },
    enabled: !!businessCaseId,
    staleTime: 5 * 60 * 1000,
  });
}

export function downloadExport(downloadUrl: string, filename: string) {
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
