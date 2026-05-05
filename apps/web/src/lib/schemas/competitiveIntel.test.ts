import { describe, expect, it } from "vitest";

import {
  parseBattlecard,
  parseBattlecardList,
  parseCompetitiveLandscapeResponse,
  parseCompetitor,
  parseCompetitorListResponse,
  parseWinLossRecord,
  parseWinLossSummaryResponse,
} from "./competitiveIntel";

describe("competitiveIntel schemas", () => {
  it("parses competitor list envelopes with backend overlap counts", () => {
    const parsed = parseCompetitorListResponse({
      competitors: [
        {
          id: "comp-1",
          name: "Acme Analytics",
          description: "Competitive analytics platform",
          domain: "acme.example",
          founded_year: 2018,
          strengths: ["integrations"],
          weaknesses: ["pricing"],
          market_position: "challenger",
          pricing_tier: "mid",
          target_segments: ["enterprise"],
          product_overlap_count: 2,
          entity_type: "Competitor",
          created_at: "2026-01-01T00:00:00Z",
          updated_at: "2026-01-02T00:00:00Z",
        },
      ],
      total: 1,
      skip: 0,
      limit: 50,
    });

    expect(parsed.competitors[0].name).toBe("Acme Analytics");
    expect(parsed.competitors[0].product_overlap_count).toBe(2);
  });

  it("parses competitor details with related products and battlecard previews", () => {
    const parsed = parseCompetitor({
      id: "comp-1",
      name: "Acme Analytics",
      strengths: [],
      weaknesses: [],
      target_segments: [],
      competing_products: [
        { id: "prod-1", name: "Fabric 4L", overlap_score: 0.8 },
      ],
      battlecards: [
        {
          id: "bc-1",
          product_id: "prod-1",
          positioning: "Stronger value proof.",
        },
      ],
    });

    expect(parsed.competing_products[0].overlap_score).toBe(0.8);
    expect(parsed.battlecards[0].id).toBe("bc-1");
  });

  it("rejects malformed competitor list totals", () => {
    expect(() =>
      parseCompetitorListResponse({ competitors: [], total: -1 })
    ).toThrow();
  });

  it("parses battlecard payloads with stored string objection handlers", () => {
    const parsed = parseBattlecard({
      id: "bc-1",
      tenant_id: "tenant-1",
      competitor_id: "comp-1",
      product_id: "prod-1",
      positioning: "Lead with ROI evidence.",
      differentiators: ["workflow automation"],
      objection_handlers: ["Cost: show payback period"],
      talk_tracks: ["Anchor on measurable value"],
      win_themes: ["speed to value"],
      trap_questions: ["How are outcomes measured today?"],
      last_reviewed_at: "2026-01-01T00:00:00Z",
      created_at: "2026-01-01T00:00:00Z",
      updated_at: "2026-01-02T00:00:00Z",
    });

    expect(parsed.objection_handlers).toEqual(["Cost: show payback period"]);
  });

  it("parses battlecard list responses", () => {
    const parsed = parseBattlecardList([
      {
        id: "bc-1",
        competitor_id: "comp-1",
        product_id: "prod-1",
        positioning: "Differentiate on governed value modeling.",
      },
    ]);

    expect(parsed).toHaveLength(1);
  });

  it("rejects malformed battlecards without identifiers", () => {
    expect(() =>
      parseBattlecard({ competitor_id: "comp-1", product_id: "prod-1" })
    ).toThrow();
  });

  it("parses recorded win-loss responses", () => {
    const parsed = parseWinLossRecord({
      id: "wl-1",
      outcome: "won",
      deal_size_usd: 125000,
      reason: "Superior quantified value story",
      industry: "Software",
      recorded_at: "2026-01-03T00:00:00Z",
      status: "recorded",
    });

    expect(parsed.outcome).toBe("won");
  });

  it("rejects unsupported win-loss outcomes", () => {
    expect(() =>
      parseWinLossRecord({ id: "wl-1", outcome: "maybe" })
    ).toThrow();
  });

  it("parses win-loss summary envelopes", () => {
    const parsed = parseWinLossSummaryResponse({
      competitors: [
        {
          competitor: {
            id: "comp-1",
            name: "Acme Analytics",
            market_position: "challenger",
          },
          wins: 3,
          losses: 1,
          total_deals: 4,
          win_rate: 0.75,
          won_revenue: 300000,
          lost_revenue: 100000,
        },
      ],
      total_competitors: 1,
    });

    expect(parsed.competitors[0].win_rate).toBe(0.75);
  });

  it("parses competitive landscape envelopes", () => {
    const parsed = parseCompetitiveLandscapeResponse({
      landscape: [
        {
          competitor: {
            id: "comp-1",
            name: "Acme Analytics",
            market_position: "challenger",
            pricing_tier: "mid",
          },
          product_overlaps: 2,
          wins: 3,
          losses: 1,
          win_rate: 0.75,
          overlap_score: 0.8,
        },
      ],
      total_competitors: 1,
      total_wins: 3,
      total_losses: 1,
      overall_win_rate: 0.75,
    });

    expect(parsed.landscape[0].competitor.name).toBe("Acme Analytics");
  });

  it("rejects malformed landscape entries", () => {
    expect(() =>
      parseCompetitiveLandscapeResponse({
        landscape: [
          {
            competitor: {},
            wins: 1,
            losses: 0,
            win_rate: 1,
            overlap_score: 0.5,
          },
        ],
        total_competitors: 1,
        total_wins: 1,
        total_losses: 0,
        overall_win_rate: 1,
      })
    ).toThrow();
  });
});
