"use client"

import * as React from "react"
import { useLocation } from "wouter"
import {
  ArrowUp,
  Briefcase,
  Building2,
  FileText,
  History,
  Mic,
  Paperclip,
  Search,
  Settings2,
  Shield,
  Sparkles,
  Users,
  Wand2,
} from "lucide-react"

import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Command,
  CommandEmpty,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from "@/components/ui/command"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Label } from "@/components/ui/label"
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { Separator } from "@/components/ui/separator"
import { Switch } from "@/components/ui/switch"
import { Textarea } from "@/components/ui/textarea"
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { WorkflowLayout } from "../components/WorkflowLayout"
import { useWorkflowStore } from "../store/workflowStore"
import { STEPS } from "../constants"

type PromptMode = "Fast" | "Balanced" | "Deep"
type DeliverableType =
  | "account_brief"
  | "discovery_prep"
  | "value_hypotheses"
  | "executive_summary"
type EnrichmentDepth = "light" | "standard" | "deep"
type SectionKey =
  | "company"
  | "buyingContext"
  | "stakeholders"
  | "businessPain"
  | "deliverable"
  | "compliance"
  | "researchFocus"
  | "notes"

type Stakeholders = {
  economicBuyer: string
  champion: string
  evaluator: string
  compliance: string
}

