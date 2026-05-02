import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { http, HttpResponse } from "msw";
import { server } from "../../../test/mocks/server";
import { apiClient } from "./client";
import {
  applySessionServiceTestEnvironment,
  authFixtures,
  type MemoryStorage,
} from "@/test/authSessionTestUtils";

describe("ApiClient", () => {
  let testLocalStorage: MemoryStorage;

  beforeEach(() => {
    ({ localStorage: testLocalStorage } = applySessionServiceTestEnvironment());
  });

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
      testLocalStorage.clear();
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    it("should include tenant ID header from localStorage", async () => {
      testLocalStorage.setItem(
        "vf.auth.session",
        JSON.stringify(
          authFixtures.validSession({
            tenantId: "test-tenant-123",
            user: authFixtures.user({ tenantId: "test-tenant-123" }),
          })
        )
      );
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
      expect(capturedHeaders.authorization).toMatch(/^Bearer /);
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

      // Wrap in try/catch to prevent unhandled rejection warning
      let error: Error | undefined;
      try {
        await apiClient.get("l3", "/test");
      } catch (e) {
        error = e as Error;
      }
      expect(error).toBeDefined();
    });

    it("should throw on HTTP error status", async () => {
      server.use(
        http.get("/api/v1/graph/test", () => {
          return HttpResponse.json({ error: "Server Error" }, { status: 500 });
        })
      );

      // Wrap in try/catch to prevent unhandled rejection warning
      let error: Error | undefined;
      try {
        await apiClient.get("l3", "/test");
      } catch (e) {
        error = e as Error;
      }
      expect(error).toBeDefined();
      expect(error?.message).toContain("Request failed with status code 500");
    });
  });

  describe("URL construction contract (FE-001 regression protection)", () => {
    it("never produces duplicate /v1/ segments", async () => {
      const testCases = ["l1", "l2", "l3", "l4", "l5", "l6"] as const;
      const capturedUrls: string[] = [];

      server.use(
        http.get("/api/v1/:layer/*", ({ request }) => {
          capturedUrls.push(request.url);
          return HttpResponse.json({});
        })
      );

      for (const layer of testCases) {
        try {
          await apiClient.get(layer, "/test");
        } catch {
          // Expected - handler returns empty, may throw
        }
      }

      for (const url of capturedUrls) {
        const pathname = new URL(url).pathname;
        expect(pathname).not.toMatch(/\/v1\/v1\//);
        expect(pathname).not.toMatch(/\/v1$/);
        expect(pathname).toMatch(/^\/api\/v1\/\w+/);
      }
    });

    it("correctly composes /api/v1 + /benchmarks -> /api/v1/benchmarks", async () => {
      let capturedUrl = "";

      server.use(
        http.get("/api/v1/benchmarks/datasets", ({ request }) => {
          capturedUrl = request.url;
          return HttpResponse.json({ data: [] });
        })
      );

      await apiClient.get("l6", "/datasets");
      expect(capturedUrl).toContain("/api/v1/benchmarks/datasets");
      expect(capturedUrl).not.toContain("/v1/v1/");
    });

    it("correctly composes all layer prefixes", async () => {
      const expectations: Record<string, string> = {
        l1: "/api/v1/ingest/health",
        l2: "/api/v1/extract/jobs",
        l3: "/api/v1/graph/entities",
        l4: "/api/v1/agents/workflows",
        l5: "/api/v1/truths/audit",
        l6: "/api/v1/benchmarks/datasets",
      };

      for (const [layer, expectedPath] of Object.entries(expectations)) {
        let capturedUrl = "";

        server.use(
          http.get(expectedPath, ({ request }) => {
            capturedUrl = request.url;
            return HttpResponse.json({});
          })
        );

        const endpoint = expectedPath.split("/").pop() || "/test";
        await apiClient.get(layer as "l1" | "l2" | "l3" | "l4" | "l5" | "l6", "/" + endpoint);
        expect(capturedUrl).toContain(expectedPath);
      }
    });
  });
});
