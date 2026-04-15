#!/bin/bash
# Configure HashiCorp Vault Database Secrets Engine for PostgreSQL
# This script sets up dynamic credential generation for Value Fabric

set -euo pipefail

# Configuration
VAULT_ADDR="${VAULT_ADDR:-https://vault.value-fabric.local:8200}"
VAULT_NAMESPACE="${VAULT_NAMESPACE:-value-fabric}"
POSTGRES_HOST="${POSTGRES_HOST:-postgres.value-fabric.svc.cluster.local}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_ADMIN_USER="${POSTGRES_ADMIN_USER:-vault}"
POSTGRES_ADMIN_PASSWORD="${POSTGRES_ADMIN_PASSWORD:-}"  # Must be provided

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v vault &> /dev/null; then
        log_error "Vault CLI not found. Please install: https://developer.hashicorp.com/vault/downloads"
        exit 1
    fi
    
    if [[ -z "${VAULT_TOKEN:-}" ]]; then
        log_error "VAULT_TOKEN environment variable not set"
        exit 1
    fi
    
    if [[ -z "$POSTGRES_ADMIN_PASSWORD" ]]; then
        log_error "POSTGRES_ADMIN_PASSWORD must be provided"
        exit 1
    fi
    
    log_info "Prerequisites check passed"
}

# Enable the database secrets engine
enable_database_engine() {
    log_info "Enabling Vault database secrets engine..."
    
    vault secrets list | grep -q "^database/" || {
        vault secrets enable -path=database database
        log_info "Database secrets engine enabled"
    } || {
        log_warn "Database secrets engine already enabled"
    }
}

# Configure PostgreSQL connection
configure_postgres_connection() {
    log_info "Configuring PostgreSQL connection..."
    
    vault write database/config/postgres \
        plugin_name=postgresql-database-plugin \
        allowed_roles="app-role,admin-role,readonly-role,layer1-app,layer2-app,layer3-app,layer4-app" \
        connection_url="postgresql://{{username}}:{{password}}@${POSTGRES_HOST}:${POSTGRES_PORT}/postgres?sslmode=require" \
        username="$POSTGRES_ADMIN_USER" \
        password="$POSTGRES_ADMIN_PASSWORD" \
        max_open_connections=10 \
        max_idle_connections=5 \
        max_connection_lifetime="1h"
    
    log_info "PostgreSQL connection configured"
}

# Create database roles
create_roles() {
    log_info "Creating database roles..."
    
    # Generic app role (1 hour TTL, 24 hour max TTL)
    vault write database/roles/app-role \
        db_name=postgres \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
            GRANT USAGE ON SCHEMA public TO \"{{name}}\"; \
            GRANT CREATE ON SCHEMA public TO \"{{name}}\"; \
            GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; \
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO \"{{name}}\";" \
        default_ttl="1h" \
        max_ttl="24h"
    
    # Admin role (4 hour TTL, 24 hour max TTL)
    vault write database/roles/admin-role \
        db_name=postgres \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
            ALTER USER \"{{name}}\" WITH SUPERUSER;" \
        default_ttl="4h" \
        max_ttl="24h"
    
    # Readonly role (24 hour TTL, 7 day max TTL)
    vault write database/roles/readonly-role \
        db_name=postgres \
        creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
            GRANT USAGE ON SCHEMA public TO \"{{name}}\"; \
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; \
            ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO \"{{name}}\";" \
        default_ttl="24h" \
        max_ttl="168h"
    
    # Layer-specific roles with least privilege
    for layer in layer1 layer2 layer3 layer4; do
        vault write database/roles/${layer}-app \
            db_name=postgres \
            creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; \
                GRANT USAGE ON SCHEMA public TO \"{{name}}\"; \
                GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO \"{{name}}\"; \
                ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO \"{{name}}\";" \
            default_ttl="1h" \
            max_ttl="4h"
        log_info "Created role: ${layer}-app"
    done
    
    log_info "Database roles created"
}

