/**
 * Robust prompt parser for ProspectPromptBuilder.
 *
 * Replaces brittle line-by-line exact matching with regex-based section
 * extraction that tolerates natural language variation in headers and
 * bullet styles.
 */

export type SectionKey =
  | "company"
  | "buyingContext"
  | "stakeholders"
  | "businessPain"
  | "deliverable"
  | "compliance"
  | "researchFocus"
  | "notes"

export type DeliverableType =
  | "account_brief"
  | "discovery_prep"
  | "value_hypotheses"
  | "executive_summary"

export type Stakeholders = {
  economicBuyer: string
  champion: string
  evaluator: string
  compliance: string
}

export type ProspectSetupDraft = {
  companyName: string
  companyDomain: string
  industry: string
  buyingContext: string
  whyNow: string
  knownInitiative: string
  stakeholders: Stakeholders
  businessPain: string[]
  currentFriction: string[]
  desiredOutcomes: string[]
  desiredOutputs: DeliverableType[]
  compliance: {
    regulatedIndustry: string
    knownRequirements: string[]
    securityReviewExpected: string
  }
  researchFocus: string[]
  notes: string
}

export type ParsedPrompt = {
  draft: ProspectSetupDraft
  visibleSections: Record<SectionKey, boolean>
}

const DELIVERABLE_MAP: Record<string, DeliverableType> = {
  "account brief": "account_brief",
  "discovery prep": "discovery_prep",
  "value hypotheses": "value_hypotheses",
  "executive summary": "executive_summary",
}

function createEmptyDraft(): ProspectSetupDraft {
  return {
    companyName: "",
    companyDomain: "",
    industry: "",
    buyingContext: "",
    whyNow: "",
    knownInitiative: "",
    stakeholders: { economicBuyer: "", champion: "", evaluator: "", compliance: "" },
    businessPain: [],
    currentFriction: [],
    desiredOutcomes: [],
    desiredOutputs: [],
    compliance: { regulatedIndustry: "", knownRequirements: [], securityReviewExpected: "" },
    researchFocus: [],
    notes: "",
  }
}

function createEmptyVisible(): Record<SectionKey, boolean> {
  return {
    company: false,
    buyingContext: false,
    stakeholders: false,
    businessPain: false,
    deliverable: false,
    compliance: false,
    researchFocus: false,
    notes: false,
  }
}

function deliverableValueFromLabel(label: string): DeliverableType | undefined {
  const normalized = label.trim().toLowerCase()
  return DELIVERABLE_MAP[normalized]
}

/* ─── Regex helpers ─────────────────────────────────────────────────────── */

/** Build a regex that matches a header line, case-insensitive.
 *  Allows optional trailing colon and whitespace. */
function headerRe(...patterns: string[]): RegExp {
  const inner = patterns.map((p) => p.replace(/\s+/g, "\\s+")).join("|")
  return new RegExp(`^(?:${inner})\\s*:?\\s*$`, "i")
}

/** Match a line that starts with a key and captures the value after the first colon. */
function kvRe(...keys: string[]): RegExp {
  const inner = keys.map((k) => k.replace(/\s+/g, "\\s+")).join("|")
  return new RegExp(`^(?:${inner})\\s*[:：]\\s*(.*)$`, "i")
}

/* ─── Section header definitions ────────────────────────────────────────── */

const COMPANY_RE = headerRe("company(?: name)?", "organization", "org", "firm")
const WEBSITE_RE = headerRe("website", "domain", "web(?:site)?", "url")
const INDUSTRY_RE = headerRe("industry", "vertical", "sector")

const BUYING_CONTEXT_RE = headerRe("buying context", "business context", "context")
const WHY_NOW_RE = headerRe("why this account now", "why now", "urgency", "trigger")
const KNOWN_INITIATIVE_RE = headerRe(
  "known initiative or trigger",
  "known initiative",
  "initiative",
  "trigger event"
)

const STAKEHOLDERS_RE = headerRe("stakeholders", "decision makers", "buying committee", "buying team")

const BUSINESS_PAIN_RE = headerRe(
  "known or suspected business pains",
  "business pains",
  "pain points",
  "challenges",
  "problems"
)
const CURRENT_FRICTION_RE = headerRe(
  "current friction",
  "friction",
  "blockers",
  "obstacles",
  "barriers"
)
const DESIRED_OUTCOMES_RE = headerRe(
  "desired business outcome",
  "desired outcomes",
  "outcomes",
  "goals",
  "objectives"
)

