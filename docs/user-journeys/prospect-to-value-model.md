# User Journey: Prospect to Value Model

This document provides a detailed step-by-step guide for users navigating from initial prospect input through intelligence generation, hypothesis development, and value model building in the Value Fabric platform.

## Overview

This user journey covers the complete end-to-end workflow for creating a value case for a prospect, from entering initial company information to generating a quantitative value model with ROI analysis.

**Target Users**: Sales representatives, business analysts, value engineers  
**Estimated Time**: 15-30 minutes for a complete workflow  
**Prerequisites**: User account with appropriate permissions, active subscription

## Phase 1: Prospect Input

### Step 1.1: Navigate to Prospect Setup

1. Log in to Value Fabric
2. Navigate to `/workflow/prospect` or click "New Value Case" from the home page
3. The ProspectSetup page loads with the ProspectPromptBuilder component

### Step 1.2: Enter Company Information

**Company Details Section**:

1. Click the company search icon or type company name in the textarea
2. Select from existing companies or enter a new company:
   - **Company Name**: e.g., "Medtronic"
   - **Website**: e.g., "medtronic.com"
   - **Industry**: e.g., "Medical Devices"

**Tip**: Use the company selector dropdown to quickly choose from existing accounts in your CRM.

### Step 1.3: Add Buying Context

**Buying Context Section**:

1. Click "Add buying context" or type directly in the textarea
2. Provide context about the buying situation:
   - **Buying context**: e.g., "New product launch readiness across distributed field teams"
   - **Why this account now**: e.g., "Need stronger rep ramp, compliant messaging, and executive discovery prep"
   - **Known initiative or trigger**: e.g., "Field launch enablement refresh"

**Tip**: The more specific the buying context, the better the AI can tailor the intelligence generation.

### Step 1.4: Specify Stakeholders

**Stakeholders Section**:

1. Click "Add stakeholders" or type directly in the textarea
2. Identify key buying committee members:
   - **Economic buyer**: e.g., "VP Sales"
   - **Business champion**: e.g., "Sales Enablement Leader"
   - **Technical evaluator**: e.g., "RevOps / IT"
   - **Compliance / legal**: e.g., "Regulatory and legal operations"

**Tip**: Understanding the buying committee helps tailor messaging and identify decision-makers.

### Step 1.5: Define Business Pain

**Business Pain Section**:

1. Click "Add business pain" or type directly in the textarea
2. List current challenges:
   - **Known or suspected business pains**:
     - e.g., "Rep onboarding is slow for complex offerings"
     - e.g., "Messaging consistency is difficult across field teams"
     - e.g., "Launch content is fragmented across systems"
   - **Current friction**:
     - e.g., "Multiple systems create version confusion"
     - e.g., "Coaching quality varies by manager"
   - **Desired business outcome**:
     - e.g., "Faster rep ramp time"
     - e.g., "More consistent compliant messaging"
     - e.g., "Better launch readiness"

**Tip**: Focus on quantifiable pain points that can be measured and addressed with your solution.

### Step 1.6: Select Deliverable Type

**Deliverable Section**:

1. Click "Add deliverable" or use the settings popover
2. Select the primary deliverable type:
   - **Account brief**: Comprehensive account overview
   - **Discovery prep**: Questions and talking points for discovery calls
   - **Value hypotheses**: AI-generated value hypotheses for validation
   - **Executive summary**: Executive-level summary and messaging

**Tip**: Select "Value hypotheses" if you plan to build a quantitative value model later in the workflow.

### Step 1.7: Configure Analysis Settings

**Settings Popover**:

1. Click the settings icon (gear) to open the settings popover
2. Configure analysis parameters:
   - **Mode**:
     - **Fast**: Quick analysis with limited depth
     - **Balanced** (default): Standard analysis depth
     - **Deep**: Comprehensive deep research
   - **Enrichment depth**:
     - **Light**: Minimal external data
     - **Standard** (default): Standard enrichment
     - **Deep**: Maximum enrichment
   - **Flags**:
     - **Use uploaded files**: Include attached documents
     - **Use prior account context**: Leverage existing account data
     - **Run web enrichment**: Fetch external web data
     - **Compliance-sensitive mode**: Enhanced compliance checks for regulated industries

**Tip**: Use "Deep" mode for complex, high-value opportunities. Use "Fast" mode for quick prospecting.

### Step 1.8: Submit and Navigate

1. Review the assembled prompt in the textarea
2. Click the "Submit" button (primary button in the bottom right)
3. Wait for account creation (status message: "Launching intelligence...")
4. System automatically navigates to `/intelligence/:accountId/signals`

**Troubleshooting**:
- If submission fails, check that required fields (company name) are filled
- If navigation doesn't occur, manually navigate to `/accounts` and select the created account

## Phase 2: Intelligence Workspace

### Step 2.1: Explore the Intelligence Workspace

Upon navigation, you'll see the IntelligenceWorkspace with:

