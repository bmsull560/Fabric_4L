# Runbook: DiskSpaceLow

## Overview

Disk space utilization exceeding 90% (only 10% remaining) indicates approaching storage capacity limits. Proactive intervention required before reaching critical threshold (<5%).

## Trigger

- **Alert:** `DiskSpaceLow`
- **Condition:** `node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.10` for 5 minutes
- **Dashboard:** [Node Exporter Full](../../monitoring/grafana/dashboards/node-exporter-full.json) → Disk Space panel
- **Precedes:** [DiskSpaceCritical](disk-space-critical.md) alert at <5%

## Impact

- **Severity:** P3 - Warning (will escalate to P0 if unaddressed)
- **Immediate Impact:** Log rotation may fail, temp file creation issues
- **Time to Critical:** Typically 12-24 hours at current growth rate
- **Business Impact:** Degraded logging, potential service interruption looming

## Diagnosis

### 1. Identify Affected Node and Mountpoint

```bash
# Check all nodes for low disk status
kubectl get nodes -o json | jq -r '.items[] | .metadata.name as $n | .status.conditions[] | select(.type=="DiskPressure") | [$n, .status, .reason] | @tsv'

# Check specific node (from alert labels)
kubectl describe node <node-name> | grep -A10 "Conditions"

# Detailed disk usage
df -h | grep -E "Filesystem|/dev/|overlay"
```

### 2. Find Disk Usage by Directory

```bash
# On the affected node
du -h / --max-depth=1 2>/dev/null | sort -hr | head -10
du -h /var --max-depth=1 2>/dev/null | sort -hr | head -10
du -h /tmp --max-depth=1 2>/dev/null | sort -hr | head -10

# Check container logs (often the culprit)
find /var/log -type f -size +50M -exec ls -lh {} \;

# Check Docker storage
docker system df
```

### 3. Identify Growth Trends

```bash
# Check historical growth (if metrics available)
curl -s http://prometheus:9090/api/v1/query?query='predict_linear(node_filesystem_avail_bytes[1h], 86400) < 0'

# Find recently modified large files
find /var/log -type f -mtime -1 -size +10M -exec ls -lh {} \;

# Check for core dumps
find /tmp -name "core.*" -size +10M 2>/dev/null
```

## Immediate Containment

### 1. Log Rotation and Cleanup

```bash
# Rotate logs immediately
logrotate -f /etc/logrotate.d/value-fabric

# Vacuum journal (if systemd)
journalctl --vacuum-time=1d

# Truncate old logs
find /var/log -name "*.log.*" -mtime +7 -delete
find /var/log -name "*.gz" -mtime +14 -delete
```

### 2. Docker Cleanup

```bash
# Remove unused images, containers, volumes
docker system prune -af --volumes

# Clean build cache
docker builder prune -af

# Check dangling images
docker images -f "dangling=true" -q | xargs docker rmi 2>/dev/null || true
```

### 3. Package Cache Cleanup

```bash
# Clean package caches
apt-get clean  # Debian/Ubuntu
yum clean all  # RHEL/CentOS

# Clean npm/pip caches
npm cache clean --force 2>/dev/null || true
pip cache purge 2>/dev/null || true
```

## Remediation

### Quick Fix: PVC Resize (Cloud)

```bash
# AWS EBS - expand by 50%
kubectl get pvc <pvc-name> -n value-fabric -o json | jq '.spec.resources.requests.storage'
# Then patch: kubectl patch pvc <pvc-name> -n value-fabric -p '{"spec":{"resources":{"requests":{"storage":"NEW_SIZE"}}}}'

# Verify resize initiated
kubectl describe pvc <pvc-name> -n value-fabric | grep -A5 "Events"
```

### Root Cause Analysis

```bash
# Identify largest consumers
find /var -type f -size +100M -exec ls -lh {} \; 2>/dev/null | sort -k5 -hr | head -20

# Check application-specific growth
kubectl logs -n value-fabric --all-containers --since=24h | wc -c

# Database size check (if Postgres is culprit)
kubectl exec -n value-fabric -it deployment/postgres -- \
  psql -c "SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC LIMIT 10;"
```

## Rollback

If cleanup causes issues:

```bash
# Check application logs for errors
kubectl logs -n value-fabric -l app=layer4-agents --since=5m | grep -i error

# Restore from backup if critical files deleted
# (Depends on backup strategy - S3/MinIO restore)

# Verify no data loss
curl -sf https://api.valuefabric.io/v1/health && echo "Service: OK"
```

## Validation

```bash
# Verify disk space recovered
df -h | grep -E "Filesystem|/dev/"

# Check alert cleared (no DiskPressure condition)
kubectl get nodes -o json | jq '.items[].status.conditions[] | select(.type=="DiskPressure")'

# Verify log writing works
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  sh -c "echo 'validation test' >> /var/log/app.log && echo 'Write: OK'"

# Check growth rate (should be negative or stable)
du -sh /var/log
```

## Escalation

| Condition | Action |
|-----------|--------|
| Space <7% after cleanup | Page infrastructure on-call `#vf-infra-oncall` |
| PVC resize fails | Engage cloud platform support |
| Database is primary consumer | Escalate to DBA `#vf-dba-oncall` |
| Growth rate >10%/day | Page platform engineering |

## Prevention

- **Lower thresholds:** Alert at 20% free (currently 10%)
- **Automated cleanup:** Configure logrotate with `maxsize 100M`, `rotate 7`
- **PVC auto-expansion:** Enable if cloud provider supports it
- **Monitoring:** Track `predict_linear(disk_free[6h], 86400)` for early warning
- **Log aggregation:** Ship logs to external system (Loki/Elasticsearch) quickly
- **Resource quotas:** Set `ephemeral-storage` limits on pods

---

**Related Runbooks:**
- [Disk Space Critical](disk-space-critical.md) - Emergency response for <5%
- [Disk Inode Exhaustion](disk-inode-exhaustion.md) - Related storage issue
