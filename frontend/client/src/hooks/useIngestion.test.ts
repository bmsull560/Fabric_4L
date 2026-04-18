import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { createWrapper, createMockResponse } from "../test-utils";
import {
  useIngestionJobList,
  useIngestionJobDetail,
  useJobComplianceLogs,
  useCancelJob,
  useRetryJob,
} from "./useIngestion";
import { apiClient } from "@/api/client";

// Mock the API client
vi.mock("@/api/client", () => ({
  apiClient: {
    get: vi.fn(),
    delete: vi.fn(),
    post: vi.fn(),
  },
}));

describe("useIngestion", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("useIngestionJobList", () => {
    it("fetches jobs with pagination", async () => {
      const mockResponse = {
        data: [
          {
            id: "job-1",
            status: "COMPLETED",
            created_at: "2024-04-01T10:00:00Z",
            progress_percent_complete: 100,
            progress_processed_pages: 50,
            configuration: { url: "https://example.com" },
          },
        ],
        pagination: { page: 1, limit: 20, total: 1, totalPages: 1 },
        aggregation: {
          by_status: { COMPLETED: 1 },
          total_execution_time_ms: 5000,
          total_records_extracted: 100,
        },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockResponse));

      const { result } = renderHook(() => useIngestionJobList({ page: 1, limit: 20 }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.jobs).toHaveLength(1);
      expect(result.current.data?.jobs[0].id).toBe("job-1");
      expect(result.current.data?.jobs[0].status).toBe("completed");
      expect(result.current.data?.pagination.total).toBe(1);
    });

    it("applies status filter correctly", async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse({
        data: [],
        pagination: { page: 1, limit: 20, total: 0, totalPages: 0 },
        aggregation: { by_status: {}, total_execution_time_ms: 0, total_records_extracted: 0 },
      }));

      renderHook(() => useIngestionJobList({ status: ["PENDING", "QUEUED"] }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledWith("l1", expect.stringContaining("status=PENDING"));
      });
    });

    it("applies date range filter correctly", async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse({
        data: [],
        pagination: { page: 1, limit: 20, total: 0, totalPages: 0 },
        aggregation: { by_status: {}, total_execution_time_ms: 0, total_records_extracted: 0 },
      }));

      renderHook(() => useIngestionJobList({ dateFrom: "2024-04-01", dateTo: "2024-04-30" }), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(apiClient.get).toHaveBeenCalledWith("l1", expect.stringContaining("date_from=2024-04-01"));
        expect(apiClient.get).toHaveBeenCalledWith("l1", expect.stringContaining("date_to=2024-04-30"));
      });
    });

    it("handles empty response", async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse({
        data: [],
        pagination: { page: 1, limit: 20, total: 0, totalPages: 0 },
        aggregation: { by_status: {}, total_execution_time_ms: 0, total_records_extracted: 0 },
      }));

      const { result } = renderHook(() => useIngestionJobList(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data?.jobs).toHaveLength(0);
      expect(result.current.data?.pagination.total).toBe(0);
    });

    it("maps backend status to frontend status correctly", async () => {
      const mockResponse = {
        data: [
          { id: "1", status: "PENDING", created_at: "2024-04-01T10:00:00Z", progress_percent_complete: 0, configuration: {} },
          { id: "2", status: "QUEUED", created_at: "2024-04-01T10:00:00Z", progress_percent_complete: 0, configuration: {} },
          { id: "3", status: "EXTRACTING", created_at: "2024-04-01T10:00:00Z", progress_percent_complete: 50, configuration: {} },
          { id: "4", status: "COMPLETED", created_at: "2024-04-01T10:00:00Z", progress_percent_complete: 100, configuration: {} },
          { id: "5", status: "FAILED", created_at: "2024-04-01T10:00:00Z", progress_percent_complete: 0, configuration: {} },
          { id: "6", status: "CANCELLED", created_at: "2024-04-01T10:00:00Z", progress_percent_complete: 0, configuration: {} },
          { id: "7", status: "PARTIAL_SUCCESS", created_at: "2024-04-01T10:00:00Z", progress_percent_complete: 80, configuration: {} },
        ],
        pagination: { page: 1, limit: 20, total: 7, totalPages: 1 },
        aggregation: { by_status: {}, total_execution_time_ms: 0, total_records_extracted: 0 },
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockResponse));

      const { result } = renderHook(() => useIngestionJobList(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const jobs = result.current.data?.jobs ?? [];
      expect(jobs[0].status).toBe("pending");   // PENDING
      expect(jobs[1].status).toBe("pending");   // QUEUED
      expect(jobs[2].status).toBe("processing"); // EXTRACTING
      expect(jobs[3].status).toBe("completed");  // COMPLETED
      expect(jobs[4].status).toBe("failed");     // FAILED
      expect(jobs[5].status).toBe("failed");     // CANCELLED
      expect(jobs[6].status).toBe("completed");  // PARTIAL_SUCCESS
    });

    it("handles API error", async () => {
      vi.mocked(apiClient.get).mockRejectedValueOnce(new Error("Network error"));

      const { result } = renderHook(() => useIngestionJobList(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error?.message).toBe("Network error");
    });
  });

  describe("useIngestionJobDetail", () => {
    it("fetches job detail when jobId provided", async () => {
      const mockDetail = {
        id: "job-1",
        target_id: "target-1",
        organization_id: "org-1",
        configuration: { url: "https://example.com" },
        status: "COMPLETED",
        priority: 5,
        created_at: "2024-04-01T10:00:00Z",
        updated_at: "2024-04-01T10:05:00Z",
        triggered_by: "manual",
        created_by: "user-1",
        progress: {
          total_pages: 100,
          processed_pages: 100,
          failed_pages: 0,
          current_stage: "STORING",
          percent_complete: 100,
        },
        results: {
          raw_content_count: 100,
          extracted_record_count: 95,
          storage_bytes_used: 1024000,
          output_location: "s3://bucket/job-1",
        },
        resources: {
          browser_sessions_used: 2,
          proxy_requests_made: 100,
          llm_tokens_consumed: 5000,
          compute_time_ms: 300000,
        },
        stages: [
          { stage: "VALIDATING", status: "COMPLETED", started_at: "2024-04-01T10:00:00Z", completed_at: "2024-04-01T10:00:05Z" },
        ],
        errors: [],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockDetail));

      const { result } = renderHook(() => useIngestionJobDetail("job-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.id).toBe("job-1");
      expect(result.current.data?.domain).toBe("https://example.com");
      expect(result.current.data?.progress.percentComplete).toBe(100);
      expect(result.current.data?.progress.processedPages).toBe(100);
      expect(result.current.data?.stages).toHaveLength(1);
    });

    it("does not fetch when jobId is null", async () => {
      const { result } = renderHook(() => useIngestionJobDetail(null), {
        wrapper: createWrapper(),
      });

      // Should be in initial state, not loading
      expect(result.current.isLoading).toBe(false);
      expect(result.current.data).toBeUndefined();
      expect(apiClient.get).not.toHaveBeenCalled();
    });

    it("maps backend fields to frontend types (snake_case to camelCase)", async () => {
      const mockDetail = {
        id: "job-1",
        target_id: "target-1",
        organization_id: "org-1",
        configuration: { url: "https://example.com" },
        status: "EXTRACTING",
        priority: 3,
        created_at: "2024-04-01T10:00:00Z",
        triggered_by: "scheduler",
        created_by: "user-1",
        progress: {
          total_pages: 50,
          processed_pages: 25,
          failed_pages: 2,
          current_url: "https://example.com/page-25",
          current_stage: "EXTRACTING",
          percent_complete: 50,
        },
        results: {
          raw_content_count: 25,
          extracted_record_count: 23,
          storage_bytes_used: 512000,
        },
        resources: {
          browser_sessions_used: 1,
          proxy_requests_made: 50,
          llm_tokens_consumed: 2500,
          compute_time_ms: 150000,
        },
        stages: [],
        errors: [],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockDetail));

      const { result } = renderHook(() => useIngestionJobDetail("job-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      const data = result.current.data!;
      expect(data.targetId).toBe("target-1");
      expect(data.organizationId).toBe("org-1");
      expect(data.triggeredBy).toBe("scheduler");
      expect(data.createdBy).toBe("user-1");
      expect(data.progress.totalPages).toBe(50);
      expect(data.progress.processedPages).toBe(25);
      expect(data.progress.failedPages).toBe(2);
      expect(data.progress.currentUrl).toBe("https://example.com/page-25");
      expect(data.progress.currentStage).toBe("EXTRACTING");
      expect(data.results.rawContentCount).toBe(25);
      expect(data.results.extractedRecordCount).toBe(23);
      expect(data.resources.browserSessionsUsed).toBe(1);
      expect(data.resources.proxyRequestsMade).toBe(50);
    });

    it("handles job with errors", async () => {
      const mockDetail = {
        id: "job-1",
        target_id: "target-1",
        organization_id: "org-1",
        configuration: { url: "https://example.com" },
        status: "FAILED",
        priority: 5,
        created_at: "2024-04-01T10:00:00Z",
        triggered_by: "manual",
        created_by: "user-1",
        progress: { processed_pages: 10, failed_pages: 5, current_stage: "EXTRACTING", percent_complete: 20 },
        results: { raw_content_count: 10, extracted_record_count: 0, storage_bytes_used: 0 },
        resources: { browser_sessions_used: 1, proxy_requests_made: 15, llm_tokens_consumed: 1000, compute_time_ms: 60000 },
        stages: [],
        errors: [
          {
            id: "error-1",
            stage: "EXTRACTING",
            error_code: "TIMEOUT",
            error_message: "Request timed out after 30s",
            url: "https://example.com/slow-page",
            retryable: true,
            retry_count: 2,
            occurred_at: "2024-04-01T10:01:00Z",
          },
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockDetail));

      const { result } = renderHook(() => useIngestionJobDetail("job-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data?.errors).toHaveLength(1);
      expect(result.current.data?.errors[0].errorCode).toBe("TIMEOUT");
      expect(result.current.data?.errors[0].retryable).toBe(true);
      expect(result.current.data?.errors[0].retryCount).toBe(2);
    });
  });

  describe("useJobComplianceLogs", () => {
    it("fetches logs for selected job", async () => {
      const mockLogs = {
        items: [
          {
            id: "log-1",
            event_type: "ROBOTS_TXT_CHECK",
            severity: "INFO",
            request_url: "https://example.com",
            request_timestamp: "2024-04-01T10:00:00Z",
            response_action_taken: "Allowed",
            created_at: "2024-04-01T10:00:01Z",
          },
          {
            id: "log-2",
            event_type: "RATE_LIMIT_APPLIED",
            severity: "WARNING",
            request_url: "https://example.com/page-2",
            request_timestamp: "2024-04-01T10:01:00Z",
            response_action_taken: "Delayed 1000ms",
            created_at: "2024-04-01T10:01:01Z",
          },
        ],
      };

      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse(mockLogs));

      const { result } = renderHook(() => useJobComplianceLogs("job-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));

      expect(result.current.data).toHaveLength(2);
      expect(result.current.data?.[0].eventType).toBe("ROBOTS_TXT_CHECK");
      expect(result.current.data?.[0].severity).toBe("INFO");
      expect(result.current.data?.[1].severity).toBe("WARNING");

      // Verify job_id is passed in query params
      expect(apiClient.get).toHaveBeenCalledWith("l1", expect.stringContaining("job_id=job-1"));
    });

    it("returns empty array when no logs", async () => {
      vi.mocked(apiClient.get).mockResolvedValueOnce(createMockResponse({ items: [] }));

      const { result } = renderHook(() => useJobComplianceLogs("job-1"), {
        wrapper: createWrapper(),
      });

      await waitFor(() => expect(result.current.isSuccess).toBe(true));
      expect(result.current.data).toHaveLength(0);
    });

    it("does not fetch when jobId is null", async () => {
      const { result } = renderHook(() => useJobComplianceLogs(null), {
        wrapper: createWrapper(),
      });

      expect(result.current.isLoading).toBe(false);
      expect(apiClient.get).not.toHaveBeenCalled();
    });
  });

  describe("useCancelJob", () => {
    it("calls DELETE /jobs/{id}", async () => {
      vi.mocked(apiClient.delete).mockResolvedValueOnce(createMockResponse({ status: "CANCELLED", job_id: "job-1" }));

      const { result } = renderHook(() => useCancelJob(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync("job-1");

      expect(apiClient.delete).toHaveBeenCalledWith("l1", "/jobs/job-1");
    });

    it("exposes error on failure", async () => {
      vi.mocked(apiClient.delete).mockRejectedValueOnce(new Error("Job not found"));

      const { result } = renderHook(() => useCancelJob(), {
        wrapper: createWrapper(),
      });

      result.current.mutate("job-1");

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error?.message).toBe("Job not found");
    });
  });

  describe("useRetryJob", () => {
    it("calls POST /jobs/{id}/retry with FULL strategy", async () => {
      vi.mocked(apiClient.post).mockResolvedValueOnce(createMockResponse({ job_id: "job-2", status: "PENDING" }));

      const { result } = renderHook(() => useRetryJob(), {
        wrapper: createWrapper(),
      });

      await result.current.mutateAsync("job-1");

      expect(apiClient.post).toHaveBeenCalledWith("l1", "/jobs/job-1/retry", { retry_strategy: "FULL" });
    });

    it("exposes error on failure", async () => {
      vi.mocked(apiClient.post).mockRejectedValueOnce(new Error("Cannot retry active job"));

      const { result } = renderHook(() => useRetryJob(), {
        wrapper: createWrapper(),
      });

      result.current.mutate("job-1");

      await waitFor(() => expect(result.current.isError).toBe(true));
      expect(result.current.error?.message).toBe("Cannot retry active job");
    });
  });
});