- **Header**: Account name, industry, revenue
- **Progress Rail**: Visual indicator of workflow completion
- **Tab Navigation**: 13 tabs organized by category
- **Tab Content**: Active tab's content area
- **Right Rail**: Agent assistance and workflow guidance

### Step 2.2: Review Signals Tab (Default)

**Signals Tab** (`/intelligence/:accountId/signals`):

1. View raw market signals and triggers detected for the account
2. Review signal categories:
   - Company announcements
   - Industry trends
   - Competitive movements
   - Technology changes
3. Click on signals to view details

**Tip**: Signals provide the foundation for hypothesis generation. Review them before proceeding.

### Step 2.3: Review Account Enrichment

**Account Enrichment Tab** (`/intelligence/:accountId/enrichment`):

1. Click "Account Enrichment" tab
2. View firmographic data:
   - Company size, revenue, growth
   - Employee count and locations
   - Technology stack
   - Recent news and events

**Tip**: Use enrichment data to validate your understanding of the prospect's situation.

### Step 2.4: Review Stakeholders

**Stakeholders Tab** (`/intelligence/:accountId/stakeholders`):

1. Click "Stakeholders" tab
2. View identified buyer personas:
   - Role and seniority
   - Priorities and concerns
   - Influence level
   - Recommended messaging approach

**Tip**: Compare AI-identified stakeholders with your known contacts to identify gaps.

## Phase 3: Hypothesis Generation

### Step 3.1: Navigate to Hypotheses Tab

1. Click "Value Hypotheses" tab
2. View the HypothesesTab component

### Step 3.2: Generate Hypotheses

**Initial State**:

- If no hypotheses exist, you'll see an empty state with a "Generate Hypotheses" button
- If hypotheses exist from previous runs, they'll be displayed in a list

**Generate Action**:

1. Click the "Generate Hypotheses" button (sparkle icon)
2. Wait for generation (button shows "Generating..." with spinner)
3. System calls `POST /api/v1/value-hypotheses/generate`
4. Hypotheses appear in the list with confidence scores

**Expected Output**:

- 10-20 hypotheses generated
- Each hypothesis includes:
  - Value driver name
  - Hypothesis text
  - Confidence score (0-100%)
  - Signal count
  - Product mapping
  - Status (draft)

**Tip**: Higher confidence scores (>70%) indicate stronger signal-to-product alignment.

### Step 3.3: Review Hypothesis Details

1. Click on a hypothesis card to select it
2. View details in the right rail:
   - Full hypothesis text
   - Confidence percentage
   - Product ID
   - Status
   - Evidence count
   - Validation notes (if any)

**Tip**: Review the signal→product mapping to understand the evidence supporting each hypothesis.

### Step 3.4: Validate Hypotheses

**Validation Process**:

1. Select a hypothesis with status "draft"
2. Review the hypothesis text and evidence
3. Click "Validate" (checkmark icon) or "Reject" (X icon)
4. System calls `POST /api/v1/value-hypotheses/:id/validate`
5. Hypothesis status updates to "validated" or "rejected"
6. Add validation notes in the right rail (optional)

**Validation Criteria**:

- **Validate**: Hypothesis is accurate, relevant, and supported by evidence
- **Reject**: Hypothesis is inaccurate, irrelevant, or not supported

**Tip**: Focus validation on hypotheses that align with your solution's unique value proposition.

### Step 3.5: Filter Hypotheses

1. Use the status filter buttons:
   - **All**: Show all hypotheses
   - **Draft**: Show unvalidated hypotheses
   - **Validated**: Show approved hypotheses
   - **Rejected**: Show rejected hypotheses
   - **Converted**: Show hypotheses converted to value model

**Tip**: Filter to "Validated" to see hypotheses ready for value model building.

## Phase 4: Value Model Building

### Step 4.1: Navigate to Value Model Tab

1. Click "Value Model" tab
2. View the ValueModelTab component

**Route Note**: Value Model is available at both:
- `/intelligence/:accountId/value-model` (new workspace)
- `/studio/:accountId/value-model` (legacy workspace)

### Step 4.2: Review Value Lines

**Initial State**:

- If no value lines exist, system auto-generates them from validated hypotheses
- Value lines display in a table with scenarios

**Value Line Structure**:

Each value line includes:
- **Driver**: Business value driver name
- **Conservative**: Conservative scenario value ($)
- **Expected**: Expected scenario value ($)
- **Optimistic**: Optimistic scenario value ($)
- **Source**: Evidence or hypothesis source

### Step 4.3: Select Scenario

1. Use the scenario selector buttons:
   - **Conservative**: Pessimistic assumptions
   - **Expected** (default): Realistic assumptions
   - **Optimistic**: Optimistic assumptions

**Impact**: Scenario selection affects:
- Total annual value calculation
- Hard savings vs strategic value breakdown
- ROI calculation results

**Tip**: Use "Expected" for internal planning, "Conservative" for customer-facing proposals.

### Step 4.4: Toggle Strategic Value

