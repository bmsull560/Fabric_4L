# DiskInodeExhaustion Runbook

## Severity: warning

## Alert Condition
`node_filesystem_files_free / node_filesystem_files < 0.10` for 5 minutes.

## Impact
New files cannot be created, causing application and system failures even if disk bytes are available.

## Triage Steps
1. Identify the node and filesystem from alert labels.
2. Find directories with the most files: `df -i` and `find /path -xdev -printf '%h\n' | sort | uniq -c | sort -k 1 -n | tail`.

## Resolution
### Quick Fix
- Remove old small files (logs, cache fragments, temporary build artifacts).
- Archive and delete directories with millions of tiny files.
- Restart services that may be leaking empty files.

### Root Cause Analysis
- Identify the process or application creating excessive files.
- Review if log rotation is splitting into too many small files.

## Escalation
- Escalate to infrastructure on-call if node-level intervention is required.
- Contact `#vf-infra-oncall`.

## Prevention
- Consolidate logs into fewer, larger files.
- Set up inode monitoring with lower thresholds.
- Avoid designs that create one file per event on local disk.