const DESIRED_OUTPUT_RE = headerRe(
  "desired output",
  "outputs",
  "deliverables",
  "deliverable"
)

const COMPLIANCE_RE = headerRe(
  "compliance sensitivity",
  "compliance",
  "security review",
  "regulatory"
)

const RESEARCH_FOCUS_RE = headerRe(
  "research focus",
  "focus areas",
  "research priorities"
)

const NOTES_RE = headerRe("additional notes", "notes", "extra context", "comments")

/* ─── Extraction helpers ────────────────────────────────────────────────── */

function readSingleLine(lines: string[], consumed: boolean[], ...patterns: string[]): string {
  const re = kvRe(...patterns)
  for (let i = 0; i < lines.length; i++) {
    if (consumed[i]) continue
    const match = lines[i].match(re)
    if (match) {
      consumed[i] = true
      return match[1].trim()
    }
  }
  return ""
}

function readBullets(lines: string[], startIndex: number, consumed: boolean[]): string[] {
  const items: string[] = []
  for (let i = startIndex + 1; i < lines.length; i++) {
    const trimmed = lines[i].trim()
    if (!trimmed) {
      consumed[i] = true
      if (items.length) break
      continue
    }
    if (!/^[-*•+]\s/.test(trimmed)) break
    consumed[i] = true
    const item = trimmed.replace(/^[-*•+]\s*/, "").trim()
    if (item) items.push(item)
  }
  return items
}

function findSectionStart(lines: string[], consumed: boolean[], re: RegExp): number {
  for (let i = 0; i < lines.length; i++) {
    if (consumed[i]) continue
    if (re.test(lines[i].trim())) {
      consumed[i] = true
      return i
    }
  }
  return -1
}

/* ─── Stakeholder role detection ────────────────────────────────────────── */

function parseStakeholderItem(item: string): { role: keyof Stakeholders | null; value: string } {
  const [rawKey, ...rest] = item.split(":")
  const value = rest.join(":").trim()
  if (!value) return { role: null, value: item }

  const key = rawKey.trim().toLowerCase()

  if (key.includes("economic") || key.includes("buyer") || key.includes("decision")) {
    return { role: "economicBuyer", value }
  }
  if (key.includes("champion") || key.includes("sponsor") || key.includes("advocate")) {
    return { role: "champion", value }
  }
  if (key.includes("technical") || key.includes("evaluator") || key.includes("it ")) {
    return { role: "evaluator", value }
  }
  if (key.includes("compliance") || key.includes("legal") || key.includes("security")) {
    return { role: "compliance", value }
  }

  return { role: null, value: item }
}

/* ─── Compliance item detection ─────────────────────────────────────────── */

function parseComplianceItem(item: string): { key: string; value: string } {
  const [rawKey, ...rest] = item.split(":")
  const value = rest.join(":").trim()
  return { key: rawKey.trim().toLowerCase(), value }
}

/* ─── Main parser ───────────────────────────────────────────────────────── */