1. Check/uncheck "Include strategic value" checkbox
2. View updated metrics:
   - **Total Annual Value**: Sum of all value lines
   - **Hard Savings**: Tangible, quantifiable savings
   - **Strategic Value**: Intangible, strategic benefits
   - **Value Lines**: Number of value lines

**Tip**: Include strategic value for executive audiences, exclude for finance-focused audiences.

### Step 4.5: Calculate ROI

**Calculate Action**:

1. Click "Calculate ROI" button (calculator icon)
2. System calls `POST /api/v1/roi/calculate` with:
   - Deal size (total value)
   - Annual benefit
   - Implementation cost (30% of deal size by default)
   - Discount rate (10% by default)
   - Time horizon (3 years by default)
3. View ROI summary card:
   - **NPV**: Net Present Value
   - **IRR**: Internal Rate of Return
   - **Payback**: Payback period in months
   - **3-Year ROI**: Total ROI percentage

**ROI Interpretation**:

- **NPV > $0**: Investment creates value
- **IRR > 10%**: Return exceeds cost of capital
- **Payback < 18 months**: Quick payback is favorable
- **3-Year ROI > 300%**: Strong return on investment

**Tip**: Adjust implementation cost and discount rate in the Variables modal for accurate ROI.

### Step 4.6: View Industry Benchmarks

**Benchmark Display**:

1. System automatically fetches industry benchmarks
2. View benchmark comparison card:
   - **Avg ROI**: Industry average ROI percentage
   - **Avg Payback**: Industry average payback period
   - **Avg NPV**: Industry average NPV
   - **Sample Size**: Number of companies in benchmark

**Benchmark Comparison**:

- Compare your calculated ROI against industry averages
- Identify if your value proposition is above or below market
- Use benchmarks to validate assumptions

**Tip**: If your ROI is significantly below industry average, review value line assumptions.

### Step 4.7: Edit Variables (Optional)

1. Click "Variables" button (settings icon)
2. Edit calculation parameters:
   - Implementation cost percentage
   - Discount rate
   - Time horizon years
   - Value line multipliers
3. Recalculate ROI with new variables

**Tip**: Use variables to model different scenarios and sensitivity analysis.

## Phase 5: Output Generation

### Step 5.1: Generate Executive Value Case

1. Click "Executive Value Case" tab
2. View generated narrative:
   - Executive summary
   - Problem statement
   - Solution overview
   - Value proposition
   - ROI analysis
   - Next steps

**Tip**: Review and edit the narrative to align with your messaging and tone.

### Step 5.2: Generate Realization Plan

1. Click "Realization Plan" tab
2. View generated plan:
   - Implementation phases
   - Milestones and timelines
   - Owners and responsibilities
   - Success metrics
   - Risk mitigation

**Tip**: Customize the realization plan based on customer-specific requirements.

## Troubleshooting

### Common Issues

**Issue**: Account creation fails on submit

**Solution**:
- Check that company name is filled
- Verify network connectivity
- Check API service status
- Try with a simpler prompt first

**Issue**: Hypotheses generation fails

**Solution**:
- Ensure account has enrichment data
- Check that product portfolio is configured
- Verify signals are detected
- Try with "Fast" mode first

**Issue**: ROI calculation returns error

**Solution**:
- Ensure value lines exist
- Check that industry is set on account
- Verify ROI calculator service is running
- Try with default variables

**Issue**: Navigation doesn't occur after submit

**Solution**:
- Manually navigate to `/accounts`
- Select the created account
- Navigate to intelligence workspace
- Check browser console for errors

### Performance Tips

- Use "Fast" mode for quick prospecting
- Use "Balanced" mode for standard workflows
- Use "Deep" mode for high-value opportunities
- Cache frequently used companies
- Validate hypotheses in batches
- Use scenario toggles for quick comparisons

## Best Practices

### Phase 1: Prospect Input

- Be specific about buying context and business pain
- Identify all key stakeholders in the buying committee
- Select the appropriate deliverable type for your use case
- Use compliance-sensitive mode for regulated industries

### Phase 2: Intelligence Workspace

- Review signals before generating hypotheses
- Validate enrichment data against your knowledge
- Compare AI-identified stakeholders with your contacts
- Use the right rail for agent assistance

### Phase 3: Hypothesis Generation

- Generate hypotheses after enrichment is complete
- Focus validation on high-confidence hypotheses
- Add validation notes for rejected hypotheses
- Filter by status to track progress

### Phase 4: Value Model Building

- Start with "Expected" scenario for planning
- Include strategic value for executive audiences
- Compare ROI against industry benchmarks
- Use variables for sensitivity analysis

### Phase 5: Output Generation

- Customize narratives for your brand voice
- Tailor realization plans to customer context
- Include specific success metrics
- Align next steps with sales process

## Related Documentation

- [Core User Workflow](../workflows/core-user-workflow.md)
- [Data Intelligence Layer Architecture](../../value-fabric/docs/data-intelligence-layer.md)
- [Three-Tier UX Model](../../specs/three_tier_ux_model.md)
- [API Reference](../API_REFERENCE.md)
