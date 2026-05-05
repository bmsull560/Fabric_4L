import { describe, expect, it } from "vitest";

import {
  parseCapabilityCoverageList,
  parsePortfolioSummary,
  parseProduct,
  parseProductListResponse,
  parseSignalMatchList,
} from "./products";

const validProduct = {
  id: "prod-1",
  name: "Value Fabric Platform",
  description: "A value intelligence platform",
  category: "platform",
  sku: "VF-ENT",
  pricing_model: "subscription",
  target_personas: ["CRO", "RevOps"],
  industries: ["software", "financial-services"],
  features: [{ id: "feature-1", name: "Signal matching" }],
  capabilities: [{ id: "capability-1", name: "Pipeline acceleration" }],
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-02T00:00:00Z",
};

describe("product runtime-boundary parsers", () => {
  it("parses a valid product and preserves passthrough backend fields", () => {
    const result = parseProduct({
      ...validProduct,
      backend_only_score: 0.91,
    });

    expect(result.id).toBe("prod-1");
    expect(result.name).toBe("Value Fabric Platform");
    expect(result.backend_only_score).toBe(0.91);
  });

  it("applies array defaults for optional product collection fields", () => {
    const result = parseProduct({
      id: "prod-2",
      name: "Whitespace Radar",
    });

    expect(result.target_personas).toEqual([]);
    expect(result.industries).toEqual([]);
    expect(result.features).toEqual([]);
    expect(result.capabilities).toEqual([]);
  });

  it("rejects a product missing required identity fields", () => {
    expect(() => parseProduct({ id: "prod-invalid" })).toThrowError();
  });

  it("parses a valid product list response and applies pagination defaults", () => {
    const result = parseProductListResponse({
      products: [validProduct],
      total: 1,
    });

    expect(result.products).toHaveLength(1);
    expect(result.skip).toBe(0);
    expect(result.limit).toBe(0);
  });

  it("rejects invalid product list totals", () => {
    expect(() =>
      parseProductListResponse({
        products: [validProduct],
        total: -1,
      })
    ).toThrowError();
  });

  it("parses signal-match arrays with nested product records", () => {
    const result = parseSignalMatchList([
      {
        product: validProduct,
        total_score: 0.82,
        signal_count: 3,
        top_matches: [{ signal_id: "sig-1", score: 0.9 }],
      },
    ]);

    expect(result[0]?.signal_count).toBe(3);
    expect(result[0]?.top_matches).toEqual([
      { signal_id: "sig-1", score: 0.9 },
    ]);
  });

  it("rejects malformed signal-match scores", () => {
    expect(() =>
      parseSignalMatchList([
        {
          product: validProduct,
          total_score: "high",
          signal_count: 3,
          top_matches: [],
        },
      ])
    ).toThrowError();
  });

  it("parses portfolio summaries", () => {
    const result = parsePortfolioSummary({
      total_products: 2,
      total_features: 4,
      total_capabilities: 3,
      categories: ["platform", "analytics"],
      avg_features_per_product: 2,
      avg_capabilities_per_product: 1.5,
    });

    expect(result.total_products).toBe(2);
    expect(result.avg_capabilities_per_product).toBe(1.5);
  });

  it("rejects malformed portfolio summaries", () => {
    expect(() =>
      parsePortfolioSummary({
        total_products: 2,
        total_features: 4,
        total_capabilities: 3,
        categories: "platform",
        avg_features_per_product: 2,
        avg_capabilities_per_product: 1.5,
      })
    ).toThrowError();
  });

  it("parses capability coverage lists", () => {
    const result = parseCapabilityCoverageList([
      {
        capability: { id: "capability-1", name: "Pipeline acceleration" },
        products: [validProduct],
        signal_demand: 7,
        status: "covered",
      },
    ]);

    expect(result[0]?.signal_demand).toBe(7);
    expect(result[0]?.status).toBe("covered");
  });

  it("rejects negative capability signal demand", () => {
    expect(() =>
      parseCapabilityCoverageList([
        {
          capability: { id: "capability-1", name: "Pipeline acceleration" },
          products: [validProduct],
          signal_demand: -1,
          status: "covered",
        },
      ])
    ).toThrowError();
  });
});