type ProspectSetupDraft = {
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

type AttachmentItem = {
  id: string
  name: string
}

type CreateSetupResult = {
  accountId: string
} | void

export type ProspectSetupPromptPayload = {
  companyName?: string
  companyDomain?: string
  industry?: string
  accountContext?: string
  buyingContext?: string
  whyNow?: string
  knownInitiative?: string
  businessPain?: string[]
  currentFriction?: string[]
  desiredOutcomes?: string[]
  stakeholders?: Partial<Stakeholders>
  sourceArtifacts?: AttachmentItem[]
  outputType: DeliverableType
  desiredOutputs: DeliverableType[]
  mode: PromptMode
  enrichmentDepth: EnrichmentDepth
  useUploadedFiles: boolean
  usePriorAccountContext: boolean
  runWebEnrichment: boolean
  complianceSensitive: boolean
  deepResearch: boolean
  freeformPrompt: string
}

export type CompanyOption = {
  id: string
  name: string
  domain?: string
  industry?: string
  accountId?: string
}

type ActivityItem = {
  id: string
  title: string
  updatedAt: string
  prompt: string
}

type AttachResult = void | null | AttachmentItem | AttachmentItem[]

type ProspectPromptBuilderProps = {
  className?: string
  initialValue?: string
  initialCompany?: CompanyOption
  companyOptions?: CompanyOption[]
  recentActivities?: ActivityItem[]
  onCreateSetup?: (payload: ProspectSetupPromptPayload) => CreateSetupResult | Promise<CreateSetupResult>
  onAttachContent?: () => AttachResult | Promise<AttachResult>
  onOpenVoiceInput?: () => void
  onNavigateToWorkspace?: (path: string, accountId: string) => void
}

type BuilderState = {
  draft: ProspectSetupDraft
  promptText: string
  visibleSections: Record<SectionKey, boolean>
  mode: PromptMode
  primaryDeliverable: DeliverableType
  enrichmentDepth: EnrichmentDepth
  useUploadedFiles: boolean
  usePriorAccountContext: boolean
  runWebEnrichment: boolean
  complianceSensitive: boolean
  attachments: AttachmentItem[]
  selectedCompany?: CompanyOption
  isSubmitting: boolean
  isRecording: boolean
  searchOpen: boolean
  statusMessage: string
  successMessage: string
  errorMessage: string
}

type ParsedPrompt = {
  draft: ProspectSetupDraft
  visibleSections: Record<SectionKey, boolean>
}

type BuilderAction =
  | { type: "APPLY_PROMPT_TEXT"; promptText: string }
  | { type: "SELECT_COMPANY"; company: CompanyOption }
  | { type: "SYNC_SELECTED_COMPANY"; company?: CompanyOption }
  | { type: "ENABLE_SECTION"; section: SectionKey }
  | { type: "SET_MODE"; mode: PromptMode }
  | { type: "SET_PRIMARY_DELIVERABLE"; deliverable: DeliverableType }
  | { type: "SET_ENRICHMENT_DEPTH"; enrichmentDepth: EnrichmentDepth }
  | {
      type: "SET_FLAG"
      key:
        | "useUploadedFiles"
        | "usePriorAccountContext"
        | "runWebEnrichment"
        | "complianceSensitive"
      value: boolean
    }
  | { type: "SET_SEARCH_OPEN"; open: boolean }
  | { type: "SET_RECORDING"; value: boolean }
  | { type: "ATTACHMENTS_ADDED"; attachments: AttachmentItem[]; statusMessage?: string }
  | { type: "STRENGTHEN_PROMPT" }
  | { type: "ENABLE_DEEP_RESEARCH" }
  | { type: "RESTORE_ACTIVITY"; activity: ActivityItem }
  | { type: "START_SUBMIT" }
  | { type: "SUBMIT_SUCCESS"; message: string }
  | { type: "SUBMIT_ERROR"; message: string }
  | { type: "CLEAR_MESSAGES" }

const DEFAULT_COMPANIES: CompanyOption[] = [
  { id: "1", name: "Medtronic", domain: "medtronic.com", industry: "Medical Devices" },
  { id: "2", name: "Stryker", domain: "stryker.com", industry: "Medical Devices" },
  { id: "3", name: "Baxter", domain: "baxter.com", industry: "Healthcare" },
  { id: "4", name: "Johnson & Johnson MedTech", domain: "jnjmedtech.com", industry: "Medical Devices" },
  { id: "5", name: "Finastra", domain: "finastra.com", industry: "Financial Services Technology" },
]

const DEFAULT_ACTIVITIES: ActivityItem[] = [
  {
    id: "a1",
    title: "Medtronic launch readiness setup",
    updatedAt: "2h ago",
    prompt:
      "Company: Medtronic\nWebsite: medtronic.com\nIndustry: Medical Devices\n\nBuying context: New product launch readiness across distributed field teams\nWhy this account now: Need stronger rep ramp, compliant messaging, and executive discovery prep\nKnown initiative or trigger: Field launch enablement refresh\n\nStakeholders:\n- Economic buyer: VP Sales\n- Business champion: Sales Enablement Leader\n- Technical evaluator: RevOps / IT\n- Compliance / legal: Regulatory and legal operations\n\nKnown or suspected business pains:\n- Rep onboarding is slow for complex offerings\n- Messaging consistency is difficult across field teams\n- Launch content is fragmented across systems\n\nCurrent friction:\n- Multiple systems create version confusion\n- Coaching quality varies by manager\n\nDesired business outcome:\n- Faster rep ramp time\n- More consistent compliant messaging\n- Better launch readiness\n\nDesired output:\n- Account brief\n- Discovery prep\n- Value hypotheses\n\nCompliance sensitivity:\n- Regulated industry: yes\n- Known requirements: FDA-related controls; auditability\n- Security / legal review expected: yes",
  },
  {
    id: "a2",
    title: "Financial services coaching setup",
    updatedAt: "Yesterday",
    prompt:
      "Company: Goldman Sachs\nWebsite: goldmansachs.com\nIndustry: Financial Services\n\nBuying context: Advisor enablement and coaching scale\nWhy this account now: Need consistent messaging and compliance-safe coaching motions\n\nDesired output:\n- Executive summary\n- Value hypotheses",
  },
]

const MODE_OPTIONS: PromptMode[] = ["Fast", "Balanced", "Deep"]

const DELIVERABLE_OPTIONS: { label: string; value: DeliverableType }[] = [
  { label: "Account brief", value: "account_brief" },
  { label: "Discovery prep", value: "discovery_prep" },
  { label: "Value hypotheses", value: "value_hypotheses" },
  { label: "Executive summary", value: "executive_summary" },
]

const ENRICHMENT_OPTIONS: { label: string; value: EnrichmentDepth }[] = [
  { label: "Light", value: "light" },
  { label: "Standard", value: "standard" },
  { label: "Deep", value: "deep" },
]

const UI_BUTTON_STYLES = {
  pill:
    "h-10 rounded-2xl border border-border/60 bg-background px-4 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-foreground",
  icon:
    "h-10 w-10 rounded-2xl border border-transparent bg-transparent text-muted-foreground shadow-none transition-all hover:border-border/60 hover:bg-muted hover:text-foreground hover:shadow-sm",
  accentIcon:
    "h-10 w-10 rounded-2xl border border-transparent bg-transparent text-violet-600 shadow-none transition-all hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700 hover:shadow-sm dark:text-violet-400 dark:hover:border-violet-500/40 dark:hover:bg-violet-500/10 dark:hover:text-violet-300",
  option:
    "h-10 rounded-2xl border border-border/60 bg-background px-3 text-sm font-medium shadow-sm transition-colors hover:bg-accent hover:text-foreground",
  primary:
    "h-10 rounded-2xl bg-foreground px-4 text-sm font-medium text-background shadow-sm transition-opacity hover:opacity-90 disabled:pointer-events-none disabled:opacity-50",
  chip:
    "min-h-11 w-full justify-start rounded-2xl border border-border/60 bg-background px-3 py-3 text-left text-sm font-medium text-foreground shadow-sm transition-colors hover:bg-accent hover:text-foreground",
  badge:
    "rounded-2xl border border-border/60 bg-muted/40 px-2.5 py-1 text-xs font-medium",
} as const

const CORE_SECTIONS: SectionKey[] = [
  "company",
  "buyingContext",
  "stakeholders",
  "businessPain",
  "deliverable",
]

function createEmptyDraft(): ProspectSetupDraft {
  return {
    companyName: "",
    companyDomain: "",
    industry: "",
    buyingContext: "",
    whyNow: "",
    knownInitiative: "",
    stakeholders: {
      economicBuyer: "",
      champion: "",
      evaluator: "",
      compliance: "",
    },
    businessPain: [],
    currentFriction: [],
    desiredOutcomes: [],
    desiredOutputs: [],
    compliance: {
      regulatedIndustry: "",
      knownRequirements: [],
      securityReviewExpected: "",
    },
    researchFocus: [],
    notes: "",
  }
}

function createEmptyVisibleSections(): Record<SectionKey, boolean> {
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

function hasContent(value: string | string[]) {
  return Array.isArray(value) ? value.some((item) => item.trim().length > 0) : value.trim().length > 0
}

function deliverableLabel(value: DeliverableType) {
  return DELIVERABLE_OPTIONS.find((option) => option.value === value)?.label ?? value
}

function deliverableValueFromLabel(label: string): DeliverableType | undefined {
  const normalized = label.trim().toLowerCase()
  return DELIVERABLE_OPTIONS.find((option) => option.label.toLowerCase() === normalized)?.value
}

function serializeBulletSection(title: string, items: string[], placeholder = "") {
  const filteredItems = items.filter((item) => item.trim().length > 0)
  const lines = filteredItems.length > 0 ? filteredItems.map((item) => `- ${item}`) : placeholder ? [`- ${placeholder}`] : ["-"]
  return `${title}:\n${lines.join("\n")}` 
}

function serializeDraft(
  draft: ProspectSetupDraft,
  visibleSections: Record<SectionKey, boolean>,
  primaryDeliverable: DeliverableType
) {
  const sections: string[] = []

  const showCompany =
    visibleSections.company || hasContent(draft.companyName) || hasContent(draft.companyDomain) || hasContent(draft.industry)
  if (showCompany) {
    sections.push(
      [
        `Company: ${draft.companyName}`,
        `Website: ${draft.companyDomain}`,
        `Industry: ${draft.industry}`,
      ].join("\n")
    )
  }

  const showBuyingContext =
    visibleSections.buyingContext ||
    hasContent(draft.buyingContext) ||
    hasContent(draft.whyNow) ||
    hasContent(draft.knownInitiative)
  if (showBuyingContext) {
    sections.push(
      [
        `Buying context: ${draft.buyingContext}`,
        `Why this account now: ${draft.whyNow}`,
        `Known initiative or trigger: ${draft.knownInitiative}`,
      ].join("\n")
    )
  }

  const showStakeholders =
    visibleSections.stakeholders || Object.values(draft.stakeholders).some((value) => value.trim().length > 0)
  if (showStakeholders) {
    sections.push(
      [
        "Stakeholders:",
        `- Economic buyer: ${draft.stakeholders.economicBuyer}`,
        `- Business champion: ${draft.stakeholders.champion}`,
        `- Technical evaluator: ${draft.stakeholders.evaluator}`,
        `- Compliance / legal: ${draft.stakeholders.compliance}`,
      ].join("\n")
    )
  }

  const showBusinessPain =
    visibleSections.businessPain ||
    hasContent(draft.businessPain) ||
    hasContent(draft.currentFriction) ||
    hasContent(draft.desiredOutcomes)
  if (showBusinessPain) {
    sections.push(
      [
        serializeBulletSection("Known or suspected business pains", draft.businessPain),
        serializeBulletSection("Current friction", draft.currentFriction),
        serializeBulletSection("Desired business outcome", draft.desiredOutcomes),
      ].join("\n\n")
    )
  }

  const outputs = draft.desiredOutputs.length > 0 ? draft.desiredOutputs : visibleSections.deliverable ? [primaryDeliverable] : []
  const showDeliverable = visibleSections.deliverable || outputs.length > 0
  if (showDeliverable) {
    sections.push(
      serializeBulletSection(
        "Desired output",
        outputs.map((item) => deliverableLabel(item)),
        deliverableLabel(primaryDeliverable)
      )
    )
  }

  const showCompliance =
    visibleSections.compliance ||
    hasContent(draft.compliance.regulatedIndustry) ||
    hasContent(draft.compliance.knownRequirements) ||
    hasContent(draft.compliance.securityReviewExpected)
  if (showCompliance) {
    sections.push(
      [
        "Compliance sensitivity:",
        `- Regulated industry: ${draft.compliance.regulatedIndustry}`,
        `- Known requirements: ${draft.compliance.knownRequirements.join("; ")}`,
        `- Security / legal review expected: ${draft.compliance.securityReviewExpected}`,
      ].join("\n")
    )
  }

  const showResearchFocus = visibleSections.researchFocus || hasContent(draft.researchFocus)
  if (showResearchFocus) {
    sections.push(serializeBulletSection("Research focus", draft.researchFocus, "Company overview and current priorities"))
  }

  const showNotes = visibleSections.notes || hasContent(draft.notes)
  if (showNotes) {
    sections.push(`Additional notes:\n${draft.notes}`.trim())
  }

  return sections.join("\n\n").trim()
}

function parsePromptText(promptText: string): ParsedPrompt {
  const draft = createEmptyDraft()
  const visibleSections = createEmptyVisibleSections()
  const lines = promptText.split(/\r?\n/)
  const consumed = new Array(lines.length).fill(false)

  const readSingleLine = (label: string) => {
    const lowerLabel = `${label.toLowerCase()}:` 
    const index = lines.findIndex((line) => line.trim().toLowerCase().startsWith(lowerLabel))
    if (index === -1) return ""
    consumed[index] = true
    const raw = lines[index].split(":").slice(1).join(":").trim()
    return raw
  }

  const readBulletSection = (label: string) => {
    const lowerLabel = `${label.toLowerCase()}:` 
    const startIndex = lines.findIndex((line) => line.trim().toLowerCase() === lowerLabel)
    if (startIndex === -1) return [] as string[]
    consumed[startIndex] = true

    const items: string[] = []
    for (let i = startIndex + 1; i < lines.length; i += 1) {
      const line = lines[i]
      const trimmed = line.trim()
      if (!trimmed) {
        if (items.length > 0) {
          consumed[i] = true
          break
        }
        consumed[i] = true
        continue
      }
      if (!trimmed.startsWith("-")) break
      consumed[i] = true
      const item = trimmed.replace(/^\-\s*/, "").trim()
      if (item) items.push(item)
    }
    return items
  }

  const readStakeholders = () => {
    const items = readBulletSection("Stakeholders")
    if (items.length > 0 || /(^|\n)Stakeholders:/i.test(promptText)) {
      visibleSections.stakeholders = true
    }
    for (const item of items) {
      const [rawKey, ...rest] = item.split(":")
      const value = rest.join(":").trim()
      const key = rawKey.trim().toLowerCase()
      if (key.includes("economic")) draft.stakeholders.economicBuyer = value
      if (key.includes("champion")) draft.stakeholders.champion = value
      if (key.includes("technical") || key.includes("evaluator")) draft.stakeholders.evaluator = value
      if (key.includes("compliance") || key.includes("legal")) draft.stakeholders.compliance = value
    }
  }

  draft.companyName = readSingleLine("Company")
  draft.companyDomain = readSingleLine("Website")
  draft.industry = readSingleLine("Industry")
  draft.buyingContext = readSingleLine("Buying context")
  draft.whyNow = readSingleLine("Why this account now")
  draft.knownInitiative = readSingleLine("Known initiative or trigger")

  if (draft.companyName || draft.companyDomain || draft.industry) visibleSections.company = true
  if (draft.buyingContext || draft.whyNow || draft.knownInitiative) visibleSections.buyingContext = true

  readStakeholders()

  draft.businessPain = readBulletSection("Known or suspected business pains")
  draft.currentFriction = readBulletSection("Current friction")
  draft.desiredOutcomes = readBulletSection("Desired business outcome")
  if (draft.businessPain.length || draft.currentFriction.length || draft.desiredOutcomes.length) {
    visibleSections.businessPain = true
  }

  const outputs = readBulletSection("Desired output")
  if (outputs.length > 0 || /(^|\n)Desired output:/i.test(promptText)) visibleSections.deliverable = true
  draft.desiredOutputs = outputs
    .map((value) => deliverableValueFromLabel(value))
    .filter((value): value is DeliverableType => Boolean(value))

  const complianceItems = readBulletSection("Compliance sensitivity")
  if (complianceItems.length > 0 || /(^|\n)Compliance sensitivity:/i.test(promptText)) {
    visibleSections.compliance = true
  }
  for (const item of complianceItems) {
    const [rawKey, ...rest] = item.split(":")
    const value = rest.join(":").trim()
    const key = rawKey.trim().toLowerCase()
    if (key.includes("regulated industry")) draft.compliance.regulatedIndustry = value
    if (key.includes("known requirements")) {
      draft.compliance.knownRequirements = value
        ? value.split(/[;,]/).map((part) => part.trim()).filter(Boolean)
        : []
    }
    if (key.includes("security") || key.includes("legal review")) draft.compliance.securityReviewExpected = value
  }

  draft.researchFocus = readBulletSection("Research focus")
  if (draft.researchFocus.length > 0 || /(^|\n)Research focus:/i.test(promptText)) {
    visibleSections.researchFocus = true
  }

  const noteStart = lines.findIndex((line) => line.trim().toLowerCase() === "additional notes:")
  if (noteStart !== -1) {
    visibleSections.notes = true
    consumed[noteStart] = true
    const noteLines: string[] = []
    for (let i = noteStart + 1; i < lines.length; i += 1) {
      consumed[i] = true
      noteLines.push(lines[i])
    }
    draft.notes = noteLines.join("\n").trim()
  }

  if (!draft.notes) {
    const leftover = lines.filter((line, index) => !consumed[index] && line.trim().length > 0)
    if (leftover.length > 0) {
      draft.notes = leftover.join("\n").trim()
      visibleSections.notes = true
    }
  }

  return { draft, visibleSections }
}

function buildStrengthenedState(state: BuilderState) {
  const visibleSections = { ...state.visibleSections }
  for (const section of CORE_SECTIONS) visibleSections[section] = true
  const nextDraft =
    state.draft.desiredOutputs.length === 0
      ? { ...state.draft, desiredOutputs: [state.primaryDeliverable] }
      : state.draft
  return {
    ...state,
    draft: nextDraft,
    visibleSections,
    promptText: serializeDraft(nextDraft, visibleSections, state.primaryDeliverable),
    statusMessage: "Prompt strengthened with missing value case sections.",
    successMessage: "",
    errorMessage: "",
  }
}

function enableDeepResearchState(state: BuilderState) {
  const visibleSections = { ...state.visibleSections, researchFocus: true }
  const nextDraft: ProspectSetupDraft = {
    ...state.draft,
    researchFocus:
      state.draft.researchFocus.length > 0
        ? state.draft.researchFocus
        : [
            "Company overview and current priorities",
            "Likely stakeholders and buying committee",
            "Business pain signals",
            "Industry and compliance considerations",
            "Initial value hypotheses",
          ],
  }
  return {
    ...state,
    draft: nextDraft,
    visibleSections,
    mode: "Deep",
    enrichmentDepth: "deep",
    promptText: serializeDraft(nextDraft, visibleSections, state.primaryDeliverable),
    statusMessage: "Deep research enabled. Research focus added to the analysis.",
    successMessage: "",
    errorMessage: "",
  }
}

function builderReducer(state: BuilderState, action: BuilderAction): BuilderState {
  switch (action.type) {
    case "APPLY_PROMPT_TEXT": {
      const parsed = parsePromptText(action.promptText)
      return {
        ...state,
        draft: parsed.draft,
        visibleSections: parsed.visibleSections,
        promptText: action.promptText,
        complianceSensitive:
          state.complianceSensitive ||
          Boolean(
            parsed.visibleSections.compliance ||
              parsed.draft.compliance.regulatedIndustry ||
              parsed.draft.compliance.knownRequirements.length ||
              parsed.draft.compliance.securityReviewExpected
          ),
        successMessage: "",
        errorMessage: "",
      }
    }
    case "SELECT_COMPANY": {
      const nextDraft: ProspectSetupDraft = {
        ...state.draft,
        companyName: action.company.name,
        companyDomain: action.company.domain ?? state.draft.companyDomain,
        industry: action.company.industry ?? state.draft.industry,
      }
      const visibleSections = { ...state.visibleSections, company: true }
      return {
        ...state,
        draft: nextDraft,
        visibleSections,
        selectedCompany: action.company,
        searchOpen: false,
        promptText: serializeDraft(nextDraft, visibleSections, state.primaryDeliverable),
        statusMessage: `${action.company.name} added to the value case.`,
        successMessage: "",
        errorMessage: "",
      }
    }
    case "SYNC_SELECTED_COMPANY":
      return {
        ...state,
        selectedCompany: action.company,
      }
    case "ENABLE_SECTION": {
      const visibleSections = { ...state.visibleSections, [action.section]: true }
      let nextDraft = state.draft
      if (action.section === "deliverable" && nextDraft.desiredOutputs.length === 0) {
        nextDraft = { ...nextDraft, desiredOutputs: [state.primaryDeliverable] }
      }
      return {
        ...state,
        draft: nextDraft,
        visibleSections,
        promptText: serializeDraft(nextDraft, visibleSections, state.primaryDeliverable),
        statusMessage: `${sectionTitle(action.section)} added to the prompt.`,
        successMessage: "",
        errorMessage: "",
      }
    }
    case "SET_MODE":
      return {
        ...state,
        mode: action.mode,
        statusMessage: `${action.mode} analysis depth selected.`,
        successMessage: "",
        errorMessage: "",
      }
    case "SET_PRIMARY_DELIVERABLE": {
      const desiredOutputs = state.draft.desiredOutputs.includes(action.deliverable)
        ? state.draft.desiredOutputs
        : [action.deliverable, ...state.draft.desiredOutputs]
      const nextDraft = { ...state.draft, desiredOutputs }
      const nextVisibleSections = { ...state.visibleSections, deliverable: true }
      return {
        ...state,
        primaryDeliverable: action.deliverable,
        draft: nextDraft,
        visibleSections: nextVisibleSections,
        promptText: serializeDraft(nextDraft, nextVisibleSections, action.deliverable),
        statusMessage: `${deliverableLabel(action.deliverable)} selected as the primary output.`,
        successMessage: "",
        errorMessage: "",
      }
    }
    case "SET_ENRICHMENT_DEPTH":
      return {
        ...state,
        enrichmentDepth: action.enrichmentDepth,
        statusMessage: `${capitalize(action.enrichmentDepth)} enrichment depth selected.`,
        successMessage: "",
        errorMessage: "",
      }
    case "SET_FLAG":
      return {
        ...state,
        [action.key]: action.value,
        statusMessage: `${flagLabel(action.key)} ${action.value ? "enabled" : "disabled"}.`,
        successMessage: "",
        errorMessage: "",
      }
    case "SET_SEARCH_OPEN":
      return {
        ...state,
        searchOpen: action.open,
      }
    case "SET_RECORDING":
      return {
        ...state,
        isRecording: action.value,
        statusMessage: action.value ? "Voice input started." : "Voice input stopped.",
        successMessage: "",
        errorMessage: "",
      }
    case "ATTACHMENTS_ADDED":
      return {
        ...state,
        attachments: [...state.attachments, ...action.attachments],
        statusMessage:
          action.statusMessage ??
          `${action.attachments.length} attachment${action.attachments.length > 1 ? "s" : ""} added.`,
        successMessage: "",
        errorMessage: "",
      }
    case "STRENGTHEN_PROMPT":
      return buildStrengthenedState(state)
    case "ENABLE_DEEP_RESEARCH":
      return enableDeepResearchState(state)
    case "RESTORE_ACTIVITY": {
      const parsed = parsePromptText(action.activity.prompt)
      return {
        ...state,
        draft: parsed.draft,
        visibleSections: parsed.visibleSections,
        promptText: action.activity.prompt,
        selectedCompany: undefined,
        statusMessage: `${action.activity.title} restored.`,
        successMessage: "",
        errorMessage: "",
      }
    }
    case "START_SUBMIT":
      return {
        ...state,
        isSubmitting: true,
        statusMessage: "Launching intelligence...",
        successMessage: "",
        errorMessage: "",
      }
    case "SUBMIT_SUCCESS":
      return {
        ...state,
        isSubmitting: false,
        statusMessage: "",
        successMessage: action.message,
        errorMessage: "",
      }
    case "SUBMIT_ERROR":
      return {
        ...state,
        isSubmitting: false,
        statusMessage: "",
        successMessage: "",
        errorMessage: action.message,
      }
    case "CLEAR_MESSAGES":
      return {
        ...state,
        statusMessage: "",
        successMessage: "",
        errorMessage: "",
      }
    default:
      return state
  }
}

function getInitialState(initialValue: string, initialCompany?: CompanyOption): BuilderState {
  const hasInitialValue = initialValue.trim().length > 0
  const parsed = hasInitialValue
    ? parsePromptText(initialValue)
    : { draft: createEmptyDraft(), visibleSections: createEmptyVisibleSections() }

  const seededDraft = initialCompany
    ? {
        ...parsed.draft,
        companyName: parsed.draft.companyName || initialCompany.name,
        companyDomain: parsed.draft.companyDomain || initialCompany.domain || "",
        industry: parsed.draft.industry || initialCompany.industry || "",
      }
    : parsed.draft

  const seededVisibleSections = initialCompany
    ? { ...parsed.visibleSections, company: true }
    : parsed.visibleSections

  const primaryDeliverable = seededDraft.desiredOutputs[0] ?? "account_brief"
  const promptText = hasInitialValue
    ? initialValue.trim()
    : initialCompany
      ? serializeDraft(seededDraft, seededVisibleSections, primaryDeliverable)
      : ""

  return {
    draft: seededDraft,
    promptText,
    visibleSections: seededVisibleSections,
    mode: "Balanced",
    primaryDeliverable,
    enrichmentDepth: "standard",
    useUploadedFiles: true,
    usePriorAccountContext: true,
    runWebEnrichment: true,
    complianceSensitive:
      seededVisibleSections.compliance ||
      Boolean(
        seededDraft.compliance.regulatedIndustry ||
          seededDraft.compliance.knownRequirements.length ||
          seededDraft.compliance.securityReviewExpected
      ),
    attachments: [],
    selectedCompany: initialCompany,
    isSubmitting: false,
    isRecording: false,
    searchOpen: false,
    statusMessage: "",
    successMessage: "",
    errorMessage: "",
  }
}

function flagLabel(
  key: "useUploadedFiles" | "usePriorAccountContext" | "runWebEnrichment" | "complianceSensitive"
) {
  switch (key) {
    case "useUploadedFiles":
      return "Uploaded files"
    case "usePriorAccountContext":
      return "Prior account context"
    case "runWebEnrichment":
      return "Web enrichment"
    case "complianceSensitive":
      return "Compliance-sensitive mode"
    default:
      return key
  }
}

function sectionTitle(section: SectionKey) {
  switch (section) {
    case "company":
      return "Company details"
    case "buyingContext":
      return "Buying context"
    case "stakeholders":
      return "Stakeholders"
    case "businessPain":
      return "Business pain"
    case "deliverable":
      return "Deliverable"
    case "compliance":
      return "Compliance sensitivity"
    case "researchFocus":
      return "Research focus"
    case "notes":
      return "Additional notes"
    default:
      return section
  }
}

function capitalize(value: string) {
  return value.charAt(0).toUpperCase() + value.slice(1)
}

function createAttachmentItems(result: AttachResult, existingCount: number): AttachmentItem[] {
  if (!result) {
    return [
      {
        id: `attachment-${existingCount + 1}`,
        name: `Attachment ${existingCount + 1}`,
      },
    ]
  }
  return Array.isArray(result) ? result : [result]
}

function resolveNavigationAccountId(result: CreateSetupResult, selectedCompany?: CompanyOption) {
  if (result && typeof result === "object" && "accountId" in result && result.accountId) {
    return result.accountId
  }
  return selectedCompany?.accountId
}

function buildPayload(state: BuilderState): ProspectSetupPromptPayload {
  const accountContext = [state.draft.buyingContext, state.draft.whyNow].filter(Boolean).join(" | ") || undefined
  const stakeholders = Object.fromEntries(
    Object.entries(state.draft.stakeholders).filter(([, value]) => value.trim().length > 0)
  ) as Partial<Stakeholders>

  return {
    companyName: state.draft.companyName || undefined,
    companyDomain: state.draft.companyDomain || undefined,
    industry: state.draft.industry || undefined,
    accountContext,
    buyingContext: state.draft.buyingContext || undefined,
    whyNow: state.draft.whyNow || undefined,
    knownInitiative: state.draft.knownInitiative || undefined,
    businessPain: state.draft.businessPain,
    currentFriction: state.draft.currentFriction,
    desiredOutcomes: state.draft.desiredOutcomes,
    stakeholders: Object.keys(stakeholders).length > 0 ? stakeholders : undefined,
    sourceArtifacts: state.attachments,
    outputType: state.primaryDeliverable,
    desiredOutputs:
      state.draft.desiredOutputs.length > 0 ? state.draft.desiredOutputs : [state.primaryDeliverable],
    mode: state.mode,
    enrichmentDepth: state.enrichmentDepth,
    useUploadedFiles: state.useUploadedFiles,
    usePriorAccountContext: state.usePriorAccountContext,
    runWebEnrichment: state.runWebEnrichment,
    complianceSensitive: state.complianceSensitive,
    deepResearch: state.mode === "Deep" || state.enrichmentDepth === "deep",
    freeformPrompt: state.promptText.trim(),
  }
}

function hasMinimumContext(state: BuilderState) {
  return Boolean(state.draft.companyName || state.draft.companyDomain || state.attachments.length > 0)
}

function canSubmit(state: BuilderState) {
  return state.promptText.trim().length > 12 || hasMinimumContext(state)
}

const PromptHeader = React.memo(function PromptHeader({
  mode,
  onModeChange,
  state,
  dispatch,
  recentActivities,
}: {
  mode: PromptMode
  onModeChange: (mode: PromptMode) => void
  state: BuilderState
  dispatch: React.Dispatch<BuilderAction>
  recentActivities: ActivityItem[]
}) {
  return (
    <div className="flex items-center justify-between gap-3 px-2">
      <div className="flex min-w-0 items-center gap-2">
        <DropdownMenu>
          <Tooltip>
            <TooltipTrigger asChild>
              <DropdownMenuTrigger asChild>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className={UI_BUTTON_STYLES.pill}
                >
                  {mode}
                </Button>
              </DropdownMenuTrigger>
            </TooltipTrigger>
            <TooltipContent className="rounded-lg">Choose analysis depth</TooltipContent>
          </Tooltip>
          <DropdownMenuContent align="start" className="rounded-2xl border border-border/60 bg-popover p-1 shadow-lg">
            <DropdownMenuLabel className="text-xs uppercase tracking-wide text-muted-foreground">
              Analysis depth
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            {MODE_OPTIONS.map((option) => (
              <DropdownMenuItem key={option} onClick={() => onModeChange(option)} className="rounded-xl">
                {option}
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>

        <Badge
          variant="secondary"
          className="h-10 rounded-2xl border border-border/60 bg-muted/60 px-4 text-sm font-medium text-foreground shadow-sm"
        >
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          New Value Case
        </Badge>
      </div>

      <div className="flex items-center gap-1.5">
        <PromptSettingsPopover state={state} dispatch={dispatch} />
        <RecentActivityMenu activities={recentActivities} onRestore={(activity) => dispatch({ type: "RESTORE_ACTIVITY", activity })} />
      </div>
    </div>
  )
})

const PromptSettingsPopover = React.memo(function PromptSettingsPopover({
  state,
  dispatch,
}: {
  state: BuilderState
  dispatch: React.Dispatch<BuilderAction>
}) {
  return (
    <Popover>
      <Tooltip>
        <TooltipTrigger asChild>
          <PopoverTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={cn(UI_BUTTON_STYLES.icon, "hover:bg-muted/80")}
              aria-label="Prompt settings"
            >
              <Settings2 className="h-4 w-4" />
            </Button>
          </PopoverTrigger>
        </TooltipTrigger>
        <TooltipContent className="rounded-lg">Open analysis settings</TooltipContent>
      </Tooltip>
      <PopoverContent align="end" className="w-80 rounded-2xl border border-border/60 bg-popover p-4 shadow-lg">
        <div className="flex flex-col gap-4">
          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Deliverable</p>
            <div className="grid grid-cols-2 gap-2">
              {DELIVERABLE_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  type="button"
                  variant="outline"
                  onClick={() => dispatch({ type: "SET_PRIMARY_DELIVERABLE", deliverable: option.value })}
                  className={cn(
                    UI_BUTTON_STYLES.option,
                    "justify-start text-left",
                    state.primaryDeliverable === option.value && "border-foreground bg-accent text-foreground"
                  )}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>

          <Separator />

          <div className="space-y-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Enrichment depth</p>
            <div className="grid grid-cols-3 gap-2">
              {ENRICHMENT_OPTIONS.map((option) => (
                <Button
                  key={option.value}
                  type="button"
                  variant="outline"
                  onClick={() => dispatch({ type: "SET_ENRICHMENT_DEPTH", enrichmentDepth: option.value })}
                  className={cn(
                    UI_BUTTON_STYLES.option,
                    state.enrichmentDepth === option.value && "border-foreground bg-accent text-foreground"
                  )}
                >
                  {option.label}
                </Button>
              ))}
            </div>
          </div>

          <Separator />

          <div className="space-y-3">
            <SettingsSwitch
              id="uploaded-files"
              label="Use uploaded files"
              checked={state.useUploadedFiles}
              onCheckedChange={(value) => dispatch({ type: "SET_FLAG", key: "useUploadedFiles", value })}
            />
            <SettingsSwitch
              id="prior-context"
              label="Use prior account context"
              checked={state.usePriorAccountContext}
              onCheckedChange={(value) => dispatch({ type: "SET_FLAG", key: "usePriorAccountContext", value })}
            />
            <SettingsSwitch
              id="web-enrichment"
              label="Run web enrichment"
              checked={state.runWebEnrichment}
              onCheckedChange={(value) => dispatch({ type: "SET_FLAG", key: "runWebEnrichment", value })}
            />
            <SettingsSwitch
              id="compliance-sensitive"
              label="Compliance-sensitive mode"
              checked={state.complianceSensitive}
              onCheckedChange={(value) => dispatch({ type: "SET_FLAG", key: "complianceSensitive", value })}
            />
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
})

const RecentActivityMenu = React.memo(function RecentActivityMenu({
  activities,
  onRestore,
}: {
  activities: ActivityItem[]
  onRestore: (activity: ActivityItem) => void
}) {
  return (
    <DropdownMenu>
      <Tooltip>
        <TooltipTrigger asChild>
          <DropdownMenuTrigger asChild>
            <Button
              type="button"
              variant="ghost"
              size="icon"
              className={cn(UI_BUTTON_STYLES.icon, "hover:bg-muted/80")}
              aria-label="Recent value cases"
            >
              <History className="h-4 w-4" />
            </Button>
          </DropdownMenuTrigger>
        </TooltipTrigger>
        <TooltipContent className="rounded-lg">Open recent value cases</TooltipContent>
      </Tooltip>
      <DropdownMenuContent align="end" className="w-80 rounded-2xl border border-border/60 bg-popover p-1 shadow-lg">
        <DropdownMenuLabel className="text-xs uppercase tracking-wide text-muted-foreground">
          Recent value cases
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        {activities.map((activity) => (
          <DropdownMenuItem
            key={activity.id}
            onClick={() => onRestore(activity)}
            className="flex flex-col items-start gap-0.5 rounded-xl px-3 py-2.5"
          >
            <span className="text-sm font-medium">{activity.title}</span>
            <span className="text-xs text-muted-foreground">{activity.updatedAt}</span>
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
})

const StatusBanner = React.memo(function StatusBanner({
  successMessage,
  statusMessage,
  errorMessage,
}: Pick<BuilderState, "successMessage" | "statusMessage" | "errorMessage">) {
  if (!successMessage && !statusMessage && !errorMessage) return null

  const tone = errorMessage ? "error" : successMessage ? "success" : "info"
  const message = errorMessage || successMessage || statusMessage

  return (
    <div
      role={errorMessage ? "alert" : "status"}
      className={cn(
        "mx-5 mb-3 rounded-2xl border px-3 py-2 text-sm",
        tone === "error" && "border-red-500/30 bg-red-500/10 text-red-700 dark:text-red-300",
        tone === "success" && "border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
        tone === "info" && "border-border/60 bg-muted/40 text-foreground"
      )}
    >
      {message}
    </div>
  )
})

const SuggestionsRail = React.memo(function SuggestionsRail({
  onEnableSection,
  onCompliance,
}: {
  onEnableSection: (section: SectionKey) => void
  onCompliance: () => void
}) {
  return (
    <div className="rounded-2xl border border-border/60 bg-muted/20 p-4 shadow-sm">
      <div className="mb-3 flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-foreground">Quick start inputs</p>
          <p className="text-xs text-muted-foreground">
            Start with any section below. All of the key setup inputs are visible here.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
        <ChipButton icon={Building2} label="Add company + website" onClick={() => onEnableSection("company")} />
        <ChipButton icon={Briefcase} label="Define buying context" onClick={() => onEnableSection("buyingContext")} />
        <ChipButton icon={Users} label="Add stakeholders" onClick={() => onEnableSection("stakeholders")} />
        <ChipButton icon={Briefcase} label="Describe business pain" onClick={() => onEnableSection("businessPain")} />
        <ChipButton icon={FileText} label="Choose deliverable" onClick={() => onEnableSection("deliverable")} />
        <ChipButton icon={Shield} label="Flag compliance sensitivity" onClick={onCompliance} />
      </div>
    </div>
  )
})

export default function ProspectSetup({
  className,
  initialValue = "",
  initialCompany,
  companyOptions = DEFAULT_COMPANIES,
  recentActivities = DEFAULT_ACTIVITIES,
  onCreateSetup,
  onAttachContent,
  onOpenVoiceInput,
  onNavigateToWorkspace,
}: ProspectPromptBuilderProps) {
  const [, navigate] = useLocation()
  const { setProspect, setCurrentStep } = useWorkflowStore()
  
  const [state, dispatch] = React.useReducer(
    builderReducer,
    { initialValue, initialCompany },
    ({ initialValue, initialCompany }) => getInitialState(initialValue, initialCompany)
  )
  const textareaRef = React.useRef<HTMLTextAreaElement | null>(null)
  const helperId = React.useId()
  const statusId = React.useId()

  const matchedSelectedCompany = React.useMemo(() => {
    if (state.selectedCompany) return state.selectedCompany
    if (!state.draft.companyName && !state.draft.companyDomain) return undefined
    return companyOptions.find((company) => {
      const nameMatches = state.draft.companyName && company.name.toLowerCase() === state.draft.companyName.toLowerCase()
      const domainMatches =
        state.draft.companyDomain &&
        company.domain &&
        company.domain.toLowerCase() === state.draft.companyDomain.toLowerCase()
      return Boolean(nameMatches || domainMatches)
    })
  }, [companyOptions, state.draft.companyDomain, state.draft.companyName, state.selectedCompany])

  const activeDeliverableLabel = React.useMemo(
    () => deliverableLabel(state.primaryDeliverable),
    [state.primaryDeliverable]
  )
  const minimumContextAvailable = React.useMemo(() => hasMinimumContext(state), [state])
  const submitEnabled = React.useMemo(() => canSubmit(state), [state])
  const liveMessage = state.errorMessage || state.successMessage || state.statusMessage

  React.useEffect(() => {
    if (matchedSelectedCompany && matchedSelectedCompany !== state.selectedCompany) {
      dispatch({ type: "SYNC_SELECTED_COMPANY", company: matchedSelectedCompany })
    }
  }, [matchedSelectedCompany, state.selectedCompany])

  const focusTextareaAtEnd = React.useCallback(() => {
    const node = textareaRef.current
    if (!node) return
    requestAnimationFrame(() => {
      node.focus()
      const position = node.value.length
      node.setSelectionRange(position, position)
    })
  }, [])

  const handlePromptChange = React.useCallback((event: React.ChangeEvent<HTMLTextAreaElement>) => {
    dispatch({ type: "APPLY_PROMPT_TEXT", promptText: event.target.value })
  }, [])

  const handleEnableSection = React.useCallback(
    (section: SectionKey) => {
      dispatch({ type: "ENABLE_SECTION", section })
      focusTextareaAtEnd()
    },
    [focusTextareaAtEnd]
  )

  const handleCompanySelect = React.useCallback(
    (company: CompanyOption) => {
      dispatch({ type: "SELECT_COMPANY", company })
      focusTextareaAtEnd()
    },
    [focusTextareaAtEnd]
  )

  const handleStrengthen = React.useCallback(() => {
    dispatch({ type: "STRENGTHEN_PROMPT" })
    focusTextareaAtEnd()
  }, [focusTextareaAtEnd])

  const handleDeepResearch = React.useCallback(() => {
    if (!minimumContextAvailable) return
    dispatch({ type: "ENABLE_DEEP_RESEARCH" })
    focusTextareaAtEnd()
  }, [focusTextareaAtEnd, minimumContextAvailable])

  const handleAttach = React.useCallback(async () => {
    try {
      const result = await onAttachContent?.()
      const attachments = createAttachmentItems(result, state.attachments.length)
      dispatch({ type: "ATTACHMENTS_ADDED", attachments })
    } catch {
      dispatch({ type: "SUBMIT_ERROR", message: "Unable to attach content. Please try again." })
    }
  }, [onAttachContent, state.attachments.length])

  const handleVoiceInput = React.useCallback(() => {
    const next = !state.isRecording
    dispatch({ type: "SET_RECORDING", value: next })
    onOpenVoiceInput?.()
  }, [onOpenVoiceInput, state.isRecording])

  const handleFormSubmit = React.useCallback(
    async (event?: React.FormEvent<HTMLFormElement>) => {
      event?.preventDefault()
      if (!submitEnabled || state.isSubmitting) return

      dispatch({ type: "START_SUBMIT" })
      try {
        const payload = buildPayload(state)
        
        // Update workflow store with prospect info
        setProspect({
          companyId: state.draft.companyName ? `temp_${Date.now()}` : `temp_${Date.now()}`,
          companyName: state.draft.companyName || "",
          contactName: state.draft.stakeholders.economicBuyer || state.draft.stakeholders.champion || "",
          contactTitle: "",
        })
        
        const result = onCreateSetup ? await onCreateSetup(payload) : undefined
        const accountId = resolveNavigationAccountId(result, matchedSelectedCompany)

        dispatch({
          type: "SUBMIT_SUCCESS",
          message: accountId ? "Intelligence launched. Opening workspace..." : "New value case created.",
        })

        if (accountId) {
          const path = `/intelligence/${accountId}/signals` 
          if (onNavigateToWorkspace) {
            onNavigateToWorkspace(path, accountId)
          } else if (typeof window !== "undefined") {
            navigate(path)
          }
        } else {
          // Fallback to workflow intelligence step
          setCurrentStep(STEPS.INTELLIGENCE)
          navigate("/workflow/intelligence")
        }
      } catch {
        dispatch({ type: "SUBMIT_ERROR", message: "Unable to launch intelligence. Please review the input and try again." })
      }
    },
    [matchedSelectedCompany, onCreateSetup, onNavigateToWorkspace, state, submitEnabled, navigate, setProspect, setCurrentStep]
  )

  const handleKeyDown = React.useCallback(
    (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if ((event.metaKey || event.ctrlKey) && event.key === "Enter") {
        event.preventDefault()
        void handleFormSubmit()
      }
    },
    [handleFormSubmit]
  )

  const handleComplianceChip = React.useCallback(() => {
    dispatch({ type: "SET_FLAG", key: "complianceSensitive", value: true })
    dispatch({ type: "ENABLE_SECTION", section: "compliance" })
    focusTextareaAtEnd()
  }, [focusTextareaAtEnd])

  React.useEffect(() => {
    if (!liveMessage) return
    const timeout = window.setTimeout(() => dispatch({ type: "CLEAR_MESSAGES" }), 5000)
    return () => window.clearTimeout(timeout)
  }, [liveMessage])

  return (
    <TooltipProvider delayDuration={150}>
      <WorkflowLayout>
        <div className={cn("w-full", className)}>
          <form className="mx-auto flex w-full max-w-4xl flex-col gap-3 px-4 py-4 sm:px-6 lg:px-8" onSubmit={handleFormSubmit}>
            <PromptHeader
              mode={state.mode}
              onModeChange={(mode) => dispatch({ type: "SET_MODE", mode })}
              state={state}
              dispatch={dispatch}
              recentActivities={recentActivities}
            />

            <div className="px-2">
              <Label htmlFor="prospect-setup-prompt" className="sr-only">
                New value case prompt
              </Label>
              <p id={helperId} className="text-sm text-muted-foreground">
                Use quick inputs to shape a new value case, refine it naturally, and press Ctrl/Cmd+Enter to launch intelligence.
              </p>
            </div>

            <div className="relative overflow-hidden rounded-[28px] border border-border/60 bg-background shadow-sm">
              <div className="px-5 pt-4">
                <div className="mb-2 flex flex-wrap items-center gap-2">
                  {matchedSelectedCompany ? (
                    <Badge variant="outline" className={UI_BUTTON_STYLES.badge}>
                      <Building2 className="mr-1.5 h-3.5 w-3.5" />
                      {matchedSelectedCompany.name}
                    </Badge>
                  ) : null}
                  <Badge variant="outline" className={UI_BUTTON_STYLES.badge}>
                    {activeDeliverableLabel}
                  </Badge>
                  {state.complianceSensitive ? (
                    <Badge
                      variant="outline"
                      className="rounded-2xl border border-amber-500/40 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-700 dark:text-amber-300"
                    >
                      <Shield className="mr-1.5 h-3.5 w-3.5" />
                      Compliance-sensitive
                    </Badge>
                  ) : null}
                  {state.attachments.length > 0 ? (
                    <Badge variant="outline" className={UI_BUTTON_STYLES.badge}>
                      <Paperclip className="mr-1.5 h-3.5 w-3.5" />
                      {state.attachments.length} attachment{state.attachments.length > 1 ? "s" : ""}
                    </Badge>
                  ) : null}
                </div>
              </div>

              <Textarea
                id="prospect-setup-prompt"
                ref={textareaRef}
                value={state.promptText}
                onChange={handlePromptChange}
                onKeyDown={handleKeyDown}
                aria-describedby={`${helperId} ${statusId}`}
                placeholder="Start a new value case by entering the company, context, stakeholders, pain points, and desired output..."
                className="min-h-[132px] resize-none border-0 bg-transparent px-5 pb-3 pt-0 text-[15px] leading-6 text-foreground shadow-none placeholder:text-muted-foreground/80 focus-visible:ring-0 focus-visible:ring-offset-0"
              />

              <StatusBanner
                successMessage={state.successMessage}
                statusMessage={state.statusMessage}
                errorMessage={state.errorMessage}
              />

              <div className="flex items-center justify-between gap-3 border-t border-border/50 px-4 py-4">
                <div className="flex items-center gap-1">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={() => void handleAttach()}
                        className={UI_BUTTON_STYLES.icon}
                        aria-label="Attach source material"
                      >
                        <Paperclip className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="rounded-lg">Attach files, notes, or source material</TooltipContent>
                  </Tooltip>

                  <Popover open={state.searchOpen} onOpenChange={(open) => dispatch({ type: "SET_SEARCH_OPEN", open })}>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <PopoverTrigger asChild>
                          <Button
                            type="button"
                            variant="ghost"
                            size="icon"
                            className={UI_BUTTON_STYLES.icon}
                            aria-label="Search account or company"
                          >
                            <Search className="h-4 w-4" />
                          </Button>
                        </PopoverTrigger>
                      </TooltipTrigger>
                      <TooltipContent className="rounded-lg">Search for a company or saved account</TooltipContent>
                    </Tooltip>
                    <PopoverContent align="start" className="w-[360px] rounded-2xl border border-border/60 bg-popover p-0 shadow-lg">
                      <Command className="rounded-2xl">
                        <CommandInput placeholder="Search company, account, or domain..." className="h-11" />
                        <CommandList className="max-h-72">
                          <CommandEmpty>No matching accounts found.</CommandEmpty>
                          {companyOptions.map((company) => (
                            <CommandItem
                              key={company.id}
                              value={`${company.name} ${company.domain ?? ""} ${company.industry ?? ""}`}
                              onSelect={() => handleCompanySelect(company)}
                              className="flex items-center gap-2 px-3 py-2.5"
                            >
                              <Building2 className="h-4 w-4 text-muted-foreground" />
                              <div className="flex min-w-0 flex-col">
                                <span className="truncate text-sm font-medium">{company.name}</span>
                                <span className="truncate text-xs text-muted-foreground">
                                  {[company.domain, company.industry].filter(Boolean).join(" • ")}
                                </span>
                              </div>
                            </CommandItem>
                          ))}
                          <CommandSeparator />
                          <CommandItem onSelect={() => handleEnableSection("company")} className="px-3 py-2.5">
                            <FileText className="mr-2 h-4 w-4 text-muted-foreground" />
                            Insert company section
                          </CommandItem>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span>
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={handleDeepResearch}
                          disabled={!minimumContextAvailable}
                          className={cn(
                            minimumContextAvailable
                              ? UI_BUTTON_STYLES.accentIcon
                              : "h-10 w-10 rounded-2xl border border-transparent bg-transparent text-muted-foreground/50"
                          )}
                          aria-label="Run account enrichment"
                        >
                          <Sparkles className="h-4 w-4" />
                        </Button>
                      </span>
                    </TooltipTrigger>
                    <TooltipContent className="rounded-lg">
                      {minimumContextAvailable
                        ? "Research the company, industry, and likely buying context"
                        : "Add a company, website, or attachment before running research"}
                    </TooltipContent>
                  </Tooltip>

                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleVoiceInput}
                        className={cn(
                          UI_BUTTON_STYLES.icon,
                          state.isRecording && "text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300"
                        )}
                        aria-pressed={state.isRecording}
                        aria-label={state.isRecording ? "Stop voice input" : "Start voice input"}
                      >
                        <Mic className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="rounded-lg">
                      {state.isRecording ? "Stop dictation" : "Dictate the setup prompt"}
                    </TooltipContent>
                  </Tooltip>
                </div>

                <div className="flex items-center gap-2">
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        type="button"
                        variant="ghost"
                        size="icon"
                        onClick={handleStrengthen}
                        className={UI_BUTTON_STYLES.accentIcon}
                        aria-label="Strengthen setup prompt"
                      >
                        <Wand2 className="h-4 w-4" />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent className="rounded-lg">Improve prompt structure and fill missing setup sections</TooltipContent>
                  </Tooltip>

                  <Button
                    type="submit"
                    size="sm"
                    disabled={!submitEnabled || state.isSubmitting}
                    className={UI_BUTTON_STYLES.primary}
                  >
                    {state.isSubmitting ? "Launching..." : "Launch Intelligence"}
                    <ArrowUp className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>

            <SuggestionsRail onEnableSection={handleEnableSection} onCompliance={handleComplianceChip} />

            <div id={statusId} aria-live="polite" aria-atomic="true" className="sr-only">
              {liveMessage}
            </div>
          </form>
        </div>
      </WorkflowLayout>
    </TooltipProvider>
  )
}

type SettingsSwitchProps = {
  id: string
  label: string
  checked: boolean
  onCheckedChange: (checked: boolean) => void
}

function SettingsSwitch({ id, label, checked, onCheckedChange }: SettingsSwitchProps) {
  return (
    <div className="flex items-center justify-between gap-3">
      <Label htmlFor={id} className="text-sm font-medium text-foreground">
        {label}
      </Label>
      <Switch id={id} checked={checked} onCheckedChange={onCheckedChange} />
    </div>
  )
}

type ChipButtonProps = {
  icon: React.ComponentType<{ className?: string }>
  label: string
  onClick: () => void
}

function ChipButton({ icon: Icon, label, onClick }: ChipButtonProps) {
  return (
    <Button
      type="button"
      variant="outline"
      onClick={onClick}
      className={UI_BUTTON_STYLES.chip}
    >
      <Icon className="mr-2 h-3.5 w-3.5 shrink-0" />
      <span className="truncate sm:whitespace-normal">{label}</span>
    </Button>
  )
}
