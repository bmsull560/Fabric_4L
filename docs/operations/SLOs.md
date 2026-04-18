# Service Level Objectives (SLOs) for Fabric_4L

## Overview

These SLOs define the target reliability and performance for the Fabric_4L platform. They are the basis for alerting, error budgets, and prioritization of reliability work.

## Platform-wide SLOs

### Availability
- **SLO:** 99.9% uptime across all layers
- **Error Budget:** 0.1% downtime = ~43 minutes per month
- **Measurement:** HTTP 200 responses / total requests
- **Window:** 30 days

### Latency
- **SLO:** p99 < 2 seconds for API requests
- **Measurement:** histogram_quantile(0.99, http_request_duration_seconds)
- **Window:** 7 days

## Layer-specific SLOs

### Layer 1 - Ingestion

| Metric | SLO | Measurement | Window |
|--------|-----|-------------|--------|
| Availability | 99.9% | HTTP 200 rate | 30 days |
| Task Success Rate | 99.5% | successful_tasks / total_tasks | 7 days |
| Task Latency | p99 < 5 min | Celery task duration | 7 days |
| Queue Depth | < 500 tasks | celery_queue_length | Real-time |

**Business Metric:**
- Documents ingested per hour: > 100 docs/hour (peak)

### Layer 2 - Extraction

| Metric | SLO | Measurement | Window |
|--------|-----|-------------|--------|
| Availability | 99.5% | HTTP 200 rate | 30 days |
| Extraction Success | 98% | Successful extractions / total | 7 days |
| LLM Cost | <$100/hour | sum(llm_cost_total[1h]) | 24 hours |
| Latency | p99 < 30s | Extraction duration | 7 days |

### Layer 3 - Knowledge Graph

| Metric | SLO | Measurement | Window |
|--------|-----|-------------|--------|
| Availability | 99.9% | Neo4j connection health | 30 days |
| Query Latency | p99 < 500ms | Graph query duration | 7 days |
| Search Latency | p99 < 1s | Vector search duration | 7 days |

### Layer 4 - Agents

| Metric | SLO | Measurement | Window |
|--------|-----|-------------|--------|
| Workflow Success | 95% | Completed / total workflows | 7 days |
| Workflow Duration | p99 < 5 min | Workflow execution time | 7 days |
| LLM Cost per Workflow | <$0.50 | Cost per workflow | 7 days |
| Checkpoint Reliability | 99.9% | Successful checkpoints | 30 days |

### Layer 5 - Ground Truth

| Metric | SLO | Measurement | Window |
|--------|-----|-------------|--------|
| Availability | 99.5% | HTTP 200 rate | 30 days |
| Evaluation Pass Rate | > 85% | Evaluations passing threshold | 7 days |

### Layer 6 - Benchmarks

| Metric | SLO | Measurement | Window |
|--------|-----|-------------|--------|
| Availability | 99% | HTTP 200 rate | 30 days |
| Report Generation | < 30s | Benchmark report duration | Real-time |

## Error Budget Policy

### Burn Rate Alerts

We use multi-window, multi-burn-rate alerting to catch SLO violations early:

| Burn Rate | Alert After | Lookback Window | Budget Exhausted In |
|-----------|-------------|-----------------|---------------------|
| 5x | 2 minutes | 1 hour | 6 hours |
| 2x | 15 minutes | 6 hours | 3 days |

### Error Budget Consumption

If error budget is consumed faster than expected:

1. **> 50% consumed in 1 week:** Freeze new feature development, focus on reliability
2. **> 75% consumed in 2 weeks:** Halt all non-essential deployments
3. **> 90% consumed in 3 weeks:** Emergency reliability sprint, manual approval for all changes

## Alert Severity Levels

### Critical (P1)
- **Response Time:** 15 minutes
- **Resolution Time:** 2 hours
- **Examples:** Service down, data loss, security incident, cost > $100/hour
- **Notification:** PagerDuty + Slack #alerts-critical

### Warning (P2)
- **Response Time:** 1 hour
- **Resolution Time:** 8 hours
- **Examples:** High latency, elevated errors, queue backlog
- **Notification:** Slack #alerts-warning

### Info (P3)
- **Response Time:** 4 hours
- **Resolution Time:** 24 hours
- **Examples:** Minor performance degradation, non-critical failures
- **Notification:** Slack #alerts-info

## On-Call Rotation

### Primary On-Call
- **Platform Team:** 24/7 coverage
- **Handoff:** Daily at 9 AM EST
- **Escalation:** Manager after 30 minutes of no response

### Secondary On-Call
- **FinOps Team:** Business hours (9-5 EST)
- **ML Team:** Business hours for model issues

## Runbooks

Every alert must have a runbook. Runbooks are stored in:
- Wiki: https://wiki.internal/runbooks/
- Repo: `docs/runbooks/`

### Required Runbooks

1. **High Error Rate** - `high-error-rate.md`
2. **Service Down** - `service-down.md`
3. **High LLM Cost** - `high-llm-cost.md`
4. **Celery Queue Backlog** - `celery-backlog.md`
5. **Database Pool Exhausted** - `database-pool.md`
6. **Disk Space Low** - `disk-space.md`

## Measuring SLOs

### Prometheus Queries

**Availability:**
```promql
sum(rate(http_requests_total{status=~"2.."}[30d]))
/ sum(rate(http_requests_total[30d]))
```

**Latency (p99):**
```promql
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket[7d])) by (le)
)
```

**Error Budget Consumption:**
```promql
1 - (
  sum(rate(http_requests_total{status=~"2.."}[30d]))
  / sum(rate(http_requests_total[30d]))
) - 0.001  # 0.001 = 99.9% SLO
```

## SLO Review Process

### Monthly Review
- Review SLO compliance
- Analyze error budget consumption
- Adjust thresholds based on data
- Update runbooks

### Quarterly Review
- Re-evaluate SLO targets
- Adjust based on business needs
- Plan reliability improvements

## Contacts

| Team | Slack | PagerDuty |
|------|-------|-----------|
| Platform | #platform-team | pagerduty-platform |
| FinOps | #finops | pagerduty-finops |
| ML | #ml-team | pagerduty-ml |
| Data | #data-team | pagerduty-data |

## References

- Google SRE Book: https://sre.google/sre-book/table-of-contents/
- SLO Workshop: https://sre.google/workbook/slo-document/
