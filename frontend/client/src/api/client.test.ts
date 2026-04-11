import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../../../test/mocks/server";
import { apiClient } from "./client";

describe("ApiClient", () => {
  describe("layer routing", () => {
    it("should route l1 requests to ingestion layer", async () => {
      let capturedUrl = "";
      server.use(
        http.get("/api/v1/ingest/health", ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({ status: "ok" });
        })
      );

      await apiClient.get("l1", "/health");
      expect(capturedUrl).toContain("/api/v1/ingest/health");
    });

    it("should route l3 requests to knowledge graph layer", async () => {
      let capturedUrl = "";
      server.use(
        http.get("/api/v1/graph/entities", ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({ entities: [] });
        })
      );

      await apiClient.get("l3", "/entities");
      expect(capturedUrl).toContain("/api/v1/graph/entities");
    });

    it("should route l4 requests to agents layer", async () => {
      let capturedUrl = "";
      server.use(
        http.get("/api/v1/agents/workflows/active", ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json([]);
        })
      );

      await apiClient.get("l4", "/workflows/active");
      expect(capturedUrl).toContain("/api/v1/agents/workflows/active");
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
      let capturedHeaders: Record<string, string> = {};

      server.use(
        http.get("/api/v1/graph/test", ({ request }) => {
          request.headers.forEach((value, key) => {
            capturedHeaders[key] = value;
          });
          return HttpResponse.json({});
        })
      );

      await apiClient.get("l3", "/test");
      expect(capturedHeaders["x-tenant-id"]).toBe("test-tenant-123");
    });

    it("should use default tenant ID when not in localStorage", async () => {
      let capturedHeaders: Record<string, string> = {};

      server.use(
        http.get("/api/v1/graph/test", ({ request }) => {
          request.headers.forEach((value, key) => {
            capturedHeaders[key] = value;
          });
          return HttpResponse.json({});
        })
      );

      await apiClient.get("l3", "/test");
      expect(capturedHeaders["x-tenant-id"]).toBe("default");
    });
  });

  describe("error handling", () => {
    it("should throw on network errors", async () => {
      server.use(
        http.get("/api/v1/graph/test", () => {
          return HttpResponse.error();
        })
      );

      await expect(apiClient.get("l3", "/test")).rejects.toThrow();
    });

    it("should throw on HTTP error status", async () => {
      server.use(
        http.get("/api/v1/graph/test", () => {
          return HttpResponse.json({ error: "Server Error" }, { status: 500 });
        })
      );

      await expect(apiClient.get("l3", "/test")).rejects.toThrow("Request failed with status code 500");
    });
  });
});
