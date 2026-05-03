# Data Model

## Core Entities

### Tenant
- `id`, `name`, `defaultValuePackId`, `plan`, `status`

### Account
- `id`, `tenantId`, `name`, `industry`, `segment`, `website`, `annualRevenue`, `employeeCount`, `crmStage`, `valuePackId`, `summary`, `createdAt`, `updatedAt`

### Stakeholder
- `id`, `accountId`, `name`, `title`, `personaId`, `department`, `priorities`, `pains`, `influenceLevel`, `decisionRole`

### Signal
- `id`, `accountId`, `sourceDocumentId`, `signalType`, `title`, `description`, `severity`, `confidence`, `extractedText`, `evidenceIds`, `mappedDriverIds`, `status`

### Evidence
- `id`, `accountId`, `sourceDocumentId`, `title`, `excerpt`, `sourceType`, `url`, `page`, `confidence`, `tags`, `supportsClaimIds`

### ValueHypothesis
- `id`, `accountId`, `title`, `personaId`, `driverIds`, `painSignalIds`, `claim`, `expectedOutcome`, `discoveryQuestions`, `confidence`, `status`

### ValueDriver
- `id`, `accountId`, `name`, `category`, `description`, `linkedSignals`, `linkedEvidence`, `levers`, `confidence`

### ValueLever
- `id`, `driverId`, `name`, `description`, `formulaId`, `baselineMetric`, `targetMetric`, `unit`, `assumptionIds`, `evidenceIds`

### Formula
- `id`, `valuePackId`, `name`, `category`, `expression`, `inputs`, `outputs`, `assumptions`, `benchmarkIds`, `validationStatus`

### Scenario
- `id`, `accountId`, `name`, `assumptions`, `roiSummary`, `paybackMonths`, `npv`, `irr`, `confidence`

### ROICalculation
- `id`, `accountId`, `scenarioId`, `revenueUplift`, `costSavings`, `riskReduction`, `totalBenefit`, `solutionCost`, `netBenefit`, `roiPercent`, `paybackMonths`, `calculationTrace`, `evidenceIds`, `assumptionIds`

### BusinessCase
- `id`, `accountId`, `title`, `executiveSummary`, `valueNarrative`, `roiCalculationIds`, `evidenceIds`, `assumptions`, `risks`, `recommendation`, `status`

### GroundTruthObject
- `id`, `tenantId`, `objectType`, `objectId`, `claim`, `validatedBy`, `validationStatus`, `evidenceIds`, `reviewDecisionIds`, `createdAt`

### AgentRun
- `id`, `tenantId`, `accountId`, `workflowType`, `status`, `currentStep`, `checkpointId`, `input`, `output`, `toolResults`, `reviewRequired`, `createdAt`, `updatedAt`

### ToolResult
- `id`, `agentRunId`, `toolName`, `status`, `output`, `error`, `startedAt`, `completedAt`

## Relationships

- Account -> Stakeholders (1:N)
- Account -> Signals (1:N)
- Account -> Evidence (1:N)
- Account -> Hypotheses (1:N)
- Account -> Drivers (1:N)
- Driver -> Levers (1:N)
- Hypothesis -> Drivers (N:M)
- Hypothesis -> Signals (N:M)
- Formula -> ValuePack (N:1)
- ROI Calculation -> Scenario (N:1)
- BusinessCase -> ROI Calculations (1:N)
