import type { AgentOutputEnvelope, ContractValidationResult } from "@fabric/platform-contract/agent-contracts";
import {
  SEMANTIC_CONTRACT_VERSION,
  isBlockingContractViolation,
  validateAgentOutputEnvelope,
  validateMemoryReference,
  validateToolInvocationEnvelope,
  validateWorkflowTransitionEnvelope,
} from "@fabric/platform-contract/agent-contracts";

const envelope: AgentOutputEnvelope<{ answer: string }> = {
  agentType: "ConversationAgent",
  output: { answer: "Phase 2 semantic metadata is present." },
  provenance: {
    tenantId: "tenant-123",
    traceId: "trace-123",
    workflowId: "workflow-123",
    sourceLayer: "layer4-agents",
  },
  contractVersions: {
    semanticContract: SEMANTIC_CONTRACT_VERSION,
    agentRegistry: "1.0.0",
  },
  prompt: {
    promptId: "conversation-system-prompts",
    version: "1.0.0",
  },
  confidence: 0.91,
  explainability: { summary: "validated" },
  evidence: [{ source: "agent-registry" }],
  emittedAt: new Date().toISOString(),
};

const validResult: ContractValidationResult<AgentOutputEnvelope> = validateAgentOutputEnvelope(envelope);
const missingProvenanceResult = validateAgentOutputEnvelope({ agentType: "ConversationAgent" }, "strict");
const failedToolResult = validateToolInvocationEnvelope(
  {
    toolName: "platform-tools.search",
    toolVersion: "1.0.0",
    callerAgentType: "ConversationAgent",
    success: false,
    provenance: { tenantId: "tenant-123", traceId: "trace-123" },
  },
  "strict"
);
const workflowResult = validateWorkflowTransitionEnvelope({
  workflowType: "roi_analysis",
  workflowId: "workflow-123",
  sourceState: "started",
  targetState: "completed",
  triggeringAgentType: "ConversationAgent",
  tenantId: "tenant-123",
  traceId: "trace-123",
});
const memoryResult = validateMemoryReference({
  memoryId: "memory-123",
  memoryType: "conversation_context",
  tenantId: "tenant-123",
  traceId: "trace-123",
});
const blocks: boolean = isBlockingContractViolation(missingProvenanceResult) || isBlockingContractViolation(failedToolResult);

void validResult;
void workflowResult;
void memoryResult;
void blocks;
