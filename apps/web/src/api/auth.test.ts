import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { apiClient } from "./client";
import { registerWithEmailPassword } from "./auth";

vi.mock("./client", () => ({
  apiClient: {
    post: vi.fn(),
  },
}));

describe("registerWithEmailPassword", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("posts a validated email/password registration request to Layer 4", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({
      data: {
        access_token: "token-123",
        token_type: "bearer",
        expires_in: 3600,
        refresh_token: "refresh-123",
        user_id: "user-123",
        email: "buyer@example.com",
        role: "tenant_admin",
        tenant_id: "tenant-123",
        tenant_slug: "tenant-123",
      },
    });

    const result = await registerWithEmailPassword({
      email: "buyer@example.com",
      password: "correct-horse-battery-staple",
    });

    expect(apiClient.post).toHaveBeenCalledWith("l4", "/tenants/register", {
      email: "buyer@example.com",
      password: "correct-horse-battery-staple",
    });
    expect(result).toMatchObject({
      access_token: "token-123",
      role: "tenant_admin",
      tenant_id: "tenant-123",
    });
  });

  it("rejects malformed registration requests before calling the API", async () => {
    await expect(
      registerWithEmailPassword({ email: "not-an-email", password: "short" }),
    ).rejects.toThrow();

    expect(apiClient.post).not.toHaveBeenCalled();
  });

  it("rejects malformed registration responses at the API boundary", async () => {
    (apiClient.post as Mock).mockResolvedValueOnce({
      data: {
        access_token: "",
        email: "buyer@example.com",
      },
    });

    await expect(
      registerWithEmailPassword({
        email: "buyer@example.com",
        password: "correct-horse-battery-staple",
      }),
    ).rejects.toThrow();
  });
});
