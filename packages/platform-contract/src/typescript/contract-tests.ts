import type { AgentResultEnvelope } from "./agent-result.js";
import type { RouteGuardResult, WorkspaceDomain, RouteTier, AccessDecision } from "./routing.js";
import { useAccountContextStore } from "./stores.js";

const envelope: AgentResultEnvelope = {
  status: "success",
  data: {},
  error: null,
  metadata: {
    trace_id: "t",
    workflow_id: "w",
    tenant_id: "tenant",
    agent_type: "planner",
    started_at: new Date().toISOString(),
    completed_at: new Date().toISOString(),
    duration_ms: 1,
    node_path: ["start"],
  },
};

const guard: RouteGuardResult = { allowed: true };
const domain: WorkspaceDomain = "studio";
const tier: RouteTier = "admin";
const decision: AccessDecision = { allowed: false, reason: "nope" };

useAccountContextStore.getState().setSelectedAccountId("acc-1");
useAccountContextStore.getState().clearSelectedAccountId();

void envelope;
void guard;
void domain;
void tier;
void decision;

// Negative assertions (must keep failing if contract is weakened)
// @ts-expect-error status must be one of success|error|paused
const badStatus: AgentResultEnvelope = { ...envelope, status: "ok" };

// @ts-expect-error Route tier is constrained union
const badTier: RouteTier = "owner";

// @ts-expect-error AccessDecision denied branch requires reason
const badDecision: AccessDecision = { allowed: false };

// @ts-expect-error selected account id setter requires string
useAccountContextStore.getState().setSelectedAccountId(null);

void badStatus;
void badTier;
void badDecision;
