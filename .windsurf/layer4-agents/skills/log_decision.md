---
description: Log agent decisions with context and reasoning
---

# Decision Logger

Use this skill to log agent decisions with full context and reasoning for auditability.

## Parameters

- `decision_id`: Unique identifier for the decision (string, required)
- `decision_type`: Type of decision made (string, required)
- `context`: Full context at time of decision (object, required)
- `reasoning`: Reasoning chain that led to decision (string, required)
- `outcome`: Result of the decision (string, required)
- `confidence`: Confidence score 0.0-1.0 (default: 1.0)

## Steps

1. Capture decision metadata (timestamp, agent, version)
2. Serialize context and reasoning
3. Store in audit log with tamper-evident hash
4. Link to related decisions and workflows
5. Return confirmation with log entry ID

## Output

Log entry confirmation:
- Log entry ID
- Timestamp
- Tamper-evident hash
- Links to related entries

## Example Use

"Log the decision to escalate this business case due to low confidence"
