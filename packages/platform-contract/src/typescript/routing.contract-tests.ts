import type {
  AccessDecision,
  RouteGuardResult,
  RouteTier,
  WorkspaceDomain,
} from "@fabric/platform-contract/routing";

const allowed: AccessDecision = { allowed: true };
const denied: AccessDecision = { allowed: false, reason: "tier-mismatch" };
const guard: RouteGuardResult = {
  allowed: false,
  redirectTo: "/login",
  reason: "auth-required",
};
const domain: WorkspaceDomain = "studio";
const tier: RouteTier = "admin";

void allowed;
void denied;
void guard;
void domain;
void tier;
