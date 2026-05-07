import { expect, test } from "@playwright/test";
import { clearUserTier, setUserTier } from "./fixtures";

test.describe("Value Case regenerate + versions", () => {
  test.beforeEach(async ({ page }) => {
    await setUserTier(page, "standard");
  });

  test.afterEach(async ({ page }) => {
    await clearUserTier(page);
  });

  test("regenerates after assumption change using current scenario/model context", async ({ page }) => {
    let callCount = 0;
    await page.route("**/api/v1/agents/v1/value-case/artifacts?account_id=demo-account-123", async (route) => {
      await route.fulfill({ json: { versions: [] } });
    });
    await page.route("**/api/v1/agents/analysis/cases?account_id=demo-account-123", async (route) => {
      await route.fulfill({ json: [{ id: "case-default" }] });
    });
    await page.route("**/api/v1/agents/analysis/cases/case-default/workspace/*", async (route) => {
      const tab = route.request().url().split("/").pop();
      if (tab === "stakeholders") return route.fulfill({ json: { stakeholders: [{ name: "Economic buyer" }] } });
      if (tab === "evidence") return route.fulfill({ json: { evidence: [{ title: "Validated calculator assumptions", decision: "accepted" }] } });
      return route.fulfill({ json: { assumptions: [{ statement: "Conservative ramp in Q1", status: "active" }] } });
    });
    await page.route("**/api/v1/graph/v1/roi/calculations?account_id=demo-account-123&limit=1", async (route) => {
      await route.fulfill({ json: { calculations: [{ id: "model-current", npv: 1500000, total_roi_pct: 210, payback_months: 10 }] } });
    });
    await page.route("**/api/v1/agents/v1/narratives/generate", async (route) => {
      await route.fulfill({ json: { id: "nar-1", title: "Case", sections: [], created_at: "2026-05-07T00:00:00Z", updated_at: "2026-05-07T00:00:00Z" } });
    });
    await page.route("**/api/v1/agents/v1/value-case/artifacts", async (route) => {
      callCount += 1;
      const payload = route.request().postDataJSON() as { inputs: { scenario_assumptions: string[]; risk_notes: string[] } };
      expect(payload.inputs.scenario_assumptions[0]).toContain("Conservative ramp");
      expect(payload.inputs.risk_notes[0]).toContain("model-current");
      await route.fulfill({ json: { id: `v-${callCount}`, account_id: "demo-account-123", version: callCount, created_at: "2026-05-07T00:00:00Z", inputs: payload.inputs, narrative: { id: "nar-1", title: "Case", sections: [], created_at: "2026-05-07T00:00:00Z", updated_at: "2026-05-07T00:00:00Z" }, business_case: { summary: "ok", metrics: { three_year_value: "$1,500,000", roi: "210%", payback: "10 months" }, risks: [] }, lineage: { narrative_id: "nar-1", business_case_id: "bc-demo-account-123" } } });
    });

    await page.goto("/value-case/demo-account-123");
    await page.getByRole("button", { name: /Generate|Regenerate/ }).click();
    expect(callCount).toBe(1);
  });

  test("returning users can retrieve and select prior versions", async ({ page }) => {
    await page.route("**/api/v1/agents/v1/value-case/artifacts?account_id=demo-account-123", async (route) => {
      await route.fulfill({ json: { versions: [{ id: "demo-account-123-v1", account_id: "demo-account-123", version: 1, created_at: "2026-05-07T00:00:00Z", inputs: { account_id: "demo-account-123", account_name: "Demo", stakeholders: [], accepted_evidence: [], scenario_assumptions: [], roi_metrics: { three_year_value: "$100", roi: "10%", payback: "12 months" }, risk_notes: [] }, narrative: { id: "nar-1", title: "Version One", sections: [], created_at: "2026-05-07T00:00:00Z", updated_at: "2026-05-07T00:00:00Z" }, business_case: { summary: "v1", metrics: { three_year_value: "$100", roi: "10%", payback: "12 months" }, risks: [] }, lineage: { narrative_id: "nar-1", business_case_id: "bc-1" } }] } });
    });
    await page.goto("/value-case/demo-account-123");
    await expect(page.getByRole("button", { name: "v1" })).toBeVisible();
    await page.getByRole("button", { name: "v1" }).click();
    await expect(page.getByText("Version One")).toBeVisible();
  });
});
