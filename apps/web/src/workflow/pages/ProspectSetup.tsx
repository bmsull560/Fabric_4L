"use client"

import * as React from "react"
import { useNavigation } from "@/hooks/useNavigation"
import { ProspectPromptBuilder } from "@/components/workspace/ProspectPromptBuilder"
import type {
  ProspectPromptBuilderProps,
  ProspectSetupPromptPayload,
  CreateSetupResult,
} from "@/components/workspace/ProspectPromptBuilder"
import { WorkflowLayout } from "../components/WorkflowLayout"
import { useWorkflowStore } from "../store/workflowStore"
import { STEPS } from "../constants"
import { createFeatureLogger } from "@/lib/telemetry"

const log = createFeatureLogger("ProspectSetup")

function resolveNavigationAccountId(
  result: CreateSetupResult,
  selectedCompany?: { accountId?: string }
): string | undefined {
  if (result && typeof result === "object" && "accountId" in result && result.accountId) {
    return result.accountId
  }
  return selectedCompany?.accountId
}

export default function ProspectSetup(props: ProspectPromptBuilderProps) {
  const { navigateTo } = useNavigation()
  const { setProspect, setCurrentStep } = useWorkflowStore()

  const handleBeforeSubmit = React.useCallback(
    (state: { draft: { companyName: string; stakeholders: { economicBuyer: string; champion: string } } }) => {
      const tempId = `temp_${Date.now()}`
      setProspect({
        companyId: tempId,
        companyName: state.draft.companyName || "",
        contactName: state.draft.stakeholders.economicBuyer || state.draft.stakeholders.champion || "",
        contactTitle: "",
      })
    },
    [setProspect]
  )

  const handleCreateSetup = React.useCallback(
    async (payload: ProspectSetupPromptPayload) => {
      const result = props.onCreateSetup ? await props.onCreateSetup(payload) : undefined
      return result
    },
    [props.onCreateSetup]
  )

  const handleNavigateToWorkspace = React.useCallback(
    (path: string, accountId: string) => {
      if (props.onNavigateToWorkspace) {
        props.onNavigateToWorkspace(path, accountId)
      } else {
        navigateTo(path)
      }
    },
    [props.onNavigateToWorkspace, navigateTo]
  )

  const handleFallbackNavigation = React.useCallback(() => {
    setCurrentStep(STEPS.INTELLIGENCE)
    navigateTo("workflow-intelligence")
  }, [setCurrentStep, navigateTo])

  return (
    <WorkflowLayout>
      <ProspectPromptBuilder
        {...props}
        onCreateSetup={handleCreateSetup}
        onNavigateToWorkspace={handleNavigateToWorkspace}
        onBeforeSubmit={handleBeforeSubmit}
        onFallbackNavigation={handleFallbackNavigation}
        getWorkspacePath={(accountId) => `/intelligence/${accountId}/signals`}
      />
    </WorkflowLayout>
  )
}
