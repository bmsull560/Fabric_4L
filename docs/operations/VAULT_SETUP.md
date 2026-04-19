# HashiCorp Vault Setup and Operations Guide

Complete guide for setting up and operating HashiCorp Vault for Value Fabric secrets management.

---

## Prerequisites

- Kubernetes cluster with External Secrets Operator installed
- Vault CLI installed locally (`brew install vault` or [download](https://developer.hashicorp.com/vault/downloads))
- kubectl access to the cluster
- PostgreSQL database running for dynamic credentials

---

## Initial Vault Setup

### 1. Deploy Vault (Development)

```bash
# Create vault namespace
kubectl create namespace vault

# Deploy Vault in dev mode
kubectl apply -f k8s/vault/vault-deployment.yaml

# Wait for Vault to be ready
kubectl wait --for=condition=ready pod -l app=vault -n vault --timeout=60s

# Port-forward for local access
kubectl port-forward -n vault deployment/vault 8200:8200 &

# Set environment variables
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=dev-root-token-change-in-production
```

### 2. Verify Vault is Running

```bash
vault status
# Should show: Sealed: false, Key Shares: 1, Key Threshold: 1
```

### 3. Initialize Vault with Development Secrets

```bash
# Run the dev init script
./scripts/vault-dev-init.sh
```

This creates:
- `secret/value-fabric/llm` - LLM API keys
- `secret/value-fabric/database` - Database credentials
- `secret/value-fabric/auth` - JWT and HMAC secrets

---

## Production Vault Setup

### 1. Enable Kubernetes Authentication

```bash
# Enable Kubernetes auth method
vault auth enable kubernetes

# Get Kubernetes cluster info
export K8S_HOST=$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')
export TOKEN_REVIEW_JWT=$(kubectl create token external-secrets -n external-secrets --duration=1h)
export K8S_CA_CERT=$(kubectl get configmap -n kube-system extension-apiserver-authentication -o=jsonpath='{.data.client-ca-file}')

# Configure Kubernetes auth
vault write auth/kubernetes/config \
  kubernetes_host="${K8S_HOST}" \
  token_reviewer_jwt="${TOKEN_REVIEW_JWT}" \
  kubernetes_ca_cert="${K8S_CA_CERT}" \
  issuer="https://kubernetes.default.svc.cluster.local"
```

### 2. Create Vault Policies

```bash
# Create policies from HCL files
vault policy write external-secrets k8s/vault/policies/external-secrets.hcl
vault policy write value-fabric-layers k8s/vault/policies/value-fabric-layers.hcl
vault policy write value-fabric-admin k8s/vault/policies/value-fabric-admin.hcl

# Verify policies
vault policy list
vault policy read external-secrets
```

### 3. Create Kubernetes Auth Roles

```bash
# External Secrets Operator role
vault write auth/kubernetes/role/external-secrets \
  bound_service_account_names=external-secrets \
  bound_service_account_namespaces=external-secrets \
  policies=external-secrets \
  ttl=1h \
  max_ttl=4h

# Layer-specific roles
for layer in layer1 layer2 layer3 layer4; do
  vault write auth/kubernetes/role/${layer}-app \
    bound_service_account_names=${layer}-ingestion,${layer}-extraction,${layer}-knowledge,${layer}-agents \
    bound_service_account_namespaces=value-fabric \
    policies=value-fabric-layers \
    ttl=1h \
    max_ttl=4h
done

# Verify roles
vault list auth/kubernetes/role
```

### 4. Enable Database Secrets Engine

```bash
# Enable the database secrets engine
vault secrets enable database

# Run the database configuration script
export POSTGRES_ADMIN_PASSWORD=<your-postgres-admin-password>
./scripts/vault/configure-database-secrets.sh
```

---

## Configure External Secrets Operator

### 1. Apply ClusterSecretStore

```bash
# Apply the ClusterSecretStore configuration
kubectl apply -f k8s/external-secrets/cluster-secret-store.yaml

# Verify it's ready
kubectl get ClusterSecretStore vault-backend
```

### 2. Apply ExternalSecrets

```bash
# Apply layer-specific ExternalSecrets
kubectl apply -f k8s/external-secrets/layer1-secrets.yaml
kubectl apply -f k8s/external-secrets/layer2-secrets.yaml
kubectl apply -f k8s/external-secrets/layer3-secrets.yaml
kubectl apply -f k8s/external-secrets/layer4-secrets.yaml

# Apply dynamic database credentials
kubectl apply -f k8s/external-secrets/vault-database-dynamic.yaml
```

### 3. Verify Secret Sync

```bash
# Check ExternalSecret status
kubectl get externalsecret -n value-fabric

# Check that K8s Secrets were created
kubectl get secrets -n value-fabric

# Verify dynamic credentials
kubectl get secret postgres-app-secret -n value-fabric -o jsonpath='{.data.DATABASE_URL}' | base64 -d
```

---

## Verification

### Run Smoke Tests

```bash
# Test Vault connectivity and secrets
export VAULT_ADDR=https://vault.value-fabric.svc:8200
export VAULT_TOKEN=<your-token>
python scripts/smoke/vault_smoke.py

# Test ClusterSecretStore
python scripts/smoke/clustersecretstore_check.py
```

### Test Dynamic Credentials

```bash
# Generate credentials
vault read database/creds/layer1-app

# Test connection (requires psql)
psql "postgresql://<user>:<pass>@postgres.value-fabric.svc.cluster.local:5432/ingestion?sslmode=require" -c "SELECT current_user;"
```

---

## Operations

### Rotate Static Secrets

```bash
# Update a secret in Vault
vault kv put secret/value-fabric/llm openai-api-key="sk-new-key"

# External Secrets Operator will sync within refreshInterval (default 1h)
# Or restart pods to pick up immediately
kubectl rollout restart deployment/layer1-ingestion -n value-fabric
```

### Rotate Dynamic Credentials

Dynamic credentials rotate automatically based on TTL:
- `layer1-app` through `layer4-app`: 1h TTL, 4h max TTL
- `admin-role`: 4h TTL, 24h max TTL
- `readonly-role`: 24h TTL, 168h max TTL

Manual rotation:
```bash
# Rotate a specific role
vault write -f database/rotate-role/layer1-app

# Rotate root credentials (admin only)
vault write -f database/rotate-root/postgres
```

### Check Audit Log

```bash
# List recent Vault operations
vault audit list

# View audit log device (if file audit is enabled)
kubectl exec -n vault deployment/vault -- cat /vault/logs/audit.log
```

---

## Troubleshooting

### ExternalSecret Sync Fails

```bash
# Check ExternalSecret status
kubectl describe externalsecret <name> -n value-fabric

# Check External Secrets Operator logs
kubectl logs -n external-secrets deployment/external-secrets

# Verify Vault connectivity
kubectl run vault-test --rm -i --restart=Never --image=curlimages/curl \
  -- -s ${VAULT_ADDR}/v1/sys/health

# Check Kubernetes auth
vault read auth/kubernetes/config
vault list auth/kubernetes/role
```

### Dynamic Credentials Fail

```bash
# Check database connection config
vault read database/config/postgres

# Check role configuration
vault read database/roles/layer1-app

# Test credential generation
vault read database/creds/layer1-app

# Check database plugin status
vault status
```

### Vault Health Issues

```bash
# Check Vault status
vault status

# Check if sealed (in production)
vault operator seal-status

# Check leader status (HA mode)
vault operator raft list-peers
```

---

## Security Best Practices

1. **Enable Audit Logging**: Configure audit devices for all secret access
2. **Short TTLs**: Use 1h default TTL for dynamic credentials
3. **No Root Tokens**: Create admin policies and revoke root token after setup
4. **TLS Everywhere**: Use `https://` for Vault in production
5. **Network Policies**: Restrict Vault access with K8s network policies
6. **Backup**: Regularly backup Vault data (for integrated storage)

---

## Related Files

| File | Purpose |
|------|---------|
| `k8s/vault/vault-deployment.yaml` | Vault server deployment |
| `k8s/vault/policies/*.hcl` | Vault policy definitions |
| `k8s/vault/k8s-auth-roles.yaml` | Kubernetes auth role config |
| `k8s/external-secrets/cluster-secret-store.yaml` | ESO cluster config |
| `k8s/external-secrets/layer*-secrets.yaml` | Layer-specific ExternalSecrets |
| `k8s/external-secrets/vault-database-dynamic.yaml` | Dynamic PostgreSQL creds |
| `scripts/vault/configure-database-secrets.sh` | Database secrets engine setup |
| `scripts/vault-dev-init.sh` | Dev environment seeding |

---

*Last updated: 2026-04-19*
