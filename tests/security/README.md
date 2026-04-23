# Security Test Suite

Comprehensive security validation tests for Fabric 4L including tenant isolation, RBAC, and OWASP Top 10 coverage.

## Quick Start

```bash
# 1. Copy environment template
cd tests/security
cp .env.example .env

# 2. Start infrastructure services
docker-compose -f ../../value-fabric/docker-compose.yml up postgres redis neo4j -d

# 3. Run smoke tests (fast)
pytest test_security_smoke.py -v

# 4. Run full security suite
pytest . -v --tb=short
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JWT_SECRET` | Yes | N/A | HS256 signing key (min 32 chars) |
| `TEST_DATABASE_URL` | No | `postgresql://localhost:5432/test_value_fabric` | PostgreSQL connection |
| `REDIS_HOST` | No | `localhost` | Redis hostname |
| `REDIS_PORT` | No | `6379` | Redis port |
| `NEO4J_URI` | No | `bolt://localhost:7687` | Neo4j Bolt URI |

## Test Structure

| File | Purpose | Runtime |
|------|---------|---------|
| `test_security_smoke.py` | Critical path validation (< 2 min) | ~60s |
| `test_tenant_isolation.py` | Cross-tenant data leak prevention | ~180s |
| `test_rbac.py` | Permission granularity and JWT security | ~120s |
| `test_owasp_top10.py` | OWASP A01-A04 coverage | ~90s |
| `test_security_misconfiguration.py` | Headers, debug endpoints | ~45s |

## CI Configuration

The security validation workflow (`.github/workflows/security-validation.yml`) automatically:
- Runs smoke tests on PRs touching security-critical paths
- Runs full suite daily at 3 AM UTC
- Requires `TEST_JWT_SECRET` repository secret

## Troubleshooting

### "JWT_SECRET environment variable is required"
Set the JWT_SECRET in your environment:
```bash
export JWT_SECRET="test-jwt-secret-must-be-at-least-32-characters-long"
```

### Database connection failures
Ensure PostgreSQL is running:
```bash
docker-compose up postgres -d
```

### Redis connection failures
Ensure Redis is running:
```bash
docker-compose up redis -d
```
