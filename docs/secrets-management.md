# Value Fabric Secrets Management Guide

Production-ready secret handling across local development, Docker Compose, and Kubernetes environments.

---

## Overview

| Environment | Method | Secret Store |
|-------------|--------|--------------|
| Local Dev | `.env` file | Local filesystem (git-ignored) |
| Docker Compose | `.env` file + env vars | Local filesystem (git-ignored) |
| Kubernetes (dev) | K8s Secrets | etcd (base64 encoded) |
| Kubernetes (prod) | External Secrets Operator | HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, or GCP Secret Manager |

---

## Required Secrets Inventory

### Critical (Service Startup Will Fail Without These)

| Secret Name | Used By | Purpose | Source |
|-------------|---------|---------|--------|
| `OPENAI_API_KEY` | L1, L2, L4 | LLM API calls | OpenAI Dashboard |

### Important (Required for Full Functionality)

| Secret Name | Used By | Purpose | Default | Source |
|-------------|---------|---------|---------|--------|
| `NEO4J_PASSWORD` | L2, L3, L4 | Graph database auth | `valuefabric` | Self-managed |
| `JWT_SECRET` | L5 | Token signing | `changeme-in-production` | Generate with `openssl rand -hex 32` |
| `POSTGRES_PASSWORD` | L1, L4, L5 | SQL database auth | `postgres` | Self-managed |

### Optional (Enhancements)

| Secret Name | Used By | Purpose | Source |
|-------------|---------|---------|--------|
| `ANTHROPIC_API_KEY` | L4 | Alternative LLM provider | Anthropic Console |
| `PINECONE_API_KEY` | L3 | Vector search backend | Pinecone Dashboard |
| `BROWSERBASE_API_KEY` | L1 | Browser automation | Browserbase Dashboard |
| `FIRECRAWL_API_KEY` | L1 | Web scraping API | Firecrawl Dashboard |
| `LAYER3_API_KEY` | L5 | Inter-layer auth | Self-managed |

---

## Local Development Setup

### 1. Create .env file

```bash
cd value-fabric
cp .env.example .env
# Edit .env with your real secrets
```

### 2. Required minimum for local dev

Your `.env` file must contain at minimum:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3. Verify .env is git-ignored

```bash
cat ../.gitignore | grep -E "^\.env"
```

Expected output: `.env` or `.env.local` should be listed.

---

## Docker Compose Setup

Docker Compose automatically loads `.env` from the same directory as `docker-compose.yml`.

### Startup with secrets

```bash
cd value-fabric
# Ensure .env exists with OPENAI_API_KEY
docker-compose up -d
```

### Verifying secrets are injected

```bash
# Check environment inside container
docker exec value-fabric-layer1 env | grep OPENAI
# Should show: OPENAI_API_KEY=sk-...
```

---

## Kubernetes Setup

### Development (K8s Secrets - Base64 Encoded)

**⚠️ WARNING:** K8s Secrets are base64-encoded, not encrypted. Use only for development.

```bash
# Apply the development secrets template
kubectl apply -f k8s/secrets.yml

# Verify
kubectl get secrets -n value-fabric
```

### Production (External Secrets Operator)

#### Prerequisites

1. Install External Secrets Operator:
   ```bash
   helm repo add external-secrets https://charts.external-secrets.io
   helm install external-secrets external-secrets/external-secrets
   ```

2. Configure Vault Kubernetes auth (one-time setup):
   ```bash
   vault auth enable kubernetes
   vault write auth/kubernetes/config \
     kubernetes_host="https://$KUBERNETES_PORT_443_TCP_ADDR:443" \
     token_reviewer_jwt="$(cat /var/run/secrets/kubernetes.io/serviceaccount/token)" \
     kubernetes_ca_cert=@/var/run/secrets/kubernetes.io/serviceaccount/ca.crt
   ```

3. Create Vault policy for Value Fabric:
   ```bash
   vault policy write value-fabric-policy - <<EOF
   path "secret/data/value-fabric/*" {
     capabilities = ["read"]
   }
   EOF
   ```

4. Create Kubernetes auth role:
   ```bash
   vault write auth/kubernetes/role/value-fabric-role \
     bound_service_account_names=external-secrets-sa \
     bound_service_account_namespaces=external-secrets \
     policies=value-fabric-policy \
     ttl=1h
   ```

#### Deploy Production Secrets

```bash
# Update vault-integration.yml with your Vault URL
# Then apply:
kubectl apply -f k8s/external-secrets/vault-integration.yml

# Verify ExternalSecrets created
kubectl get externalsecrets -n value-fabric

# Verify secrets populated
kubectl get secrets -n value-fabric
```

