# DiskSpaceLow Runbook

## Severity: warning

## Alert Condition
`node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.10` for 5 minutes.

## Impact
Risk of write failures, log rotation issues, and eventual service crashes.

## Triage Steps
1. Identify the node and mountpoint from the alert labels.
2. Check disk usage breakdown with `df -h` and `du -sh /*`.
3. Determine if growth is from logs, temp files, or application data.

## Resolution
### Quick Fix
- Truncate or rotate old logs (`journalctl --vacuum-time=1d` or logrotate).
- Clear temporary files and package caches.
- Remove unused Docker images and volumes.

### Root Cause Analysis
- Review log volume trends and retention policies.
- Check if an application is writing excessively large files.

## Escalation
- Escalate to infrastructure on-call if PVC resize is needed.
- Contact `#vf-infra-oncall`.

## Prevention
- Enable automated log rotation and retention.
- Set up PVC auto-expansion where supported.
- Monitor disk growth trends with forecasting.
