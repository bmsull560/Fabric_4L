# Backup and Disaster Recovery Runbook

## Scope
Layer 3 knowledge graph backup creation, integrity validation, restore drills, and point-in-time restore (PITR).

## Recovery Objectives
- **RTO (Recovery Time Objective): 30 minutes** — API read/write service for Layer 3 restored within 30 minutes of incident declaration.
- **RPO (Recovery Point Objective): 15 minutes** — Data loss limited to at most 15 minutes by combining periodic full backups with incremental captures.

## Preconditions
1. Backup storage is reachable (`local`, `s3`, `gcs`, `azure`, or `ftp` backend).
2. Latest backup metadata has checksum recorded.
3. Restore target database is available (or dry-run target for drills).

## Runbook Steps Mapped to RTO/RPO

### 1) Verify backup inventory (supports RPO)
- List backups and identify latest successful full + incremental chain.
- Confirm metadata checksum exists for selected backup.
- **Target time:** 5 minutes.

### 2) Validate integrity before restore (supports RPO)
- Retrieve backup and verify SHA-256 checksum from metadata sidecar.
- If mismatch occurs, select prior backup and raise incident severity.
- **Target time:** 5 minutes.

### 3) Execute restore drill (supports RTO)
- Run dry-run restore against selected backup.
- Record entities/relationships that would be restored.
- **Target time:** 10 minutes.

### 4) Execute actual restore (supports RTO)
- Restore schema, then data to recovery target.
- Use point-in-time parameter when incident requires rollback to known-safe timestamp.
- **Target time:** 10 minutes.

### 5) Post-restore validation and cutover (supports RTO)
- Validate service health checks and key API queries.
- Cut traffic to recovered instance.
- **Target time:** 5 minutes.

## Drill Cadence
- Weekly automated dry-run drills.
- Monthly PITR drill to a timestamp earlier than the latest incremental backup.

## Failure Handling
- If any integrity check fails, do not proceed with production restore from that artifact.
- If drill exceeds target RTO, open corrective action item to reduce restore runtime.
