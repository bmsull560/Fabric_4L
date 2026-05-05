# P2 Production-Readiness Governance and Commercialization

The readiness assessment identifies billing/metering, SLA/SLO operations, and SOC2/ISO-style control evidence as P2 concerns. These items are business-critical, but they depend on external providers, signed customer commitments, production telemetry, and audit ownership before they can be marked production PASS.

## P2 Gate Matrix

| Gate | Repository foundation | Current status | Production evidence still required |
|---|---|---|---|
| Billing and metering | Billing models, service code, migrations, tests, billing evidence script, and `config/production-readiness/billing_metering_policy.json`. | Foundation ready; provider reconciliation required. | Usage ledger, duplicate handling, webhook signature validation, invoice reconciliation, and budget-alert delivery. |
| SLA, SLI, and SLO operations | SLO documentation directories, monitoring assets, alerting rules, and `config/production-readiness/slo_sla_policy.json`. | Foundation ready; live dashboard evidence required. | Live SLI dashboards, burn-rate alerts, release-freeze exercise, customer communication template, and post-incident review evidence. |
| SOC2 and ISO control readiness | Compliance documentation, control scripts, security workflows, audit-evidence workflows, runbook validation, and `config/production-readiness/compliance_control_policy.json`. | Foundation ready; auditor or compliance-owner signoff required. | Control ownership, access review, change-management sample, incident drill, evidence retention, and scope signoff. |

## Commercial Assertion Rule

Commercial and compliance readiness must never be inferred from repository configuration alone. Billing readiness requires provider-backed reconciliation, SLA readiness requires live telemetry and customer-facing commitments, and compliance readiness requires assigned owners with retained evidence reviewed by a qualified compliance owner or auditor.
