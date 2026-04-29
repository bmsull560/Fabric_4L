import { describe, expect, it } from "vitest";
import {
  getWorkspaceTabOrDefault,
  resolveAccountScopedWorkspacePath,
  resolveWorkspaceRoutePath,
} from "./accountRouting";

describe("account routing utilities", () => {
  it("falls back to /accounts when no account is selected", () => {
    expect(
      resolveAccountScopedWorkspacePath({
        workspace: "intelligence",
        accountId: null,
        tab: "signals",
      })
    ).toBe("/accounts");
  });

  it("falls back to workspace default tab for invalid tabs", () => {
    expect(getWorkspaceTabOrDefault("intelligence", "not-a-tab")).toBe("signals");
    expect(getWorkspaceTabOrDefault("studio", "bad-tab")).toBe("action-plan");
  });

  it("keeps root workspace routes and deep links consistent", () => {
    const accountId = "acct-123";

    expect(resolveWorkspaceRoutePath("/intelligence", accountId)).toBe(
      "/intelligence/acct-123"
    );
    expect(resolveWorkspaceRoutePath("/intelligence/signals", accountId)).toBe(
      "/intelligence/acct-123/signals"
    );

    expect(resolveWorkspaceRoutePath("/studio", accountId)).toBe(
      "/studio/acct-123"
    );
    expect(resolveWorkspaceRoutePath("/studio/narrative", accountId)).toBe(
      "/studio/acct-123/narrative"
    );
  });
});
