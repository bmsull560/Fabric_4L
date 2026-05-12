# Runbook: StaleGroundTruthObjects

## Overview

Ground truth objects (L5) that are stale indicate the knowledge graph has drifted from verified reality. This impacts AI system reliability, model training quality, and decision accuracy. Stale objects must be refreshed through re-extraction or manual verification.

## Trigger

- **Alert:** `StaleGroundTruthObjects`
- **Condition:** `layer5_stale_objects_detected > 10` for 5 minutes
- **Dashboard:** [Ground Truth Quality](../../monitoring/grafana/dashboards/ground-truth-quality.json)

## Impact

- **Severity:** P2 - Data quality degradation
- **Immediate Impact:** AI responses may use outdated facts, model predictions degrade
- **Cascading Impact:** Compound drift across dependent entities, audit trail gaps
- **Business Impact:** Decreased trust in AI-generated insights, potential compliance issues

## Diagnosis

### 1. Identify Stale Objects

```bash
# Query Layer 5 API for stale objects
curl -s "https://api.valuefabric.io/v1/ground-truth/stale?limit=20" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.objects[] | {id, type, last_verified, age_days}'

# Check staleness distribution by entity type
curl -s "https://api.valuefabric.io/v1/ground-truth/stale/stats" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.by_type'
```

### 2. Verify Extraction Pipeline Health

```bash
# Check L2 extraction job status
kubectl get jobs -n value-fabric -l app=layer2-extraction

# Check for recent extraction failures
kubectl logs -n value-fabric -l app=layer2-extraction --since=24h | grep -i "error\|fail" | tail -20

# Verify queue depth
redis-cli -h $REDIS_HOST LLEN extraction_queue
```

### 3. Analyze Staleness Patterns

```bash
# Check staleness by source/provider
curl -s "https://api.valuefabric.io/v1/ground-truth/stale/stats" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.by_source'

# Identify oldest stale objects
curl -s "https://api.valuefabric.io/v1/ground-truth/stale?sort=oldest&limit=10" \
  -H "Authorization: Bearer $API_TOKEN"
```

## Immediate Containment

### 1. Pause Affected Workflows (if critical)

```bash
# Identify workflows using stale entities
curl -s "https://api.valuefabric.io/v1/workflows/active" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.workflows[] | select(.uses_stale_entities == true) | .id'

# Pause high-risk workflows temporarily
curl -X POST "https://api.valuefabric.io/v1/workflows/{workflow_id}/pause" \
  -H "Authorization: Bearer $API_TOKEN" \
  -d '{"reason": "stale_ground_truth_objects"}'
```

### 2. Trigger Emergency Re-extraction

```bash
# Queue re-extraction for stale high-priority objects
curl -X POST "https://api.valuefabric.io/v1/ground-truth/refresh" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "object_ids": ["obj-001", "obj-002"],
    "priority": "high",
    "force": true
  }'

# Bulk refresh all stale objects older than 7 days
curl -X POST "https://api.valuefabric.io/v1/ground-truth/refresh-stale" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "max_age_days": 7,
    "batch_size": 100
  }'
```

## Remediation

### 1. Fix Extraction Pipeline Issues

```bash
# Check L1-L2 pipeline connectivity
kubectl get pods -n value-fabric | grep -E "layer1|layer2"

# Restart stuck extraction workers
kubectl rollout restart deployment/layer2-extraction -n value-fabric

# Clear stuck queue items (if poison messages suspected)
redis-cli -h $REDIS_HOST LRANGE extraction_queue 0 10 | head -5
```

### 2. Manual Verification for Critical Objects

```bash
# Get list of critical stale objects
curl -s "https://api.valuefabric.io/v1/ground-truth/stale?critical=true" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.objects[] | .id'

# Mark verified objects as fresh (after manual check)
curl -X POST "https://api.valuefabric.io/v1/ground-truth/{object_id}/verify" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "verified_by": "oncall-engineer",
    "method": "manual",
    "confidence": 0.95
  }'
```

### 3. Root Cause Analysis

```bash
# Check extraction success rate over time
curl -s "https://api.valuefabric.io/v1/metrics/extraction?range=7d" \
  -H "Authorization: Bearer $API_TOKEN" | jq '.success_rate_by_day'

# Identify sources with degraded extraction
kubectl logs -n value-fabric -l app=layer2-extraction --since=7d | \
  grep -oP 'source:\s*\K[^\s]+' | sort | uniq -c | sort -rn | head -10
```

## Rollback

If re-extraction causes issues:

```bash
# Check extraction job logs for failures
kubectl logs -n value-fabric job/batch-extraction-$(date +%Y%m%d) | tail -50

# Restore from L5 backup if available
# (Contact platform team for backup restore procedure)

# Resume paused workflows
curl -X POST "https://api.valuefabric.io/v1/workflows/{workflow_id}/resume" \
  -H "Authorization: Bearer $API_TOKEN"
```

## Validation

```bash
# Verify stale count decreasing
curl -s "https://api.valuefabric.io/v1/metrics/ground-truth/stale-count" \
  -H "Authorization: Bearer $API_TOKEN"

# Check alert cleared (stale_objects < 10)
curl -s "https://api.valuefabric.io/v1/health/layer5" | jq '.stale_object_count'

# Spot-check refreshed objects
curl -s "https://api.valuefabric.io/v1/ground-truth/{object_id}" \
  -H "Authorization: Bearer $API_TOKEN" | jq '{id, last_verified, staleness_hours}'

# Verify dependent AI workflows functioning
curl -s "https://api.valuefabric.io/v1/workflows/active" | jq '.workflows | length'
```

## Escalation

| Condition | Action |
|-----------|--------|
| Stale > 100 objects | Page platform on-call `#vf-platform-oncall` |
| Extraction pipeline down | Page data engineering `#vf-data-oncall` |
| Data corruption suspected | Escalate to L5 architect |
| >2 hours to resolve | Engage SRE lead |

## Prevention

- **Staleness thresholds:** Alert at 5 stale objects (vs current 10)
- **Auto-refresh:** Schedule daily re-extraction for objects >30 days old
- **Source health:** Monitor extraction success rate per data source
- **Freshness SLAs:** Define max staleness per entity type (financial: 1h, reference: 7d)
- **Circuit breaker:** Pause AI workflows if >20% input entities are stale

---

**Related Runbooks:**
- [Neo4j Down](neo4j-down.md) - If graph database is the bottleneck
- [Postgres Down](postgres-down.md) - If L5 storage is unavailable

**External References:**
- [Ground Truth Architecture](../../docs/layer5-architecture.md)
- [Extraction Pipeline Docs](../../docs/layer2-extraction.md)
- [Layer 5 Observability Schema](../../../reference/layer5-observability-schema.md)
