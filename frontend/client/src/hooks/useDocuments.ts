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
  case_id: string;
  title: string;
  summary: string;
  total_value: number;
  implementation_cost: number;
  roi_ratio: number;
  payback_months: number;
  confidence_score: number;
  recommendations: string[];
  status: string;
  created_at?: string;
  document_url?: string;
  page_count: number;
  file_size_bytes: number;
}

// Constants for document operations
const EXPORT_POLL_INTERVAL_MS = 2000;
const BUSINESS_CASE_STALE_TIME_MS = 5 * 60 * 1000;
const ALLOWED_SCHEMES = ['http:', 'https:', 'blob:', 'data:'];

// Layer 4 prefixes for analysis routes (business cases, ROI, whitespace)
const L4_ANALYSIS_PREFIX = '/analysis';

const DOCUMENT_KEYS = {
  all: ['documents'] as const,
  export: (id: string) => [...DOCUMENT_KEYS.all, 'export', id] as const,
  businessCase: (id: string) => [...DOCUMENT_KEYS.all, 'businessCase', id] as const,
};

/**
 * Generic document export request (L3).
 * For business case exports, use useBusinessCaseExport instead.
 */
export function useDocumentExport() {
  return useMutation({
    mutationFn: async (request: DocumentExportRequest) => {
      const response = await apiClient.post('l3', '/documents/export', request);
      return response.data as DocumentExportResponse;
    },
  });
}

/**
 * Export a business case PDF.
 * Uses L4 analysis export endpoint.
 */
export function useBusinessCaseExport() {
  return useMutation({
    mutationFn: async ({ caseId, format = 'pdf' }: { caseId: string; format?: string }) => {
      const response = await apiClient.get('l4', `${L4_ANALYSIS_PREFIX}/cases/${caseId}/export?format=${format}`);
      return response.data as { case_id: string; format: string; document_url?: string; download_ready: boolean };
    },
  });
}

/**
 * Fetch a business case by ID from Layer 4.
 * Cached for 5 minutes.
 */
export function useBusinessCase(businessCaseId: string | null) {
  return useQuery({
    queryKey: DOCUMENT_KEYS.businessCase(businessCaseId || ''),
    queryFn: async () => {
      if (!businessCaseId) throw new Error('No business case ID provided');
      const response = await apiClient.get('l4', `${L4_ANALYSIS_PREFIX}/cases/${businessCaseId}`);
      return response.data as BusinessCase;
    },
    enabled: !!businessCaseId,
    staleTime: BUSINESS_CASE_STALE_TIME_MS,
  });
}


/**
 * Trigger a file download with URL validation.
 * Validates URL scheme to prevent XSS via javascript: protocol.
 * @throws Error if URL is malformed or uses an unsupported protocol
 */
export function downloadExport(downloadUrl: string, filename: string) {
  // Validate URL scheme to prevent XSS via javascript: protocol
  let url: URL;
  try {
    url = new URL(downloadUrl, window.location.href);
  } catch {
    throw new Error('Invalid download URL: malformed URL');
  }

  if (!ALLOWED_SCHEMES.includes(url.protocol)) {
    throw new Error(`Invalid download URL: unsupported protocol "${url.protocol}"`);
  }

  // Store validated URL to prevent TOCTOU attacks
  const validatedHref = url.href;

  const link = document.createElement('a');
  link.href = validatedHref;
  link.download = filename;
  link.rel = 'noopener noreferrer'; // Security best practice
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
