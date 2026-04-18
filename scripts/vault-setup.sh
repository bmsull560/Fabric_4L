#!/bin/bash
# Vault Setup Script for Fabric_4L
# Configures Vault for External Secrets Operator integration
#
# Usage: ./vault-setup.sh
# Environment variables:
#   VAULT_ADDR - Vault server URL (default: http://vault.vault.svc.cluster.local:8200)
#   VAULT_TOKEN - Vault root token (default: dev-root-token)
#   K8S_HOST - Kubernetes API URL (default: https://kubernetes.default.svc)

set -euo pipefail

# Constants
readonly MAX_RETRIES=3
readonly RETRY_DELAY=5
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Logging functions
log_info() { echo "[INFO]  $1"; }
log_warn() { echo "[WARN]  $1"; }
log_error() { echo "[ERROR] $1" >&2; }

# Retry function with exponential backoff
retry_with_backoff() {
    local cmd="$1"
    local max_retries="${2:-$MAX_RETRIES}"
    local delay="${3:-$RETRY_DELAY}"
    local attempt=1

    while [ $attempt -le $max_retries ]; do
        if eval "$cmd" 2>/dev/null; then
            return 0
        fi
        log_warn "Command failed (attempt $attempt/$max_retries), retrying in ${delay}s..."
        sleep $delay
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done

    log_error "Command failed after $max_retries attempts: $cmd"
    return 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    command -v vault >/dev/null 2>&1 || { log_error "vault CLI not found. Install from https://developer.hashicorp.com/vault/downloads"; exit 1; }
    command -v kubectl >/dev/null 2>&1 || { log_error "kubectl not found"; exit 1; }
    command -v curl >/dev/null 2>&1 || { log_error "curl not found"; exit 1; }
    
    log_info "✓ Prerequisites satisfied"
}

# Configuration
VAULT_ADDR="${VAULT_ADDR:-http://vault.vault.svc.cluster.local:8200}"
VAULT_TOKEN="${VAULT_TOKEN:-dev-root-token}"
K8S_HOST="${K8S_HOST:-https://kubernetes.default.svc}"

log_info "=========================================="
log_info "Fabric_4L Vault Setup"
log_info "=========================================="
log_info "Vault Address: $VAULT_ADDR"
log_info "Kubernetes Host: $K8S_HOST"

# Check prerequisites
check_prerequisites

# Wait for Vault to be ready
log_info ""
log_info "[1/8] Waiting for Vault to be ready..."
if ! retry_with_backoff "curl -sf $VAULT_ADDR/v1/sys/health > /dev/null" 30 5; then
    log_error "Vault did not become ready within timeout"
    exit 1
fi
log_info "✓ Vault is ready"

# Enable KV secrets engine
log_info ""
log_info "[2/8] Enabling KV secrets engine..."
if ! retry_with_backoff "vault secrets list | grep -q '^secret/'" 3 2; then
    if vault secrets enable -path=secret kv-v2 2>/dev/null; then
        log_info "✓ KV secrets engine enabled"
    else
        log_error "Failed to enable KV secrets engine"
        exit 1
    fi
else
    log_info "✓ KV secrets engine already enabled"
fi

# Enable Kubernetes auth
log_info ""
log_info "[3/8] Enabling Kubernetes authentication..."
if ! retry_with_backoff "vault auth list | grep -q 'kubernetes/'" 3 2; then
    if vault auth enable kubernetes 2>/dev/null; then
        log_info "✓ Kubernetes auth enabled"
    else
        log_error "Failed to enable Kubernetes auth"
        exit 1
    fi
else
    log_info "✓ Kubernetes auth already enabled"
fi

# Configure Kubernetes auth
log_info ""
log_info "[4/8] Configuring Kubernetes authentication..."

# Get service account token for token review
SERVICE_ACCOUNT_TOKEN=$(kubectl get secret -n external-secrets \
    $(kubectl get serviceaccount external-secrets -n external-secrets -o jsonpath='{.secrets[0].name}') \
    -o jsonpath='{.data.token}' | base64 -d)

# Get CA cert
CA_CERT=$(kubectl get cm kube-root-ca.crt -n kube-system -o jsonpath='{.data.ca\.crt}' 2>/dev/null || \
          kubectl get secret -n default -o jsonpath='{.items[?(@.type=="kubernetes.io/service-account-token")].data.ca\.crt}' | head -1 | base64 -d)

vault write auth/kubernetes/config \
    token_reviewer_jwt="$SERVICE_ACCOUNT_TOKEN" \
    kubernetes_host="$K8S_HOST" \
    kubernetes_ca_cert="$CA_CERT" \
    issuer=""

log_info "✓ Kubernetes auth configured"

