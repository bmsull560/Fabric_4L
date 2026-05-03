# Production Readiness

## Current State

The MVP uses mock persistence and is suitable for local development and demos.

## Production Checklist

### Infrastructure
- [ ] PostgreSQL primary database
- [ ] Neo4j graph database
- [ ] Redis cache/queue
- [ ] S3-compatible object storage
- [ ] Kubernetes manifests

### Security
- [ ] JWT token rotation
- [ ] CSRF protection
- [ ] Rate limiting
- [ ] Secret management (Infisical/Vault)
- [ ] Penetration testing

### Observability
- [ ] Structured logging
- [ ] Metrics (Prometheus)
- [ ] Distributed tracing
- [ ] Alerting (PagerDuty)

### Data
- [ ] Database migrations (Alembic)
- [ ] Backup strategies
- [ ] Data retention policies
- [ ] GDPR compliance

### CI/CD
- [ ] GitHub Actions workflows
- [ ] Automated testing gates
- [ ] Contract drift detection
- [ ] Smoke test gates
- [ ] Environment promotion

### Performance
- [ ] Load testing
- [ ] Connection pooling
- [ ] Query optimization
- [ ] CDN for static assets

## Production Gates Policy

See `.fabric/prod-gates.policy.yaml` for the current gate evaluation policy.
