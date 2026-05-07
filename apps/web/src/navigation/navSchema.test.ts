import { describe, expect, it } from "vitest";
import { resolveBreadcrumbs } from "./navSchema";

describe("resolveBreadcrumbs", () => {
  it("resolves account-scoped workspace labels from nav schema", () => {
    expect(resolveBreadcrumbs("/intelligence/acct-123/signals").map((c) => c.label)).toEqual([
      "Intelligence",
      "Signals",
    ]);
  });

  it("uses progression labels across the full workflow", () => {
    expect(resolveBreadcrumbs("/intelligence/acct-123/hypotheses").map((c) => c.label)).toEqual([
      "Intelligence",
      "Opportunities / Value Paths",
    ]);
    expect(resolveBreadcrumbs("/intelligence/acct-123/drivers").map((c) => c.label)).toEqual([
      "Intelligence",
      "Driver Tree",
    ]);
    expect(resolveBreadcrumbs("/intelligence/acct-123/evidence").map((c) => c.label)).toEqual([
      "Intelligence",
      "Evidence",
    ]);
    expect(resolveBreadcrumbs("/intelligence/acct-123/roi").map((c) => c.label)).toEqual([
      "Intelligence",
      "Scenarios",
    ]);
    expect(resolveBreadcrumbs("/value-case/acct-123").map((c) => c.label)).toEqual([
      "Value Case",
      "Business Case",
    ]);
    expect(resolveBreadcrumbs("/realization/acct-123").map((c) => c.label)).toEqual([
      "Realization",
      "Realization",
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

  it("preserves old deep links via breadcrumb aliases", () => {
    expect(resolveBreadcrumbs("/hypothesis/acct-123").map((c) => c.label)).toEqual([
      "Intelligence",
      "Opportunities / Value Paths",
    ]);
    expect(resolveBreadcrumbs("/drivers/acct-123/evidence").map((c) => c.label)).toEqual([
      "Intelligence",
      "Evidence",
    ]);
    expect(resolveBreadcrumbs("/calculator/acct-123").map((c) => c.label)).toEqual([
      "Intelligence",
      "Scenarios",
    ]);
  });
});
