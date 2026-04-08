---
description: Detect and fix errors in workflow execution
---

# Self-Correction Workflow

Use this workflow to detect errors during execution and automatically attempt fixes.

## Parameters

- `error_context`: Error message or failure description (string, required)
- `workflow_id`: ID of the workflow that failed (string, required)
- `retry_count`: Number of retry attempts (default: 1)
- `correction_strategy`: RETRY | ADJUST_PARAMS | FALLBACK | ESCALATE (default: RETRY)

## Steps

1. Analyze the error context and type
2. Identify root cause of failure
3. Select appropriate correction strategy
4. Attempt automatic fix:
   - RETRY: Re-run with same parameters
   - ADJUST_PARAMS: Modify parameters based on error
   - FALLBACK: Use alternative workflow
   - ESCALATE: Trigger human escalation
5. Validate the correction
6. Report outcome

## Output

Correction report:
- Original error identified
- Correction strategy applied
- Success/failure of correction
- Final result or escalation status
- Lessons learned for future prevention

## Example Use

"The graph query timed out. Attempt to fix by reducing depth parameter."
