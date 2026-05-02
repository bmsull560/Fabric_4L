import { describe, expect, it } from "vitest";
import { resolveBreadcrumbs } from "./navSchema";

describe("resolveBreadcrumbs", () => {
  it("resolves account-scoped workspace labels from nav schema", () => {
    expect(resolveBreadcrumbs("/intelligence/acct-123/signals").map((c) => c.label)).toEqual([
      "Intelligence",
      "Signals",
    ]);
  });

  it("prefers explicit breadcrumb labels when provided", () => {
    expect(resolveBreadcrumbs("/studio/acct-123/action-plan").map((c) => c.label)).toEqual([
      "Value Studio",
      "Action Plan",
    ]);
  });

  it("hides opaque ids by design", () => {
    expect(resolveBreadcrumbs("/accounts/12345678-abcd-1234-abcd-1234567890ab").map((c) => c.label)).toEqual([
      "Accounts",
    ]);
  });
});
