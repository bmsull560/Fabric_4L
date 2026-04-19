# Runbook: DiskInodeExhaustion

## Overview

Inode exhaustion occurs when the filesystem runs out of file pointers, not disk bytes. New files cannot be created even with ample disk space. This causes application failures, crashes, and prevents log rotation.

## Trigger

- **Alert:** `DiskInodeExhaustion`
- **Condition:** `node_filesystem_files_free / node_filesystem_files < 0.10` for 5 minutes
- **Dashboard:** [Node Exporter Full](../../monitoring/grafana/dashboards/node-exporter-full.json) → Inode Usage panel

## Impact

- **Severity:** P1 - System degradation
- **Immediate Impact:** Cannot create new files, log rotation fails, temp file creation fails
- **Cascading Impact:** Applications crash, builds fail, database operations fail
- **Note:** Different from disk space - `df -h` may show plenty of space while `df -i` shows 100%

## Diagnosis

### 1. Verify Inode Exhaustion

```bash
# Check inode usage (watch for 100% or high IUse%)
df -i

# Compare bytes vs inodes
echo "=== Bytes ===" && df -h
echo "=== Inodes ===" && df -i
```

### 2. Find Inode Hogs

```bash
# Find directories with most files
find /var -xdev -printf '%h\n' | sort | uniq -c | sort -k 1 -n | tail -20

# Count files in specific suspect directories
ls -U1 /var/log | wc -l
ls -U1 /tmp | wc -l
ls -U1 /var/cache | wc -l

# Find directories with >100k files
find /var -xdev -type d -exec sh -c 'n=$(ls -U1 "$1" 2>/dev/null | wc -l); [ "$n" -gt 100000 ] && echo "$n $1"' _ {} \;
```

### 3. Identify File Patterns

```bash
# Most common file extensions (indicates what's creating files)
find /var/log -type f | sed 's/.*\.//' | sort | uniq -c | sort -rn | head -10

# Check for tmp files
find /tmp -type f -name "*.tmp" | wc -l
find /tmp -type f -name "temp*" | wc -l

# Session/cache files
find /var -name "sess_*" -o -name "cache_*" | wc -l
```

## Immediate Containment

### 1. Stop File-Creating Processes

```bash
# Identify top file-creating processes
lsof +D /var/log 2>/dev/null | awk '{print $1,$2}' | sort | uniq -c | sort -rn | head -10

# Restart suspected leaky service
kubectl rollout restart deployment/layer4-agents -n value-fabric
```

### 2. Emergency File Cleanup

```bash
# Remove old session files (common culprit)
find /tmp -name "sess_*" -mtime +1 -delete
find /var/cache -type f -mtime +7 -delete

# Clear npm/pip temporary caches
rm -rf /tmp/npm-* /tmp/pip-* /tmp/pipx-*

# Clear Docker build cache
docker builder prune -af
```

### 3. Truncate Log Fragments

```bash
# Find and remove log fragments (app.log.1.gz, etc.)
find /var/log -name "*.gz" -mtime +7 -delete
find /var/log -name "*.[0-9]" -mtime +3 -delete

# Consolidate by truncating rather than deleting (preserves open file handles)
for f in $(find /var/log -name "*.log.*" -mtime +1); do > "$f"; done
```

## Remediation

### Quick Fix: Consolidate Small Files

```bash
# Archive old small files into tarballs (reduces inode count)
cd /var/log && tar -czf old-logs-$(date +%Y%m%d).tar.gz $(find . -name "*.log.*" -mtime +7) && find . -name "*.log.*" -mtime +7 -delete

# Move to S3/MinIO if available
aws s3 sync /var/log/old/ s3://value-fabric-logs/archive/$(date +%Y/%m/) --delete
```

### Root Cause Analysis

```bash
# Check logrotate config
 cat /etc/logrotate.d/value-fabric

# Verify logrotate is working
logrotate -d /etc/logrotate.d/value-fabric  # Debug mode

# Check application logs for error loops
kubectl logs -n value-fabric -l app=layer4-agents --tail=100 | grep -i "error\|fail\|retry"

# Identify if specific user/tenant is creating files
find /var -type f -printf '%u %p\n' | cut -d' ' -f1 | sort | uniq -c | sort -rn | head -5
```

## Rollback

If cleanup causes application issues:

```bash
# Check application logs for errors post-cleanup
kubectl logs -n value-fabric -l app=layer4-agents --since=5m

# If session files were deleted while sessions active, restart service
kubectl rollout restart deployment/layer4-agents -n value-fabric

# Restore archived files if needed
tar -xzf /var/log/old-logs-$(date +%Y%m%d).tar.gz -C /var/log/restore/
```

## Validation

```bash
# Verify inode usage decreased
df -i | grep -E "Filesystem|/dev/"

# Confirm new files can be created
touch /var/log/validation-test && rm /var/log/validation-test && echo "Write: OK"

# Check alert cleared
kubectl get events -n value-fabric | grep -i "inode"

# Verify applications running
kubectl get pods -n value-fabric | grep -v Running
```

## Escalation

| Action | Contact |
|--------|---------|
| Immediate | Infrastructure on-call `#vf-infra-oncall` |
| Filesystem corruption suspected | Storage team `#vf-storage-oncall` |
| Application leak suspected | Platform on-call `#vf-platform-oncall` |
| >45 min to resolve | Escalate to SRE lead |

## Prevention

- **Lower thresholds:** Alert at 20% inodes free (vs current 10%)
- **Logrotate tuning:** `maxage 7`, `minsize 10M`, `delaycompress`
- **Application audit:** Review code that creates one-file-per-event
- **Storage architecture:** Use object storage (S3/MinIO) for high-file-count workloads
- **Monitoring:** Track inode creation rate: `irate(node_filesystem_files[5m])`

---

**Related Runbooks:**
- [Disk Space Critical](disk-space-critical.md) - Byte exhaustion
- [Disk Space Low](disk-space-low.md) - Warning threshold

**External References:**
- [Linux Inodes Explained](https://wiki.archlinux.org/title/File_systems)
- [Kubernetes Storage Management](https://kubernetes.io/docs/concepts/storage/)