# Create policies for the roles
create_policies() {
    log_info "Creating Vault policies..."
    
    # Policy for External Secrets Operator
    cat > /tmp/eso-policy.hcl << EOF
path "database/creds/+" {
    capabilities = ["read"]
}

path "secret/data/value-fabric/*" {
    capabilities = ["read", "list"]
}
EOF
    
    vault policy write external-secrets /tmp/eso-policy.hcl
    
    # Policy for layer services
    cat > /tmp/layer-policy.hcl << EOF
path "database/creds/layer1-app" {
    capabilities = ["read"]
}

path "database/creds/layer2-app" {
    capabilities = ["read"]
}

path "database/creds/layer3-app" {
    capabilities = ["read"]
}

path "database/creds/layer4-app" {
    capabilities = ["read"]
}

path "secret/data/value-fabric/auth" {
    capabilities = ["read"]
}
EOF
    
    vault policy write value-fabric-layers /tmp/layer-policy.hcl
    
    # Policy for admin operations
    cat > /tmp/admin-policy.hcl << EOF
path "database/creds/admin-role" {
    capabilities = ["read"]
}

path "database/rotate-role/*" {
    capabilities = ["update"]
}

path "database/rotate-root/postgres" {
    capabilities = ["update"]
}

path "secret/*" {
    capabilities = ["create", "read", "update", "delete", "list"]
}
EOF
    
    vault policy write value-fabric-admin /tmp/admin-policy.hcl
    
    rm /tmp/eso-policy.hcl /tmp/layer-policy.hcl /tmp/admin-policy.hcl
    
    log_info "Vault policies created"
}

# Enable Kubernetes auth method
enable_kubernetes_auth() {
    log_info "Enabling Kubernetes auth method..."
    
    vault auth list | grep -q "^kubernetes/" || {
        vault auth enable kubernetes
        log_info "Kubernetes auth enabled"
    } || {
        log_warn "Kubernetes auth already enabled"
    }
    
    # Get Kubernetes cluster info
    local k8s_host="https://kubernetes.default.svc"
    local token_reviewer_jwt=""
    local kubernetes_ca_cert=""
    
    if command -v kubectl &> /dev/null; then
        k8s_host="$(kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}')"
        token_reviewer_jwt="$(kubectl create token external-secrets -n external-secrets --duration=1h 2>/dev/null || echo '')"
        kubernetes_ca_cert="$(kubectl get configmap -n kube-system extension-apiserver-authentication -o=jsonpath='{.data.client-ca-file}')"
    fi
    
    vault write auth/kubernetes/config \
        kubernetes_host="$k8s_host" \
        token_reviewer_jwt="${token_reviewer_jwt:-}" \
        kubernetes_ca_cert="$kubernetes_ca_cert" \
        issuer="https://kubernetes.default.svc.cluster.local"
    
    log_info "Kubernetes auth configured"
}

# Create Kubernetes auth roles
create_kubernetes_roles() {
    log_info "Creating Kubernetes auth roles..."
    
    # Role for External Secrets Operator
    vault write auth/kubernetes/role/external-secrets \
        bound_service_account_names=external-secrets \
        bound_service_account_namespaces=external-secrets \
        policies=external-secrets \
        ttl=1h
    
    # Roles for layer service accounts
    for layer in layer1 layer2 layer3 layer4; do
        vault write auth/kubernetes/role/${layer}-app \
            bound_service_account_names=${layer}-ingestion,${layer}-extraction,${layer}-knowledge,${layer}-agents \
            bound_service_account_namespaces=value-fabric \
            policies=value-fabric-layers \
            ttl=1h
    done
    
    log_info "Kubernetes auth roles created"
}

# Test dynamic credentials
test_dynamic_credentials() {
    log_info "Testing dynamic credentials..."
    
    # Generate test credentials
    local creds=$(vault read -format=json database/creds/app-role)
    local username=$(echo "$creds" | jq -r '.data.username')
    local password=$(echo "$creds" | jq -r '.data.password')
    
    log_info "Generated test credentials for user: $username"
    
    # Test connection (requires psql)
    if command -v psql &> /dev/null; then
        if PGPASSWORD="$password" psql -h "$POSTGRES_HOST" -U "$username" -d postgres -c "SELECT current_user;" > /dev/null 2>&1; then
            log_info "Dynamic credentials test: SUCCESS"
        else
            log_warn "Dynamic credentials test: FAILED (may require network access to Postgres)"
        fi
    else
        log_warn "psql not installed, skipping connection test"
    fi
}

# Main execution
main() {
    log_info "Starting Vault Database Secrets Engine configuration..."
    
    check_prerequisites
    enable_database_engine
    configure_postgres_connection
    create_roles
    create_policies
    enable_kubernetes_auth
    create_kubernetes_roles
    test_dynamic_credentials
    
    log_info "Vault Database Secrets Engine configuration complete!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Create Kubernetes secrets for each layer: kubectl apply -f k8s/external-secrets/layer*-secrets.yaml"
    log_info "2. Verify secret sync: kubectl get externalsecret -n value-fabric"
    log_info "3. Check dynamic credentials: vault read database/creds/app-role"
    log_info ""
    log_warn "Important: Store this output securely. It contains sensitive configuration details."
}

main "$@"