---

## Secret Rotation Procedures

### LLM API Keys (OpenAI, Anthropic)

1. Generate new key in provider dashboard
2. Update secret store (Vault or K8s Secret)
3. Trigger rolling restart of affected pods:
   ```bash
   kubectl rollout restart deployment/layer1-ingestion -n value-fabric
   kubectl rollout restart deployment/layer2-extraction -n value-fabric
   kubectl rollout restart deployment/layer4-agents -n value-fabric
   ```
4. Verify new pods healthy
5. Revoke old key in provider dashboard

### Database Passwords (Neo4j, PostgreSQL)

1. Update password in database first
2. Update secret in Vault/K8s
3. Rolling restart of all services using that database
4. Verify connectivity post-restart

### JWT Secret (L5)

**⚠️ CRITICAL:** JWT secret rotation invalidates all existing tokens.

1. Schedule maintenance window
2. Update secret in Vault/K8s
3. Rolling restart of L5 deployment
4. Notify all users to re-authenticate
5. Monitor for auth errors

---

## Security Best Practices

### General

- **Never commit secrets to git** - Use `.env.example` for templates
- **Rotate keys regularly** - Set calendar reminders quarterly
- **Use least privilege** - Scope API keys to minimum required permissions
- **Monitor key usage** - Set up alerts for unusual activity

### Docker Compose

- `.env` file should have permissions `600` (owner read/write only)
- Use Docker Secrets for Swarm mode (not applicable for Compose standalone)

### Kubernetes

- **Development:** K8s Secrets acceptable but keep minimal
- **Production:** Always use external secret store (Vault, cloud provider)
- Enable encryption at rest for etcd (K8s 1.7+)
- Use RBAC to limit secret access
- Rotate service account tokens regularly

### Vault Specific

- Enable audit logging
- Use short TTLs (1h default)
- Enable response wrapping for sensitive operations
- Use AppRole or Kubernetes auth (not long-lived tokens)
- Enable seal/unseal monitoring

---

## Troubleshooting

### "OPENAI_API_KEY not set" error

**Symptom:** Service fails to start with key error  
**Fix:**
```bash
# Check .env file exists and has key
cat value-fabric/.env | grep OPENAI

# For K8s, check secret exists
kubectl get secret openai-secret -n value-fabric -o jsonpath='{.data.api-key}' | base64 -d
```

### "authentication failed" for Neo4j/Postgres

**Symptom:** Services fail to connect to database  
**Fix:**
- Verify secret matches actual database password
- Check network connectivity: `kubectl exec -it <pod> -n value-fabric -- nc -zv neo4j 7687`

### External Secrets not populating

**Symptom:** `ExternalSecret` shows `SecretSyncedError`  
**Fix:**
```bash
# Check ExternalSecret status
kubectl describe externalsecret openai-api-key -n value-fabric

# Check Vault connectivity from pod
kubectl exec -it vault-0 -n vault -- vault status
```

---

## Reference

### Files

| File | Purpose |
|------|---------|
| `value-fabric/.env.example` | Template for local dev |
| `k8s/secrets.yml` | Dev secrets (base64 encoded) |
| `k8s/external-secrets/vault-integration.yml` | Production Vault integration |

### Tools

- [External Secrets Operator](https://external-secrets.io/)
- [HashiCorp Vault](https://www.vaultproject.io/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)

## OIDC Client Secrets via Vault

For Task 40 (SSO / OIDC), store `client_secret` as a Vault reference instead of plaintext in the database. Configure the tenant's OIDC settings with:

```json
{
  "oidc": {
    "client_secret_ref": "vault:secret/value-fabric/oidc/{tenant-slug}"
  }
}
```

The application resolves the reference at runtime using the Vault KV v2 API. Rotate the secret in Vault without touching the database.

## Dynamic PostgreSQL Secrets

In production, use the Vault Database Secrets Engine to generate short-lived PostgreSQL credentials. See `k8s/external-secrets/vault-database-dynamic.yml` for the ExternalSecret manifest (1h TTL). Dynamic credentials are automatically rotated and revoked, reducing the blast radius of credential leaks.

## Smoke Gate

Before deploying to production, run the Vault smoke test to verify connectivity and secret access:

```bash
export VAULT_ADDR=https://vault.value-fabric.svc:8200
export VAULT_TOKEN=<your-vault-token>
python scripts/smoke/vault_smoke.py
```

A non-zero exit code blocks the deployment pipeline.

---

*Last updated: 2026-04-13*
