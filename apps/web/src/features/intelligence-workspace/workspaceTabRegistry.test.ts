import { afterEach, describe, expect, it, vi } from "vitest";

async function loadRegistry() {
  return import("./workspaceTabRegistry");
}

describe("workspaceTabRegistry production visibility", () => {
  afterEach(() => {
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it("hides deferred stub tabs in production mode", async () => {
    vi.stubEnv("VITE_APP_ENV", "production");

    const { getActiveTabDefs, isValidTab } = await loadRegistry();
    const tabIds = getActiveTabDefs().map((tab) => tab.id);

    expect(tabIds).not.toContain("ontology-match");
    expect(tabIds).not.toContain("alternatives");
    expect(tabIds).not.toContain("solution-cost");
    expect(isValidTab("ontology-match")).toBe(false);
  });

  it("allows deferred tabs in non-production only when rollout flags are enabled", async () => {
    vi.stubEnv("VITE_APP_ENV", "development");
    vi.stubEnv("VITE_ENABLE_IW_ONTOLOGY_MATCH_TAB", "true");
    vi.stubEnv("VITE_ENABLE_IW_ALTERNATIVES_TAB", "true");
    vi.stubEnv("VITE_ENABLE_IW_SOLUTION_COST_TAB", "true");

    const { getActiveTabDefs } = await loadRegistry();
    const tabIds = getActiveTabDefs().map((tab) => tab.id);

    expect(tabIds).toContain("ontology-match");
    expect(tabIds).toContain("alternatives");
    expect(tabIds).toContain("solution-cost");
  });
});
