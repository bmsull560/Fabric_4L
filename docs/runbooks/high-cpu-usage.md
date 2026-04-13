# HighCPUUsage Runbook

## Severity: warning

## Alert Condition
`layerN_cpu_usage_percent > 80` for 10 minutes.

## Impact
Slow response times, request queuing, and potential timeout cascades.

## Triage Steps
1. Identify the pod or node with high CPU usage.
2. Check if the spike is traffic-driven or caused by a runaway process.
3. Profile the application to find hot code paths.

## Resolution
### Quick Fix
- Scale the affected service horizontally.
- Restart pods if a specific instance is CPU-spinning.
- Temporarily throttle or disable background jobs.

### Root Cause Analysis
- Use CPU profiling to identify inefficient loops or regexes.
- Review recent code changes for algorithmic regressions.

## Escalation
- Page the platform on-call if CPU remains >95% after scaling.
- Contact `#vf-platform-oncall`.

## Prevention
- Optimize hot paths based on profiling data.
- Use auto-scaling policies tied to CPU utilization.
- Add rate limiting to prevent abuse-driven CPU spikes.
