# DiskSpaceCritical Runbook

## Severity: critical

## Alert Condition
`node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.05` for 2 minutes.

## Impact
Imminent disk exhaustion will cause services to fail writes and crash.

## Triage Steps
1. Identify the affected node and mountpoint immediately.
2. Run emergency cleanup: old logs, temp files, Docker volumes.
3. Check if the issue is isolated to one pod or node-wide.

## Resolution
### Quick Fix
- Free space aggressively (logs, caches, tmp).
- Resize the underlying PVC or add a new volume if using cloud storage.
- Evict non-critical pods from the node to reclaim local disk.

### Root Cause Analysis
- Determine the root consumer of disk space.
- Review if a runaway process or large download caused the spike.

## Escalation
- Page the infrastructure on-call immediately.
- Contact `#vf-infra-oncall`.

## Prevention
- Set lower-threshold alerts (warning at 15%).
- Implement automated cleanup jobs.
- Use object storage for large payloads instead of local disk.
