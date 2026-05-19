import { describe, expect, it } from "vitest";
import {
  getWorkspaceTabOrDefault,
  resolveAccountScopedWorkspacePath,
  resolveWorkspaceRoutePath,
  isValidWorkspaceTab,
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

describe("workspace tab validation", () => {
  it("accepts valid intelligence tabs", () => {
    expect(isValidWorkspaceTab("intelligence", "signals")).toBe(true);
    expect(isValidWorkspaceTab("intelligence", "hypotheses")).toBe(true);
    expect(isValidWorkspaceTab("intelligence", "evidence")).toBe(true);
  });

  it("rejects invalid intelligence tabs", () => {
    expect(isValidWorkspaceTab("intelligence", "not-a-tab")).toBe(false);
    expect(isValidWorkspaceTab("intelligence", undefined)).toBe(false);
  });

  it("accepts valid studio tabs", () => {
    expect(isValidWorkspaceTab("studio", "action-plan")).toBe(true);
    expect(isValidWorkspaceTab("studio", "roi")).toBe(true);
  });

  it("rejects invalid studio tabs", () => {
    expect(isValidWorkspaceTab("studio", "signals")).toBe(false);
  });
});

describe("resolveAccountScopedWorkspacePath — tab path construction", () => {
  it("builds intelligence tab path", () => {
    expect(
      resolveAccountScopedWorkspacePath({
        workspace: "intelligence",
        accountId: "acct-1",
        tab: "signals",
      })
    ).toBe("/intelligence/acct-1/signals");
  });

  it("uses default tab when tab is undefined", () => {
    expect(
      resolveAccountScopedWorkspacePath({
        workspace: "intelligence",
        accountId: "acct-1",
      })
    ).toBe("/intelligence/acct-1/signals");
  });

  it("uses default tab when tab is invalid", () => {
    expect(
      resolveAccountScopedWorkspacePath({
        workspace: "studio",
        accountId: "acct-1",
        tab: "bad-tab",
      })
    ).toBe("/studio/acct-1/action-plan");
  });
});
