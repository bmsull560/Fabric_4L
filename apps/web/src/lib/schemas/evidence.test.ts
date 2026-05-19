import { describe, expect, it } from "vitest";
import type { CaseStudiesEvidenceResponse, CaseStudyEvidence } from "@/hooks/useEvidence";
import {
  parseBulkImportResponse,
  parseCaseStudy,
  parseCaseStudyListResponse,
  parseCaseStudyMutationResponse,
  parseDeleteCaseStudyResponse,
  parseEvidenceSearchResponse,
  parseEvidenceStatsResponse,
} from "./evidence";

const backendCaseStudy = {
  id: "case-study-1",
  tenant_id: "tenant-1",
  evidence_type: "case_study",
  title: "Acme reduced onboarding time with Fabric",
  content:
    "Acme used Fabric to consolidate buying signals and reduced onboarding friction across the enterprise sales process.",
  summary:
    "Fabric helped Acme reduce onboarding time while improving pipeline quality.",
  industry: "Healthcare",
  company_name: "Acme Health",
  company_size: "enterprise",
  products_used: ["Fabric Intelligence"],
  pain_signals_addressed: ["slow onboarding"],
  outcomes: [
    {
      metric: "Onboarding time",
      before_value: "90 days",
      after_value: "45 days",
      improvement_pct: 50,
      time_to_achieve_days: 120,
    },
  ],
  time_to_value_days: 30,
  deal_size_usd: 250000,
  published_date: "2026-04-01",
  tags: ["healthcare", "onboarding"],
  created_at: "2026-04-01T00:00:00Z",
  updated_at: "2026-04-02T00:00:00Z",
  linked_products: ["Fabric Intelligence"],
  linked_signals: ["slow onboarding"],
};

const workflowCaseStudiesFixture: CaseStudyEvidence[] = [
  {
    id: "case-study-1",
    title: "Acme reduced onboarding time with Fabric",
    industry: "Healthcare",
    year: 2026,
  },
];

const workflowEvidenceFixture = {
  total: 1,
  offset: 0,
  limit: 20,
  items: [backendCaseStudy],
  case_studies: workflowCaseStudiesFixture,
} satisfies CaseStudiesEvidenceResponse;

describe("evidence schemas", () => {
  it("parses backend-shaped case-study detail payloads", () => {
    const parsed = parseCaseStudy(backendCaseStudy);

    expect(parsed.id).toBe("case-study-1");
    expect(parsed.products_used).toEqual(["Fabric Intelligence"]);
    expect(parsed.outcomes[0]?.improvement_pct).toBe(50);
    expect(parsed.linked_signals).toEqual(["slow onboarding"]);
  });

  it("parses backend-shaped case-study list envelopes", () => {
    const parsed = parseCaseStudyListResponse(workflowEvidenceFixture);

    expect(parsed.total).toBe(1);
    expect(parsed.items).toHaveLength(1);
    expect(parsed.items[0]?.title).toBe(
      "Acme reduced onboarding time with Fabric"
    );
  });

  it("parses create and update mutation acknowledgement payloads", () => {
    const parsed = parseCaseStudyMutationResponse({
      id: "case-study-1",
      title: "Acme reduced onboarding time with Fabric",
      industry: "Healthcare",
      status: "created",
    });

    expect(parsed.status).toBe("created");
  });

  it("parses delete acknowledgement payloads", () => {
    const parsed = parseDeleteCaseStudyResponse({
      id: "case-study-1",
      status: "deleted",
    });

    expect(parsed.id).toBe("case-study-1");
  });

  it("parses backend stats maps returned by industry and product endpoints", () => {
    const parsed = parseEvidenceStatsResponse({
      Healthcare: 3,
      Manufacturing: 2,
    });

    expect(parsed.Healthcare).toBe(3);
  });

  it("parses bulk-import result envelopes and structured row errors", () => {
    const parsed = parseBulkImportResponse({
      total: 2,
      created: 1,
      errors: [
        {
          index: 1,
          title: "Incomplete evidence",
          error: "content is required",
        },
      ],
    });

    expect(parsed.created).toBe(1);
    expect(parsed.errors[0]?.index).toBe(1);
  });

  it("parses semantic evidence-search result envelopes", () => {
    const parsed = parseEvidenceSearchResponse({
      query: "reduce onboarding time",
      total: 1,
      results: [
        {
          evidence_id: "case-study-1",
          evidence_type: "case_study",
          title: "Acme reduced onboarding time with Fabric",
          match_score: 88,
          match_reasoning: "Strong vector match to onboarding outcomes.",
          relevance_quote: null,
        },
      ],
    });

    expect(parsed.results[0]?.match_score).toBe(88);
  });

  it("rejects malformed case-study payloads missing required identity", () => {
    expect(() =>
      parseCaseStudy({
        title: "Missing identity",
      })
    ).toThrow();
  });

  it("rejects malformed stats maps with non-numeric counts", () => {
    expect(() =>
      parseEvidenceStatsResponse({
        Healthcare: "three",
      })
    ).toThrow();
  });

  it("rejects malformed semantic search scores outside the backend range", () => {
    expect(() =>
      parseEvidenceSearchResponse({
        query: "reduce onboarding time",
        total: 1,
        results: [
          {
            evidence_id: "case-study-1",
            evidence_type: "case_study",
            title: "Acme reduced onboarding time with Fabric",
            match_score: 101,
            match_reasoning: "Out of range.",
          },
        ],
      })
    ).toThrow();
  });
});
