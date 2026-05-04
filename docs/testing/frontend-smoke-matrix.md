# Frontend Critical Test Matrix

## Scope
This matrix defines minimum ownership for critical frontend flows in `frontend/client/src`.

## Smoke flows

| Flow | Test file | Owner area | Risk covered |
|---|---|---|---|
| Login/auth gate redirects unauthenticated users | `frontend/client/src/routes/criticalFlows.smoke.test.tsx` | Routing + auth context | Unauthorized access regressions |
| Workspace shell route load for authenticated users | `frontend/client/src/routes/criticalFlows.smoke.test.tsx` | App shell + route composition | Broken home/workspace bootstrapping |
| End-to-end form interaction (Prospect setup launch) | `frontend/client/src/routes/criticalFlows.smoke.test.tsx` | Workflow intake form | Submit path breakage |

## High-risk behavior primitives

| Primitive behavior | Test file | Why high risk |
|---|---|---|
| Validation disables launch with missing context | `frontend/client/src/components/ProspectSetup.behavior.test.tsx` | Prevents invalid workflow launch |
| Loading state disables launch and communicates progress | `frontend/client/src/components/ProspectSetup.behavior.test.tsx` | Prevents duplicate submit and UX uncertainty |
| Error rendering on failed launch | `frontend/client/src/components/ProspectSetup.behavior.test.tsx` | Ensures failures are visible/actionable |

## Coverage policy (CI enforced)

Coverage thresholds are enforced in `frontend/vite.config.ts`, scoped to `frontend/client/src`.
Initial floor:
- Lines: 35%
- Functions: 35%
- Statements: 35%
- Branches: 25%

Ratcheting policy: increase each threshold incrementally once the suite stabilizes (e.g., +5% per sprint).