export function parsePromptText(promptText: string): ParsedPrompt {
  const draft = createEmptyDraft()
  const visibleSections = createEmptyVisible()

  const lines = promptText.split(/\r?\n/)
  const consumed = new Array(lines.length).fill(false)

  // --- Company ---
  draft.companyName = readSingleLine(lines, consumed, "company", "company name", "organization", "org", "firm")
  draft.companyDomain = readSingleLine(lines, consumed, "website", "domain", "url")
  draft.industry = readSingleLine(lines, consumed, "industry", "vertical", "sector")
  if (draft.companyName || draft.companyDomain || draft.industry) visibleSections.company = true

  // --- Buying context ---
  draft.buyingContext = readSingleLine(lines, consumed, "buying context", "business context", "context")
  draft.whyNow = readSingleLine(lines, consumed, "why this account now", "why now", "urgency")
  draft.knownInitiative = readSingleLine(lines, consumed, "known initiative or trigger", "known initiative", "initiative", "trigger event")
  if (draft.buyingContext || draft.whyNow || draft.knownInitiative) visibleSections.buyingContext = true

  // --- Stakeholders ---
  const shIndex = findSectionStart(lines, consumed, STAKEHOLDERS_RE)
  if (shIndex !== -1 || /(^|\n)stakeholders?[:：]?/i.test(promptText)) {
    visibleSections.stakeholders = true
  }
  if (shIndex !== -1) {
    const shItems = readBullets(lines, shIndex, consumed)
    for (const item of shItems) {
      const parsed = parseStakeholderItem(item)
      if (parsed.role) {
        draft.stakeholders[parsed.role] = parsed.value
      }
    }
  }

  // --- Business pain ---
  const bpIndex = findSectionStart(lines, consumed, BUSINESS_PAIN_RE)
  if (bpIndex !== -1) {
    draft.businessPain = readBullets(lines, bpIndex, consumed)
    visibleSections.businessPain = true
  }

  // --- Current friction ---
  const cfIndex = findSectionStart(lines, consumed, CURRENT_FRICTION_RE)
  if (cfIndex !== -1) {
    draft.currentFriction = readBullets(lines, cfIndex, consumed)
    visibleSections.businessPain = true
  }

  // --- Desired outcomes ---
  const doIndex = findSectionStart(lines, consumed, DESIRED_OUTCOMES_RE)
  if (doIndex !== -1) {
    draft.desiredOutcomes = readBullets(lines, doIndex, consumed)
    visibleSections.businessPain = true
  }

  // Also mark businessPain visible if any pain/friction/outcome bullets were found
  if (draft.businessPain.length || draft.currentFriction.length || draft.desiredOutcomes.length) {
    visibleSections.businessPain = true
  }

  // --- Desired outputs / deliverables ---
  const outIndex = findSectionStart(lines, consumed, DESIRED_OUTPUT_RE)
  if (outIndex !== -1) {
    const outItems = readBullets(lines, outIndex, consumed)
    draft.desiredOutputs = outItems
      .map((v) => deliverableValueFromLabel(v))
      .filter((v): v is DeliverableType => Boolean(v))
    visibleSections.deliverable = true
  }
  // Fallback: detect deliverable section even if bullets didn't parse
  if (!visibleSections.deliverable && /(^|\n)(desired output|deliverable|output)s?[:：]?/i.test(promptText)) {
    visibleSections.deliverable = true
  }

  // --- Compliance ---
  const compIndex = findSectionStart(lines, consumed, COMPLIANCE_RE)
  if (compIndex !== -1) {
    const compItems = readBullets(lines, compIndex, consumed)
    for (const item of compItems) {
      const { key, value } = parseComplianceItem(item)
      if (key.includes("regulated industry") || key.includes("regulated")) {
        draft.compliance.regulatedIndustry = value
      } else if (key.includes("known requirements") || key.includes("requirements")) {
        draft.compliance.knownRequirements = value
          ? value.split(/[;,]/).map((p) => p.trim()).filter(Boolean)
          : []
      } else if (key.includes("security") || key.includes("legal review") || key.includes("review expected")) {
        draft.compliance.securityReviewExpected = value
      }
    }
    visibleSections.compliance = true
  }
  if (!visibleSections.compliance && /(^|\n)compliance[:：]?/i.test(promptText)) {
    visibleSections.compliance = true
  }

  // --- Research focus ---
  const rfIndex = findSectionStart(lines, consumed, RESEARCH_FOCUS_RE)
  if (rfIndex !== -1) {
    draft.researchFocus = readBullets(lines, rfIndex, consumed)
    visibleSections.researchFocus = true
  }
  if (!visibleSections.researchFocus && /(^|\n)research focus[:：]?/i.test(promptText)) {
    visibleSections.researchFocus = true
  }

  // --- Notes ---
  const notesIndex = findSectionStart(lines, consumed, NOTES_RE)
  if (notesIndex !== -1) {
    visibleSections.notes = true
    const noteLines: string[] = []
    for (let i = notesIndex + 1; i < lines.length; i++) {
      consumed[i] = true
      noteLines.push(lines[i])
    }
    draft.notes = noteLines.join("\n").trim()
  }

  // Collect any leftover non-empty lines as notes if notes section wasn't explicitly found
  if (!draft.notes) {
    const leftover = lines.filter((line, i) => !consumed[i] && line.trim().length > 0)
    if (leftover.length > 0) {
      draft.notes = leftover.join("\n").trim()
      visibleSections.notes = true
    }
  }

  return { draft, visibleSections }
}
