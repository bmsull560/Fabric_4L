# Runbook

Operational runbooks for Value Fabric production incidents.

## Quick Reference

### Health Checks

```bash
# Check all service health endpoints
curl -f http://localhost:8001/health  # Layer 1
curl -f http://localhost:8002/health  # Layer 2
curl -f http://localhost:8003/health  # Layer 3
curl -f http://localhost:8004/health  # Layer 4
curl -f http://localhost:8005/api/v1/health  # Layer 5

# Check Kubernetes pod status
kubectl get pods -n fabric-production
kubectl get pods -n fabric-staging
```

### Database Operations

```bash
# Run database migrations
cd services/layer1-ingestion
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# Check database connection
psql $DATABASE_URL -c "SELECT 1"
```

### Testing

```bash
# Run mandatory security regression gate
bash scripts/ci/mandatory_security_regression_gate.sh

# Run gate regression tests only
python -m pytest tests/ci/test_mandatory_security_regression_gate.py -v

# List required test suites
bash scripts/ci/mandatory_security_regression_gate.sh --list-required

# Verify required suites exist
bash scripts/ci/mandatory_security_regression_gate.sh --verify-required-only
```

### Evidence Collection

```bash
# Evidence is written to repo-relative fabric_audit/
# Default path: <repo-root>/fabric_audit/
# Override with: AUDIT_DIR=/custom/path bash scripts/ci/mandatory_security_regression_gate.sh

# View evidence
ls fabric_audit/
cat fabric_audit/i04_mandatory_security_regression_gate_evidence.md
```

## Detailed Runbooks

For full details, see:

- [Runbook Index](docs/troubleshooting/runbooks/README.md)
- [SLO Breach Response](docs/troubleshooting/runbooks/application/slo-breach-response.md)
- [Audit Write Failure](docs/troubleshooting/runbooks/application/audit-write-failure.md)
- [Alertmanager Guide](docs/operations/ALERTMANAGER.md)
- [Reliability Policy](docs/operations/reliability-policy.md)
- [Severity Escalation](docs/operations/severity-escalation-policy.md)
- [Secret Remediation](docs/security/secret-remediation-runbook.md)

## Launch Rehearsal

For launch procedures, see:

- [Platform Launch Checklist](docs/launch-checklists/platform-launch.md)
- [Salesforce CRM Launch Checklist](docs/launch-checklists/salesforce-crm-launch.md)
- [Command Reference](docs/operations/COMMAND_REFERENCE.md)
