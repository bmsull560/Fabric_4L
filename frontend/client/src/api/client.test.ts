import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import axios from "axios";
import { apiClient } from "./client";

describe("ApiClient", () => {
  describe("layer routing", () => {
    it("should route l1 requests to ingestion layer", async () => {
      const mockGet = vi.spyOn(axios, "get").mockRejectedValueOnce(new Error("Network error"));
      try {
        await apiClient.get("l1", "/health");
      } catch {
        // Expected to fail
      }
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("/ingest"),
        expect.any(Object)
      );
      mockGet.mockRestore();
    });

    it("should route l3 requests to knowledge graph layer", async () => {
      const mockGet = vi.spyOn(axios, "get").mockRejectedValueOnce(new Error("Network error"));
      try {
        await apiClient.get("l3", "/entities");
      } catch {
        // Expected to fail
      }
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("/graph"),
        expect.any(Object)
      );
      mockGet.mockRestore();
    });
  });

  describe("request configuration", () => {
    beforeEach(() => {
      localStorage.clear();
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it("should include tenant ID header from localStorage", async () => {
      localStorage.setItem("tenantId", "test-tenant-123");
      
      const mockGet = vi.spyOn(axios, "get").mockRejectedValueOnce(new Error("Network error"));
      try {
        await apiClient.get("l3", "/test");
      } catch {
        // Expected
      }

      const callArg = mockGet.mock.calls[0][1] as { headers?: Record<string, string> };
      expect(callArg?.headers?.["X-Tenant-ID"]).toBe("test-tenant-123");
      mockGet.mockRestore();
    });

    it("should use default tenant ID when not in localStorage", async () => {
      const mockGet = vi.spyOn(axios, "get").mockRejectedValueOnce(new Error("Network error"));
      try {
        await apiClient.get("l3", "/test");
      } catch {
        // Expected
      }

      const callArg = mockGet.mock.calls[0][1] as { headers?: Record<string, string> };
      expect(callArg?.headers?.["X-Tenant-ID"]).toBe("default");
      mockGet.mockRestore();
    });
  });

  describe("error handling", () => {
    it("should throw on network errors", async () => {
      vi.spyOn(axios, "get").mockRejectedValueOnce(new Error("Network error"));
      
      await expect(apiClient.get("l3", "/test")).rejects.toThrow("Network error");
    });

    it("should throw on timeout errors", async () => {
      const timeoutError = new Error("timeout of 30000ms exceeded");
      vi.spyOn(axios, "get").mockRejectedValueOnce(timeoutError);
      
      await expect(apiClient.get("l3", "/test")).rejects.toThrow("timeout");
    });
  });
});