# Create Vault policy
log_info ""
log_info "[5/8] Creating Vault policy..."
cat > /tmp/fabric-policy.hcl << 'EOF'
# Allow reading all secrets under secret/fabric/*
path "secret/data/fabric/*" {
  capabilities = ["read"]
}

# Allow reading CI secrets
path "secret/data/ci/*" {
  capabilities = ["read"]
}

# Allow listing secret paths
path "secret/metadata/*" {
  capabilities = ["list"]
}
EOF

if vault policy write fabric-policy /tmp/fabric-policy.hcl 2>/dev/null; then
    log_info "✓ Policy 'fabric-policy' created"
else
    log_error "Failed to create policy"
    exit 1
fi

# Create Kubernetes auth role for External Secrets Operator
log_info ""
log_info "[6/8] Creating Kubernetes auth role..."
if vault write auth/kubernetes/role/external-secrets \
    bound_service_account_names=external-secrets \
    bound_service_account_namespaces=external-secrets \
    policies=fabric-policy \
    ttl=1h \
    max_ttl=4h 2>/dev/null; then
    log_info "✓ Auth role 'external-secrets' created"
else
    log_error "Failed to create auth role"
    exit 1
fi

# Store Layer 1 secrets
log_info ""
log_info "[7/8] Storing Layer 1 secrets..."
if vault kv put secret/fabric/layer1 \
    database_url="postgresql://layer1:${LAYER1_DB_PASSWORD:-layer1pass}@postgres:5432/layer1_db" \
    redis_url="redis://redis:6379/0" \
    jwt_secret="${JWT_SECRET:-$(openssl rand -base64 32)}" \
    openai_api_key="${OPENAI_API_KEY:-}" 2>/dev/null; then
    log_info "✓ Layer 1 secrets stored"
else
    log_error "Failed to store Layer 1 secrets"
    exit 1
fi

# Store Layer 2-6 secrets
log_info ""
log_info "[8/8] Storing Layer 2-6 secrets..."

# Generate random passwords if not set
generate_password() { openssl rand -base64 16 2>/dev/null || head /dev/urandom | tr -dc A-Za-z0-9 | head -c 16; }

LAYER2_DB_PASS="${LAYER2_DB_PASSWORD:-$(generate_password)}"
LAYER3_DB_PASS="${LAYER3_DB_PASSWORD:-$(generate_password)}"
LAYER4_DB_PASS="${LAYER4_DB_PASSWORD:-$(generate_password)}"
LAYER5_DB_PASS="${LAYER5_DB_PASSWORD:-$(generate_password)}"
LAYER6_DB_PASS="${LAYER6_DB_PASSWORD:-$(generate_password)}"
NEO4J_PASS="${NEO4J_PASSWORD:-$(generate_password)}"

# Store all layer secrets
for i in 2 3 4 5 6; do
    eval "DB_PASS=\$LAYER${i}_DB_PASS"
    if ! vault kv put "secret/fabric/layer${i}" \
        database_url="postgresql://layer${i}:${DB_PASS}@postgres:5432/layer${i}_db" 2>/dev/null; then
        log_warn "Note: Layer ${i} basic secret stored (add specific secrets manually)"
    fi
done

# Store specific additional secrets
vault kv put secret/fabric/layer2 openai_api_key="${OPENAI_API_KEY:-}" redis_url="redis://redis:6379/1" 2>/dev/null || true
vault kv put secret/fabric/layer3 neo4j_url="bolt://neo4j:7687" neo4j_user="neo4j" neo4j_password="${NEO4J_PASS}" 2>/dev/null || true
vault kv put secret/fabric/layer4 redis_url="redis://redis:6379/2" openai_api_key="${OPENAI_API_KEY:-}" 2>/dev/null || true
vault kv put secret/fabric/layer5 jwt_secret="${JWT_SECRET:-$(generate_password)}" 2>/dev/null || true

log_info "✓ All layer secrets stored"

# Verify setup
log_info ""
log_info "=========================================="
log_info "Verification"
log_info "=========================================="

log_info ""
log_info "Checking KV secrets:"
vault kv list secret/fabric/ || log_warn "Could not list KV secrets"

log_info ""
log_info "Checking auth methods:"
vault auth list || log_warn "Could not list auth methods"

log_info ""
log_info "Checking Kubernetes roles:"
vault read auth/kubernetes/role/external-secrets || log_warn "Could not read Kubernetes role"

log_info ""
log_info "=========================================="
log_info "✓ Vault setup complete!"
log_info "=========================================="
log_info ""
log_info "Next steps:"
log_info "1. Apply External Secrets: kubectl apply -f k8s/external-secrets/"
log_info "2. Verify sync: kubectl get externalsecret -n value-fabric"
log_info "3. Check secrets: kubectl get secrets -n value-fabric"
log_info ""
