# Runbook: DiskSpaceCritical

## Overview

Critical disk space exhaustion with <5% available. Services will begin failing writes immediately. This is a P0 incident requiring immediate response.

## Trigger

- **Alert:** `DiskSpaceCritical`
- **Condition:** `node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.05` for 2 minutes
- **Dashboard:** [Node Exporter Full](../../monitoring/grafana/dashboards/node-exporter-full.json) → Disk Space panel

## Impact

- **Severity:** P0 - Imminent service failure
- **Immediate Impact:** Services fail writes, crash on startup, logs lost
- **Cascading Impact:** Database corruption risk, pod eviction, scheduling failures
- **Time to Failure:** <10 minutes at current consumption rate

## Diagnosis

### 1. Identify Affected Node and Mountpoint

```bash
# Check all nodes for critical disk status
kubectl get nodes -o json | jq -r '.items[] | .metadata.name as $n | .status.conditions[] | select(.type=="DiskPressure") | [$n, .status, .reason] | @tsv'

# Check specific node (from alert labels)
kubectl describe node <node-name> | grep -A10 "Conditions"

# SSH to node (if necessary)
kubectl debug node/<node-name> -it --image=busybox
```

### 2. Find Disk Usage by Directory

```bash
# On the affected node
df -h

# Find largest directories
du -h / --max-depth=1 2>/dev/null | sort -hr | head -10
du -h /var --max-depth=1 2>/dev/null | sort -hr | head -10
du -h /tmp --max-depth=1 2>/dev/null | sort -hr | head -10

# Check container logs (often the culprit)
find /var/log -type f -size +100M -exec ls -lh {} \;
```

### 3. Check Kubernetes-specific Usage

```bash
# Docker/cri-o image storage
docker system df

# Check ephemeral storage by pod
kubectl top pod -n value-fabric --containers | sort -k4 -hr

# Check PVC usage
kubectl get pvc -n value-fabric -o json | jq '.items[] | [.metadata.name, .status.capacity.storage, .status.conditions[].message // "ok"]'
```

## Immediate Containment

### 1. Emergency Log Truncation

```bash
# Truncate application logs
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  sh -c "> /var/log/app.log"

# Vacuum journal (if systemd)
journalctl --vacuum-time=1h
```

### 2. Docker Cleanup

```bash
# Remove unused images, containers, volumes
docker system prune -af --volumes

# Clean build cache
docker builder prune -af
```

### 3. Clear Temp Directories

```bash
# Clean /tmp
rm -rf /tmp/*

# Clean package caches
apt-get clean  # Debian/Ubuntu
yum clean all  # RHEL/CentOS
```

### 4. Evict Pods from Node (Last Resort)

```bash
# Cordon node to prevent new pods
kubectl cordon <node-name>

# Evict all pods (they will reschedule elsewhere)
kubectl drain <node-name> --ignore-daemonsets --force --delete-emptydir-data
```

## Remediation

### Quick Fix: Cloud PVC Resize

```bash
# AWS EBS
kubectl patch pvc <pvc-name> -n value-fabric -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# GCP Persistent Disk
kubectl patch pvc <pvc-name> -n value-fabric -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'

# Azure Disk
kubectl patch pvc <pvc-name> -n value-fabric -p '{"spec":{"resources":{"requests":{"storage":"100Gi"}}}}'
```

### Root Cause Analysis

```bash
# Identify largest file types
find /var/log -type f -exec ls -lh {} \; | sort -k5 -hr | head -20

# Check for runaway logs from specific pods
kubectl logs -n value-fabric --all-containers --since=1h | wc -c

# Identify if specific service is logging excessively
kubectl logs -n value-fabric -l app=layer4-agents --since=1h | wc -c
```

## Rollback

If cleanup causes issues:

```bash
# Restore logs from backup (if available)
# (This is why we don't delete files but truncate them)

# If node was drained, uncordon it
kubectl uncordon <node-name>

# If PVC resize failed, check events
kubectl describe pvc <pvc-name> -n value-fabric
```

## Validation

```bash
# Verify disk space freed
df -h | grep -E "Filesystem|/dev/"

# Check alert is cleared
kubectl get nodes -o json | jq '.items[].status.conditions[] | select(.type=="DiskPressure")'

# Verify pods running
kubectl get pods -n value-fabric -o wide | grep <node-name>

# Check log writing works
kubectl exec -n value-fabric -it deployment/layer4-agents -- \
  sh -c "echo 'test' >> /var/log/app.log && echo 'Write: OK'"
```

## Escalation

| Action | Contact |
|--------|---------|
| Immediate | Infrastructure on-call `#vf-infra-oncall` |
| PVC resize failure | Cloud platform support |
| Data corruption suspected | Database team `#vf-dba-oncall` |
| >30 min to resolve | Page platform engineering lead |

## Prevention

- **Lower thresholds:** Warning at 15%, critical at 10% (before current 5%)
- **Automated cleanup:** Logrotate with size limits, tmpwatch
- **Monitoring:** Grafana alert on `predict_linear(disk_free[1h], 3600) < 0`
- **Resource quotas:** Set `ephemeral-storage` limits on pods
- **Object storage:** Move large payloads to S3/MinIO instead of local disk

---

**Related Runbooks:**
- [Disk Space Low](disk-space-low.md) - Warning threshold
- [Disk Inode Exhaustion](disk-inode-exhaustion.md) - Different resource exhaustion
