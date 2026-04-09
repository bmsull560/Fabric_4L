---
description: Request human review or approval
---

# Human Escalator Workflow

Use this workflow to escalate to human review when needed.

## When to Use

- Confidence < 0.8 on critical claims
- ROI projection > $10M
- Conflicting information detected
- First-time use case

## Parameters

- `reason`: LOW_CONFIDENCE | HIGH_IMPACT | AMBIGUITY | POLICY_VIOLATION
- `context`: Explanation of what needs review (string, required)
- `urgency`: LOW | MEDIUM | HIGH | CRITICAL (default: MEDIUM)
- `required_approvers`: List of roles or user IDs (optional)

## Steps

1. Document the issue requiring escalation
2. Categorize reason and urgency
3. Route to appropriate approvers
4. Generate ticket ID
5. Provide estimated response time

## Output

Escalation ticket:
- Ticket ID for tracking
- Issue description and context
- Assigned approvers
- Estimated response time
- Urgency level and priority
