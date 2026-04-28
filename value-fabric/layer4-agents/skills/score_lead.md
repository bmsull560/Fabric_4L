---
name: score_lead
description: Calculates lead score based on profile fit and engagement
---

# Score Lead

Calculate lead score based on company profile fit and engagement data.

## Parameters

- `prospect_id`: string — Prospect ID to score (required)
- `scoring_model`: string — Model to use (default: default)
- `factors`: array — Specific factors to include (optional)

## Steps

1. Fetch prospect data from CRM
2. Calculate company size score
3. Calculate industry fit score
4. Calculate engagement score from interactions
5. Calculate opportunity value score
6. Determine grade and generate recommendations

## Output

Returns ScoreLeadOutput with:
- `score`: Total score 0-100
- `grade`: Letter grade A-F
- `factors`: Breakdown of component scores
- `recommendations`: Suggested actions
