# Security Hardening Guide - Production Deployment

## Overview

This document provides security hardening configurations for production deployment of the Value Fabric platform.

## Security Headers Configuration

### API Layer (L1-L6)

All API layers implement the following security headers via `SecurityMiddleware`:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME type sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS protection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Controls referrer leakage |
| `Content-Security-Policy` | `default-src 'none'; frame-ancestors 'none'` | API-specific strict CSP |
| `Permissions-Policy` | Feature restrictions | Limits browser feature access |
| `Cross-Origin-Resource-Policy` | `same-origin` | Prevents cross-origin resource loading |
| `Cross-Origin-Opener-Policy` | `same-origin` | Prevents cross-origin window manipulation |

### Frontend Layer

Frontend applications should configure CSP via web server (nginx/Apache) or meta tags:

```nginx
# Example nginx CSP configuration
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://api.value-fabric.com; frame-ancestors 'none';" always;
```

## Secrets Management

### Environment Variables

Required secrets for production:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname
NEO4J_URI=bolt://neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<strong-password>

# Authentication
JWT_SECRET=<minimum-32-char-secret>
OIDC_CLIENT_SECRET=<provider-secret>

# External APIs
OPENAI_API_KEY=<api-key>
ANTHROPIC_API_KEY=<api-key>

# Storage
S3_ACCESS_KEY=<access-key>
S3_SECRET_KEY=<secret-key>
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: value-fabric-secrets
  namespace: value-fabric
type: Opaque
stringData:
  JWT_SECRET: <generated-secret>
  DATABASE_URL: <connection-string>
  NEO4J_PASSWORD: <password>
```

### Vault Integration (Recommended)

For enterprise deployments, use HashiCorp Vault:

```yaml
# Example Vault configuration
secrets:
  - path: secret/value-fabric/layer4
    keys:
      - JWT_SECRET
      - DATABASE_URL
  - path: secret/value-fabric/layer3
    keys:
      - NEO4J_PASSWORD
      - PINECONE_API_KEY
```

## Rate Limiting

### API Rate Limits

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| Authentication | 5 requests | 1 minute |
| General API | 100 requests | 1 minute |
| Graph Queries | 30 requests | 1 minute |
| Batch Operations | 10 requests | 1 minute |

### Configuration

Rate limiting is configured in each layer's `rate_limiter.py`:

```python
# Example configuration
RATE_LIMITS = {
    "default": {"requests": 100, "window": 60},
    "auth": {"requests": 5, "window": 60},
    "graph": {"requests": 30, "window": 60},
    "batch": {"requests": 10, "window": 60},
}
```

## Network Security

### Kubernetes Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: value-fabric-deny-all
  namespace: value-fabric
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

### Service-to-Service mTLS

Enable mTLS between services using Istio or Linkerd:

```yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: value-fabric
spec:
  mtls:
    mode: STRICT
```

## Input Validation

### SecurityMiddleware Features

The `SecurityMiddleware` in each API layer provides:

1. **SQL Injection Detection**: Pattern-based detection for common SQLi payloads
2. **XSS Prevention**: Detection of script tags and event handlers
3. **NoSQL Injection**: MongoDB/NoSQL-specific pattern detection
4. **Command Injection**: Shell command detection
5. **Input Sanitization**: HTML escaping and null byte removal
6. **JSON Validation**: Deep nesting and large payload protection

### Validation Bypass Paths

The following paths skip validation (legitimate data triggers false positives):
- `/v1/ingest` - RDF/Turtle data ingestion
- `/v1/sync` - Synchronization endpoints
- `/v1/batch/ingest` - Batch ingestion
- `/v1/query/graph` - Natural language graph queries
- `/v1/graph/query` - Graph traversal queries

## Audit Logging

### Sensitive Operations Logged

All layers log the following operations:

- Authentication attempts (success/failure)
- Authorization failures
- Data modifications (CREATE, UPDATE, DELETE)
- Administrative actions
- Security violations

### Log Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "level": "INFO",
  "event_type": "authentication",
  "user_id": "user-123",
  "tenant_id": "tenant-1",
  "action": "login",
  "result": "success",
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0...",
  "trace_id": "abc-123-def"
}
```

## Security Scanning

### CI/CD Pipeline

The following security scans run in CI:

1. **SAST**: Semgrep + CodeQL
2. **SCA**: Trivy/Grype for dependency vulnerabilities
3. **Secrets**: Gitleaks for credential detection
4. **Container**: Trivy image scanning
5. **IaC**: Checkov/tfsec for Terraform/K8s

### Configuration

See `.github/workflows/security-gates.yml` for scan configuration.

## Incident Response

### Security Event Handling

1. **Detection**: Security violations logged with severity
2. **Alerting**: Critical events trigger PagerDuty/Opsgenie
3. **Investigation**: Use trace_id to correlate events
4. **Mitigation**: Block IPs, revoke tokens, rotate secrets
5. **Recovery**: Restore from backups, verify integrity

### Contact

Report security issues privately:
- GitHub Security tab → Report vulnerability
- Email: security@value-fabric.com

## Compliance

### Control Mappings

| Standard | Controls |
|----------|----------|
| SOC 2 | CC6.1, CC6.2, CC6.3, CC7.1, CC7.2 |
| ISO 27001 | A.12.3, A.12.4, A.14.2 |
| GDPR | Article 32 (Security of Processing) |

See `docs/compliance/control-matrix.md` for detailed mappings.

---

**Last Updated**: 2026-04-15  
**Version**: 1.0  
**Classification**: Internal
